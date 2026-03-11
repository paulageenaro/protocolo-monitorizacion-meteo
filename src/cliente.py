import socket
import json
import threading
import sys

# --- CONFIGURACIÓN DE COLORES PARA TERMINAL LINUX ---
AZUL = '\033[94m'
VERDE = '\033[92m'
AMARILLO = '\033[93m'
ROJO = '\033[91m'
RESET = '\033[0m'
NEGRILLA = '\033[1m'

def mostrar_esquema():
    """Muestra el esquema visual de opciones al usuario."""
    print(f"\n{NEGRILLA}{AZUL}┌──────────────────────────────────────────────────────────┐")
    print(f"│                ASISTENTE METEOROLÓGICO v2.0              │")
    print(f"├──────────────────────────────────────────────────────────┤")
    print(f"│ {AMARILLO}OPCIONES DISPONIBLES:{AZUL}                                    │")
    print(f"│                                                          │")
    print(f"│ {VERDE}1. CONSULTA PUNTUAL{AZUL}                                      │")
    print(f"│    > \"Dime el tiempo en [Ciudad]\"                        │")
    print(f"│                                                          │")
    print(f"│ {VERDE}2. SUSCRIPCIÓN (ALERTAS){AZUL}                                 │")
    print(f"│    > \"Avísame si cambia el tiempo en [Ciudad]\"           │")
    print(f"│                                                          │")
    print(f"│ {VERDE}3. GESTIÓN{AZUL}                                               │")
    print(f"│    > \"Para las notificaciones\" (o 'unsub')               │")
    print(f"│    > \"Salir\"                                             │")
    print(f"└──────────────────────────────────────────────────────────┘{RESET}\n")

def listen_from_server(sock):
    """Hilo encargado de recibir y procesar mensajes del servidor."""
    while True:
        try:
            data = sock.recv(4096).decode('utf-8')
            if not data:
                print(f"\n{ROJO}[SISTEMA] Conexión perdida con el servidor.{RESET}")
                break
            
            # Separamos mensajes por el delimitador \n
            messages = data.strip().split('\n')
            for m in messages:
                if not m: continue
                msg = json.loads(m)
                
                # CASO 1: Notificación PUSH (Suscripción)
                if "type" in msg and msg["type"] == "NOTIF":
                    print(f"\n{AMARILLO}[ALERTA]{RESET} Cambio en {msg['city']}: {msg['data']}")
                
                # CASO 2: Respuesta a un comando (GET/SUB/UNSUB)
                elif "status" in msg:
                    if msg["status"] == 200:
                        # Si hay datos de clima, los mostramos; si no, mostramos el mensaje de éxito
                        res = msg.get('data', msg.get('msg', msg.get('current', 'OK')))
                        c_name = msg.get('city', '')
                        print(f"\n{VERDE}[ASISTENTE]{RESET} {c_name} {res}")
                    else:
                        print(f"\n{ROJO}[ERROR]{RESET} {msg.get('msg', 'Operación fallida')}")
                
            print(f"\n{AZUL}¿Qué más necesitas? > {RESET}", end="", flush=True)
        except:
            break

def procesar_lenguaje(entrada):
    """Traduce frases naturales a comandos estructurados del protocolo JSON."""
    entrada = entrada.lower()
    
    # Listado dinámico de ciudades para reconocimiento
    ciudades = ["madrid", "granada", "barcelona", "sevilla", "matalascañas", "londres", "paris", "vigo", "bilbao"]
    ciudad_detectada = "Madrid" # Valor por defecto
    for c in ciudades:
        if c in entrada:
            ciudad_detectada = c.capitalize()

    # Intención: Suscripción
    if any(p in entrada for p in ["avísame", "notifica", "suscribe", "alerta"]):
        return {"command": "SUB", "city": ciudad_detectada, "variables": ["temp", "hum", "wind"]}
    
    # Intención: Consulta puntual
    if any(p in entrada for p in ["dime", "tiempo", "clima", "qué hace", "llueve"]):
        return {"command": "GET", "city": ciudad_detectada}
    
    # Intención: Cancelación
    if any(p in entrada for p in ["para", "cancela", "unsub", "quitar"]):
        return {"command": "UNSUB"}
    
    # Si no entiende, devuelve None
    return None

def start_client():
    # 1. Pedir IP del servidor
    print(f"{NEGRILLA}--- INICIO DEL CLIENTE ---{RESET}")
    ip_srv = input("Introduce la IP del Servidor (o 'localhost'): ").strip()
    if not ip_srv: ip_srv = "127.0.0.1"

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((ip_srv, 5000))
    except Exception as e:
        print(f"{ROJO}No se pudo conectar: {e}{RESET}")
        return

    # 2. Lanzar hilo de escucha asíncrona
    threading.Thread(target=listen_from_server, args=(client,), daemon=True).start()
    
    # 3. Mostrar interfaz visual
    mostrar_esquema()

    # 4. Bucle principal de interacción
    try:
        while True:
            frase = input(f"{AZUL}¿Qué necesitas? > {RESET}").strip()
            
            if not frase: continue
            if frase.lower() in ["salir", "exit", "quit", "adiós"]:
                print(f"{VERDE}[ASISTENTE] ¡Hasta pronto!{RESET}")
                break
            
            # Analizar lenguaje
            msg_json = procesar_lenguaje(frase)
            
            if msg_json:
                # Enviar comando JSON al servidor con delimitador \n
                client.sendall((json.dumps(msg_json) + "\n").encode('utf-8'))
            else:
                print(f"{AMARILLO}[!] No te he entendido. Prueba con algo como: 'Dime el tiempo en Granada'{RESET}")
    except KeyboardInterrupt:
        pass
    finally:
        client.close()

if __name__ == "__main__":
    start_client()
