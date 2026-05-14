# Pruebas en Bruno

Crea una colección nueva y añade estas peticiones:

1. `GET http://IP_SERVIDOR:8000/health`
2. `GET http://IP_SERVIDOR:8000/cities`
3. `GET http://IP_SERVIDOR:8000/weather/Granada`
4. `POST http://IP_SERVIDOR:8000/clients`
5. `POST http://IP_SERVIDOR:8000/clients/{{client_id}}/subscriptions`

Body JSON para la suscripción:

```json
{
  "city": "Granada",
  "variables": ["temp", "hum", "pres", "wind"]
}
```

6. `GET http://IP_SERVIDOR:8000/clients/{{client_id}}/notifications`
7. `DELETE http://IP_SERVIDOR:8000/clients/{{client_id}}/subscriptions/Granada`
8. `DELETE http://IP_SERVIDOR:8000/clients/{{client_id}}`
