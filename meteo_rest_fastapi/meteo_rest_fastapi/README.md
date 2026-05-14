# MeteoApp REST API

Transformación del sistema de monitorización meteorológica basado en sockets/RMI a un servicio web REST con **Python + FastAPI**.

## 1. Instalación

```bash
cd meteo_rest_fastapi
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
# .venv\Scripts\activate         # Windows PowerShell
pip install -r requirements.txt
```

Crea un fichero `.env` a partir de `.env.example`:

```bash
cp .env.example .env
```

Dentro de `.env`, define:

```text
OPENWEATHER_API_KEY=tu_clave_real
UPDATE_INTERVAL_SECONDS=60
```

## 2. Ejecución

Para que sea accesible desde otra máquina o VM:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Desde la misma máquina:

```text
http://127.0.0.1:8000/docs
```

Desde otra VM:

```text
http://IP_DEL_SERVIDOR:8000/docs
```

## 3. Documentación OpenAPI / Swagger

FastAPI genera automáticamente:

- Swagger UI: `/docs`
- ReDoc: `/redoc`
- Especificación OpenAPI JSON: `/openapi.json`

Para obtener el JSON OpenAPI:

```bash
curl http://127.0.0.1:8000/openapi.json -o openapi.json
```

Para entregar la documentación en PDF, abre `/docs` o `/redoc` en el navegador y usa **Imprimir → Guardar como PDF**.

## 4. Tabla de transformación

| Método/protocolo anterior | Recurso REST | Método HTTP | Código esperado |
|---|---|---:|---:|
| `listCities()` / `LIST` | `/cities` | `GET` | `200 OK` |
| `getWeather(city)` / `GET` | `/weather/{city}` | `GET` | `200 OK` / `404 Not Found` |
| `GET` sin ciudad | `/weather?city=Madrid` | `GET` | `200 OK` |
| Crear identidad de cliente REST | `/clients` | `POST` | `201 Created` |
| `subscribe(city, callback)` / `SUB` | `/clients/{client_id}/subscriptions` | `POST` | `201 Created` / `400 Bad Request` / `404 Not Found` |
| Ver suscripciones activas | `/clients/{client_id}/subscriptions` | `GET` | `200 OK` |
| `unsubscribe(callback)` / `UNSUB` total | `/clients/{client_id}/subscriptions` | `DELETE` | `200 OK` |
| `UNSUB` de ciudad concreta | `/clients/{client_id}/subscriptions/{city}` | `DELETE` | `200 OK` / `404 Not Found` |
| `onWeatherChange(data)` / `NOTIF` | `/clients/{client_id}/notifications` | `GET` | `200 OK` |

## 5. Nota importante sobre callbacks y REST

En RMI, el servidor puede invocar `onWeatherChange(data)` directamente sobre el cliente porque el cliente también expone un objeto remoto. En REST puro no existe esa invocación remota directa: cada interacción empieza con una petición HTTP del cliente.

Por eso, las notificaciones se modelan como un recurso consultable:

```text
GET /clients/{client_id}/notifications
```

Así se mantiene la semántica de suscripción y notificación, pero adaptada al modelo stateless de HTTP.

## 6. Pruebas

Consulta `curl_examples.md` para comandos de prueba.

También puedes usar:

```bash
python client_polling.py http://127.0.0.1:8000 Granada
```

## 7. Captura con Wireshark

Filtro recomendado:

```text
tcp.port == 8000 || http
```

Qué debe observarse:

- Peticiones `GET`, `POST` y `DELETE`.
- Cabeceras HTTP como `Host`, `User-Agent`, `Content-Type` y `Content-Length`.
- Cuerpo JSON legible en las peticiones `POST` y en las respuestas.
- Diferencia clara frente a RMI: aquí se observa HTTP + JSON, mientras que en RMI se observan llamadas JRMI y serialización Java.
