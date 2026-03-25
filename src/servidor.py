import socket # Para la comunicación por red (TCP)
import threading # Para manejar múltiples clientes a la vez y procesos en segundo plano
import json # Para enviar y recibir datos en formato JSON
import time # Para controlar los intervalos de actualización
import requests # Para hacer peticiones HTTP a la API de OpenWeather

class MeteoServer:
    def __init__(self, host='127.0.0.1', port=5000): # Cambiado a 0.0.0.0 para acceso externo
        self.host = host
        self.port = port
        self.api_key = "be0c11c0a23c59c181513ee2570c9cd0" # Tu llave para la API de clima
        
        # --- LISTA DE CIUDADES DISPONIBLES ---
        self.ciudades_soportadas = ["Madrid", "Granada", "Barcelona", "Sevilla", "Matalascañas", "Londres", "Paris", "Malaga", "Valencia", "Bilbao"]
        
        self.city_states = {} # Guarda el último clima conocido de cada ciudad
        self.subscriptions = {} # Guarda qué cliente está suscrito a qué ciudad
        self.lock = threading.Lock() # Evita que dos hilos choquen al modificar datos

    def fetch_weather(self, city):
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={self.api_key}&units=metric"
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                return { # Extrae solo lo que nos interesa: temp, humedad, presión y viento
                    "temp": data['main']['temp'],
                    "hum": data['main']['humidity'],
                    "pres": data['main']['pressure'],
                    "wind": data['wind']['speed']
                }
            else:
                return None
        except Exception as e:
            print(f"[RED ERROR] Error al conectar con la API: {e}")
            return None

    def update_loop(self):
        while True:
            with self.lock:
                cities_to_update = set()
                for subs in self.subscriptions.values(): # 1. Mira qué ciudades tienen suscriptores activos
                    cities_to_update.update(subs.keys())
            
            for city in cities_to_update:
                new_data = self.fetch_weather(city) # 2. Llama a fetch_weather para cada una de esas ciudades
                if new_data:
                    with self.lock:
                        old_data = self.city_states.get(city, {})
                        self.city_states[city] = new_data   # 3. Guarda los nuevos datos en self.city_states
                        self.process_notifications(city, old_data)  # 4. Llama a process_notifications para avisar a los clientes si algo cambió
            
            time.sleep(60) # Espera 1 minuto antes de volver a actualizar

    def process_notifications(self, city, old_data):
        current_data = self.city_states[city]
        for sock, subs in list(self.subscriptions.items()):
            if city in subs:
                sub = subs[city]
                changes = {}
                for v in sub["vars"]:
                    if current_data.get(v) != sub["last_sent"].get(v):  # Compara los datos nuevos con los que el cliente recibió la última vez.
                        changes[v] = current_data[v]
                
                if changes: # Si la temperatura o el viento han cambiado, le envía un mensaje tipo "NOTIF".
                    sub["last_sent"].update(changes)
                    self.send_json(sock, {"type": "NOTIF", "city": city, "data": changes})

    def send_json(self, sock, data): # Convierte un diccionario de Python a un string JSON y le añade un \n (salto de línea) para que el cliente sepa dónde termina el mensaje.
        try:
            payload = json.dumps(data) + "\n"
            sock.sendall(payload.encode('utf-8'))
        except:
            self.remove_client(sock)

    def remove_client(self, sock):
        with self.lock:
            if sock in self.subscriptions:
                del self.subscriptions[sock]
            try:
                sock.close()
            except:
                pass

    def handle_client(self, conn, addr):
        print(f"[NUEVA CONEXIÓN] {addr}")
        try: # Bucle infinito que escucha lo que envía el cliente
            while True:
                data = conn.recv(1024).decode('utf-8')
                if not data: break
                
                messages = data.strip().split('\n')
                for m in messages:
                    req = json.loads(m)
                    cmd = req.get("command")
                    city = req.get("city", "Madrid")

                    # --- NUEVO COMANDO: LIST ---
                    if cmd == "LIST":
                        print(f"[LIST] {addr} solicita catálogo")
                        self.send_json(conn, {
                            "status": 200, 
                            "type": "RESP_LIST", 
                            "data": self.ciudades_soportadas,
                            "msg": f"Actualmente tengo {len(self.ciudades_soportadas)} ciudades disponibles."
                        })

                    elif cmd == "GET":
                        print(f"[GET] {addr} pide {city}")
                        fresh_data = self.fetch_weather(city)
                        if fresh_data:
                            self.send_json(conn, {"status": 200, "city": city, "data": fresh_data})
                        else:
                            self.send_json(conn, {"status": 404, "msg": "Ciudad no encontrada"})

                    elif cmd == "SUB":
                        vars_req = req.get("variables", ["temp", "hum", "pres", "wind"])
                        
                        # --- COMPROBACIÓN DE SUSCRIPCIÓN PREVIA ---
                        with self.lock:
                            if conn not in self.subscriptions:
                                self.subscriptions[conn] = {}
                                
                            if city in self.subscriptions[conn]:
                                self.send_json(conn, {
                                    "status": 400, 
                                    "msg": f"Ya estás suscrito a las alertas de {city}. ✅"
                                })
                                continue # Saltamos al siguiente mensaje sin hacer nada más
                        
                        # Si no estaba suscrito, procedemos normalmente
                        print(f"[SUB] {addr} se suscribe a {city}")
                        initial_data = self.fetch_weather(city)
                        if initial_data:
                            with self.lock:
                                self.city_states[city] = initial_data
                                self.subscriptions[conn][city] = {
                                    "vars": vars_req, 
                                    "last_sent": initial_data.copy()
                                }
                            self.send_json(conn, {"status": 200, "msg": f"Suscrito a {city}", "current": initial_data})
                        else:
                            self.send_json(conn, {"status": 404, "msg": "Ciudad no válida"})    
                    elif cmd == "UNSUB":
                        with self.lock:
                            target_city = req.get("city")
                            if conn in self.subscriptions:
                                if target_city and target_city in self.subscriptions[conn]:
                                    del self.subscriptions[conn][target_city]
                                    self.send_json(conn, {"status": 200, "msg": f"Suscripción a {target_city} cancelada"})
                                else:
                                    del self.subscriptions[conn]
                                    self.send_json(conn, {"status": 200, "msg": "Todas las suscripciones canceladas"})

        except Exception as e:
            print(f"[CLIENT ERROR] {e}")
        finally:
            self.remove_client(conn)

    def start(self):
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Crea el socket TCP
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
        server_sock.bind((self.host, self.port)) # Asigna la IP y el Puerto
        server_sock.listen(5) # Empieza a esperar conexiones
        
        threading.Thread(target=self.update_loop, daemon=True).start() # Lanza el hilo que actualiza el clima cada minuto
        print(f"--- SERVIDOR ACTIVO EN {self.host}:{self.port} ---")
        
        while True:
            conn, addr = server_sock.accept() # Acepta a un nuevo cliente
            threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start() # Lanza un hilo nuevo para ese cliente específico (así pueden haber muchos a la vez)

if __name__ == "__main__":
    MeteoServer().start()
