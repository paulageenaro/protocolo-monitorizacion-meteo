import asyncio
import websockets
import socket
import json
import threading

# Configuración
WS_HOST = '0.0.0.0'
WS_PORT = 8080
TCP_HOST = '127.0.0.1' 
TCP_PORT = 5000

async def handle_client(websocket):
    """Maneja la conexión de un cliente WebSocket y lo puentea al servidor TCP."""
    print(f"[PROXY] Nuevo cliente Web conectado desde {websocket.remote_address}")
    
    # 1. Conectar al servidor TCP real
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        tcp_socket.connect((TCP_HOST, TCP_PORT))
        print(f"[PROXY] Conectado al servidor TCP {TCP_HOST}:{TCP_PORT}")
    except Exception as e:
        print(f"[PROXY ERROR] No se pudo conectar al servidor TCP: {e}")
        await websocket.send(json.dumps({"status": 500, "msg": "Error interno del proxy al conectar al servidor."}))
        return

    # 2. Bucle de lectura desde el servidor TCP hacia el WebSocket
    def tcp_to_ws():
        while True:
            try:
                data = tcp_socket.recv(4096).decode('utf-8')
                if not data:
                    break
                
                # El servidor puede enviar múltiples mensajes separados por \n
                messages = data.strip().split('\n')
                for msg in messages:
                    if msg:
                        # Usar asyncio.run_coroutine_threadsafe asegura hilo seguro
                        asyncio.run_coroutine_threadsafe(websocket.send(msg), loop)
            except Exception as e:
                print(f"[PROXY TCP->WS] Error: {e}")
                break
        print("[PROXY] Desconectado del servidor TCP.")

    # Iniciar hilo en segundo plano para escuchar al TCP
    loop = asyncio.get_event_loop()
    threading.Thread(target=tcp_to_ws, daemon=True).start()

    # 3. Bucle de lectura desde el WebSocket hacia el servidor TCP
    try:
        async for message in websocket:
            print(f"[PROXY WS->TCP] Recibido: {message}")
            try:
                # Validar que es JSON, por si acaso
                json.loads(message)
                tcp_socket.sendall((message + "\n").encode('utf-8'))
            except json.JSONDecodeError:
                print("[PROXY ERROR] El cliente Web envió un JSON inválido.")
    except websockets.exceptions.ConnectionClosed:
        print(f"[PROXY] Cliente Web {websocket.remote_address} desconectado.")
    finally:
        tcp_socket.close()

async def main():
    print(f"--- PROXY WEBSOCKETS INICIADO EN ws://{WS_HOST}:{WS_PORT} ---")
    print(f"Redirigiendo tráfico a TCP {TCP_HOST}:{TCP_PORT}")
    async with websockets.serve(handle_client, WS_HOST, WS_PORT):
        await asyncio.Future()  # Ejecutar para siempre

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[PROXY] Apagando proxy...")
