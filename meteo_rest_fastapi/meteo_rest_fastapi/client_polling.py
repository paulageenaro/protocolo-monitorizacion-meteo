"""Cliente de prueba REST con polling de notificaciones.

Ejecuta primero el servidor:
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

Después, en otra terminal:
    python client_polling.py http://127.0.0.1:8000 Granada
"""

import sys
import time
import httpx

base_url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
city = sys.argv[2] if len(sys.argv) > 2 else "Granada"

with httpx.Client(base_url=base_url, timeout=10.0) as client:
    r = client.post("/clients")
    r.raise_for_status()
    client_id = r.json()["client_id"]
    print(f"Cliente creado: {client_id}")

    r = client.post(
        f"/clients/{client_id}/subscriptions",
        json={"city": city, "variables": ["temp", "hum", "pres", "wind"]},
    )
    print("Suscripción:", r.status_code, r.json())
    r.raise_for_status()

    print("Consultando notificaciones cada 5 segundos. Ctrl+C para salir.")
    try:
        while True:
            r = client.get(f"/clients/{client_id}/notifications")
            print(r.json())
            time.sleep(5)
    except KeyboardInterrupt:
        client.delete(f"/clients/{client_id}")
        print("Cliente eliminado.")
