import socket
import threading
import json
import time
import requests

class MeteoServer:
    def __init__(self, host='0.0.0.0', port=5000):
        self.host = host
        self.port = port
        # REEMPLAZA ESTO CON TU API KEY REAL
        self.api_key = "be0c11c0a23c59c181513ee2570c9cd0" 
        
        # Diccionario para guardar el último estado conocido de cada ciudad
        self.city_states = {} 
        # Diccionario de suscripciones: { socket: {"city": "Granada", "vars": [...], "last_sent": {...}} }
        self.subscriptions = {}
        self.lock = threading.Lock()

    def fetch_weather(self, city):
        """Consulta la API de OpenWeather para una ciudad concreta."""
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={self.api_key}&units=metric"
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "temp": data['main']['temp'],
                    "hum": data['main']['humidity'],
                    "pres": data['main']['pressure'],
                    "wind": data['wind']['speed']
                }
            else:
                print(f"[API ERROR] Ciudad '{city}' no encontrada o API Key inválida.")
                return None
        except Exception as e:
            print(f"[RED ERROR] Error al conectar con la API: {e}")
            return None

    def update_loop(self):
        """Hilo que actualiza periódicamente las ciudades con suscriptores."""
        while True:
            with self.lock:
                cities_to_update = {sub["city"] for sub in self.subscriptions.values()}
            
            for city in cities_to_update:
                new_data = self.fetch_weather(city)
                if new_data:
                    with self.lock:
                        old_data = self.city_states.get(city, {})
                        self.city_states[city] = new_data
                        self.process_notifications(city, old_data)
            
            time.sleep(60) # Actualización cada minuto

    def process_notifications(self, city, old_data):
        """Envía notificaciones si los datos de la ciudad cambiaron."""
        current_data = self.city_states[city]
        for sock, sub in list(self.subscriptions.items()):
            if sub["city"] == city:
                changes = {}
                for v in sub["vars"]:
                    # Si el valor actual es distinto al último que le enviamos a este cliente
                    if current_data.get(v) != sub["last_sent"].get(v):
                        changes[v] = current_data[v]
                
                if changes:
                    sub["last_sent"].update(changes)
                    self.send_json(sock, {"type": "NOTIF", "city": city, "data": changes})

    def send_json(self, sock, data):
        try:
            payload = json.dumps(data) + "\n"
            sock.sendall(payload.encode('utf-8'))
        except:
            self.remove_client(sock)

    def remove_client(self, sock):
        with self.lock:
            if sock in self.subscriptions:
                print(f"[LOG] Cliente {sock.getpeername()} desconectado.")
                del self.subscriptions[sock]
            try:
                sock.close()
            except:
                pass

    def handle_client(self, conn, addr):
        print(f"[NUEVA CONEXIÓN] {addr}")
        try:
            while True:
                data = conn.recv(1024).decode('utf-8')
                if not data: break
                
                # Gestión de múltiples mensajes en un mismo buffer
                messages = data.strip().split('\n')
                for m in messages:
                    req = json.loads(m)
                    cmd = req.get("command")
                    city = req.get("city", "Madrid")

                    if cmd == "GET":
                        print(f"[GET] {addr} pide {city}")
                        fresh_data = self.fetch_weather(city)
                        if fresh_data:
                            self.send_json(conn, {"status": 200, "city": city, "data": fresh_data})
                        else:
                            self.send_json(conn, {"status": 404, "msg": "Ciudad no encontrada"})

                    elif cmd == "SUB":
                        vars_req = req.get("variables", ["temp", "hum", "pres", "wind"])
                        print(f"[SUB] {addr} se suscribe a {city}")
                        
                        # Al suscribirse, enviamos datos actuales de esa ciudad inmediatamente
                        initial_data = self.fetch_weather(city)
                        if initial_data:
                            with self.lock:
                                self.city_states[city] = initial_data
                                self.subscriptions[conn] = {
                                    "city": city, 
                                    "vars": vars_req, 
                                    "last_sent": initial_data.copy()
                                }
                            self.send_json(conn, {"status": 200, "msg": f"Suscrito a {city}", "current": initial_data})
                        else:
                            self.send_json(conn, {"status": 404, "msg": "Ciudad no válida"})

                    elif cmd == "UNSUB":
                        with self.lock:
                            if conn in self.subscriptions:
                                del self.subscriptions[conn]
                                self.send_json(conn, {"status": 200, "msg": "Suscripción cancelada"})

        except Exception as e:
            print(f"[CLIENT ERROR] {e}")
        finally:
            self.remove_client(conn)

    def start(self):
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind((self.host, self.port))
        server_sock.listen(5)
        
        threading.Thread(target=self.update_loop, daemon=True).start()
        print(f"--- SERVIDOR ACTIVO EN {self.host}:{self.port} ---")
        
        while True:
            conn, addr = server_sock.accept()
            threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":

    MeteoServer().start()
