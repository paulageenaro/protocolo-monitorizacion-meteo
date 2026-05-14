# Pruebas con curl

Arranque del servidor:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Comprobar que el servidor está activo:

```bash
curl -i http://127.0.0.1:8000/health
```

Listar ciudades:

```bash
curl -i http://127.0.0.1:8000/cities
```

Consultar el tiempo de Granada:

```bash
curl -i http://127.0.0.1:8000/weather/Granada
```

Crear cliente REST:

```bash
curl -i -X POST http://127.0.0.1:8000/clients
```

Sustituye `<CLIENT_ID>` por el identificador devuelto.

Crear una suscripción:

```bash
curl -i -X POST http://127.0.0.1:8000/clients/<CLIENT_ID>/subscriptions \
  -H "Content-Type: application/json" \
  -d '{"city":"Granada","variables":["temp","hum","pres","wind"]}'
```

Ver suscripciones activas:

```bash
curl -i http://127.0.0.1:8000/clients/<CLIENT_ID>/subscriptions
```

Consultar notificaciones pendientes:

```bash
curl -i http://127.0.0.1:8000/clients/<CLIENT_ID>/notifications
```

Cancelar una suscripción concreta:

```bash
curl -i -X DELETE http://127.0.0.1:8000/clients/<CLIENT_ID>/subscriptions/Granada
```

Cancelar todas las suscripciones:

```bash
curl -i -X DELETE http://127.0.0.1:8000/clients/<CLIENT_ID>/subscriptions
```

Borrar el cliente:

```bash
curl -i -X DELETE http://127.0.0.1:8000/clients/<CLIENT_ID>
```
