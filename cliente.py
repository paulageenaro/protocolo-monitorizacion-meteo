import socket
import json
import threading

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
                    print(f"\n[NOTIFICACIÓN] {msg['city']} ha cambiado: {msg['data']}")
                elif "status" in msg:
                    # Imprime tanto mensajes de texto como datos de diccionarios
                    info = msg.get('data', msg.get('msg', msg.get('current', '')))
                    c_name = msg.get('city', '')
                    print(f"\n[RESPUESTA] {c_name} -> {info}")
                
            print("> ", end="", flush=True)
        except:
            break

def start_client():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect(('127.0.0.1', 5000))
    except:
        print("Servidor no encontrado.")
        return

    threading.Thread(target=listen_from_server, args=(client,), daemon=True).start()

    print("--- COMANDOS DISPONIBLES ---")
    print("1. GET <ciudad>          (Ej: GET Granada)")
    print("2. SUB <ciudad> <vars>   (Ej: SUB Madrid temp hum)")
    print("3. UNSUB                 (Cancela suscripción)")
    print("4. EXIT                  (Salir)")
    
    while True:
        line = input("> ").strip().split()
        if not line: continue
        
        cmd = line[0].upper()
        if cmd == "EXIT": break
        
        msg = {}
        if cmd == "GET":
            city = line[1] if len(line) > 1 else "Madrid"
            msg = {"command": "GET", "city": city}
        
        elif cmd == "SUB":
            if len(line) < 2:
                print("Uso: SUB <ciudad> [variables...]")
                continue
            city = line[1]
            vars_list = line[2:] if len(line) > 2 else ["temp", "hum", "pres", "wind"]
            msg = {"command": "SUB", "city": city, "variables": vars_list}
            
        elif cmd == "UNSUB":
            msg = {"command": "UNSUB"}
            
        else:
            print("Comando inválido.")
            continue

        client.sendall((json.dumps(msg) + "\n").encode('utf-8'))

    client.close()

if __name__ == "__main__":
    start_client()