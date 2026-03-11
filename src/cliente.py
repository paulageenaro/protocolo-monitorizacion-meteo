import socket
import json
import threading
import unicodedata
import re  # Añadimos regex para limpiar signos de puntuación

# Colores
AZUL = '\033[94m'
VERDE = '\033[92m'
AMARILLO = '\033[93m'
ROJO = '\033[91m'
RESET = '\033[0m'
NEGRILLA = '\033[1m'

def limpiar_texto(texto):
    """Limpia tildes, mayúsculas, signos de puntuación y espacios extra."""
    # 1. Quitar mayúsculas y espacios en los bordes
    texto = texto.lower().strip()
    # 2. Quitar signos de puntuación (¿? ¡! . , ; :)
    texto = re.sub(r'[¿?¡!.,;:]', '', texto)
    # 3. Quitar tildes
    return "".join(c for c in unicodedata.normalize('NFD', texto)
                   if unicodedata.category(c) != 'Mn')

def mostrar_esquema():
    print(f"\n{NEGRILLA}{AZUL}┌──────────────────────────────────────────────────────────┐")
    print(f"│                🌤️  ASISTENTE METEO v5.0  🌤️               │")
    print(f"├──────────────────────────────────────────────────────────┤")
    print(f"│ {AMARILLO}¿QUÉ PUEDES HACER?{AZUL}                                       │")
    print(f"│                                                          │")
    print(f"│ {VERDE}0. CATÁLOGO:{AZUL} \"¿Qué ciudades tienes?\" 📂                 │")
    print(f"│ {VERDE}1. CONSULTA:{AZUL} \"Dime el tiempo en Granada\"                 │")
    print(f"│ {VERDE}2. SUSCRIPCIÓN:{AZUL} \"Avísame de los cambios en Madrid\"        │")
    print(f"│ {VERDE}3. CANCELAR:{AZUL} \"Quiero desubscribirme\" ❌                   │")
    print(f"│ {VERDE}4. SALIR:{AZUL} \"Adiós\"                                         │")
    print(f"└──────────────────────────────────────────────────────────┘{RESET}\n")

def listen_from_server(sock):
    while True:
        try:
            data = sock.recv(4096).decode('utf-8')
            if not data: break
            messages = data.strip().split('\n')
            for m in messages:
                if not m: continue
                msg = json.loads(m)
                
                if "type" in msg and msg["type"] == "NOTIF":
                    print(f"\n{AMARILLO}{NEGRILLA}⚠️  ¡AVISO! El tiempo en {msg['city'].upper()} ha cambiado: {msg['data']} 📡{RESET}")
                
                elif msg.get("type") == "RESP_LIST":
                    print(f"\n{VERDE}{NEGRILLA}[ASISTENTE]: {msg['msg']}{RESET}")
                    print(f"{AZUL}📍 Ciudades: {', '.join(msg['data'])}{RESET}")

                elif "status" in msg:
                    if msg["status"] == 200:
                        if "Suscrito" in str(msg.get('msg', '')):
                            print(f"\n{VERDE}{NEGRILLA}[ASISTENTE]: ¡Genial! Suscrito correctamente. ✅{RESET}")
                            print(f"{VERDE}¡Bienvenido! Se le avisará de cambios en la ciudad elegida. 🔔{RESET}")
                        elif "data" in msg:
                            # MODIFICACIÓN: Mostrar explícitamente el nombre de la ciudad
                            ciudad_nombre = msg.get('city', 'la ciudad solicitada')
                            print(f"\n{VERDE}{NEGRILLA}[ASISTENTE]:{RESET} Aquí tienes el clima actual de {NEGRILLA}{ciudad_nombre}{RESET}:")
                            print(f"{VERDE}🌡️  Datos: {msg['data']}{RESET}")
                        else:
                            print(f"\n{VERDE}{NEGRILLA}[ASISTENTE]:{RESET} {msg.get('msg', 'Hecho')} 👍")
                    else:
                        print(f"\n{ROJO}[ASISTENTE]: No he podido encontrar esa ciudad. 😕{RESET}")
                
            print(f"\n{AZUL}¿Qué más necesitas? > {RESET}", end="", flush=True)
        except:
            break

def procesar_lenguaje(frase_original):
    # Usamos la nueva limpieza ultra-flexible
    entrada = limpiar_texto(frase_original)
    
    # Intención: VER CIUDADES
    if any(p in entrada for p in ["ciudades", "lista", "catalogo", "cuales hay", "disponibles"]):
        return {"command": "LIST"}

    # Detectar Ciudad (Manejo flexible de nombres)
    ciudades_db = {
        "madrid": "Madrid", "granada": "Granada", "barcelona": "Barcelona", 
        "sevilla": "Sevilla", "matalascanas": "Matalascañas", "londres": "London", 
        "paris": "Paris", "malaga": "Malaga", "valencia": "Valencia", "bilbao": "Bilbao"
    }
    
    ciudad_detectada = None
    for clave, nombre_real in ciudades_db.items():
        if clave in entrada:
            ciudad_detectada = nombre_real
            break

    palabras_clima = ["tiempo", "clima", "que hace", "get", "avisame", "notifica", "suscribe", "alerta"]
    if any(p in entrada for p in palabras_clima) and not ciudad_detectada:
        # Intentamos ver si puso una palabra que parece una ciudad pero no está en la lista
        print(f"\n{AMARILLO}[ASISTENTE]: Lo siento, no tengo esa ciudad en mi catálogo actual. 📂{RESET}")
        print(f"{AZUL}Prueba a decir '¿Qué ciudades tienes?' para ver cuáles conozco. 😊{RESET}")
        return None
            
    # Intención: SUSCRIPCIÓN
    if any(p in entrada for p in ["avisame", "notifica", "suscribeme","subscribe", "alerta", "suscripcion", "vigila"]):
        return {"command": "SUB", "city": ciudad_detectada or "Madrid", "variables": ["temp", "hum", "wind"]}
    
    # Intención: CANCELAR
    if any(p in entrada for p in ["para", "cancela", "unsub", "desubscribirme", "quitar"]):
        confirmar = input(f"\n{AMARILLO}🤔 ¿Seguro que quieres cancelar tus alertas? (si/no): {RESET}")
        if limpiar_texto(confirmar) == "si":
            return {"command": "UNSUB"}
        return None

    # Intención: CONSULTA (Si no es suscripción ni catálogo, pero hay ciudad o palabras de clima)
    if ciudad_detectada or any(p in entrada for p in ["dime", "tiempo", "clima", "que hace", "get"]):
        return {"command": "GET", "city": ciudad_detectada or "Madrid"}
    
    return None

def start_client():
    print(f"{NEGRILLA}{AZUL}--- 🌐 CONEXIÓN AL SERVIDOR METEO ---{RESET}")
    print(f"IP del servidor (Enter para {AMARILLO}'localhost'{RESET}):")
    ip_srv = input("> ").strip() or "127.0.0.1"

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((ip_srv, 5000))
        print(f"{VERDE}¡Conectado! 🚀{RESET}")
    except:
        print(f"{ROJO}❌ Error de conexión.{RESET}")
        return

    threading.Thread(target=listen_from_server, args=(client,), daemon=True).start()
    mostrar_esquema()

    while True:
        frase = input(f"{AZUL}Tú: {RESET}").strip()
        if not frase: continue
        
        # Limpieza para comando de salida
        frase_limpia = limpiar_texto(frase)
        if frase_limpia in ["salir", "exit", "adios"]: 
            print(f"{VERDE}¡Hasta pronto! 👋{RESET}")
            break
        
        msg_json = procesar_lenguaje(frase)
        if msg_json:
            client.sendall((json.dumps(msg_json) + "\n").encode('utf-8'))
        elif "desubscribirme" not in frase_limpia:
            print(f"{AMARILLO}[!] No te entiendo. Prueba con: '¿Qué ciudades tienes?' 🧐{RESET}")

    client.close()

if __name__ == "__main__":
    start_client()
