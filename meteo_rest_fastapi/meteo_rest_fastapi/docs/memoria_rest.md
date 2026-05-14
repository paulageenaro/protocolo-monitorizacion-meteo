# Transformación del sistema MeteoApp a REST

## 1. Tabla de transformación de métodos a recursos REST

| Operación anterior | Semántica | Endpoint REST | Método HTTP | Código correcto |
|---|---|---|---:|---:|
| `LIST` / `listCities()` | Obtener catálogo de ciudades disponibles | `/cities` | `GET` | `200 OK` |
| `GET` / `getWeather(city)` | Consultar el estado meteorológico actual de una ciudad | `/weather/{city}` | `GET` | `200 OK` o `404 Not Found` |
| `GET` sin ciudad | Consultar ciudad por defecto | `/weather?city=Madrid` | `GET` | `200 OK` |
| `SUB` / `subscribe(city, callback)` | Crear una suscripción meteorológica | `/clients/{client_id}/subscriptions` | `POST` | `201 Created` |
| `SUB` duplicado | Suscripción repetida a una misma ciudad | `/clients/{client_id}/subscriptions` | `POST` | `400 Bad Request` |
| `UNSUB` total / `unsubscribe(callback)` | Cancelar todas las suscripciones de un cliente | `/clients/{client_id}/subscriptions` | `DELETE` | `200 OK` |
| `UNSUB` con ciudad | Cancelar una ciudad concreta | `/clients/{client_id}/subscriptions/{city}` | `DELETE` | `200 OK` o `404 Not Found` |
| `NOTIF` / `onWeatherChange(data)` | Recibir cambios meteorológicos pendientes | `/clients/{client_id}/notifications` | `GET` | `200 OK` |

## 2. Diferencias respecto a objetos distribuidos

En la versión con objetos distribuidos, el cliente invoca métodos remotos como si fueran métodos Java ordinarios. La comunicación queda oculta por RMI: el cliente obtiene una referencia remota, llama a `getWeather`, `listCities` o `subscribe`, y el sistema se encarga de serializar los objetos y transportar la invocación. Además, el mecanismo de callback permite que el servidor invoque `onWeatherChange(data)` sobre el cliente cuando detecta cambios meteorológicos.

En la versión REST, la comunicación se hace explícita mediante HTTP. Cada operación se expresa como una petición sobre un recurso: las ciudades se consultan con `GET /cities`, el tiempo de una ciudad con `GET /weather/{city}` y las suscripciones se crean con `POST /clients/{client_id}/subscriptions`. La información viaja en JSON, de forma legible y fácilmente interpretable por herramientas como navegador, `curl`, Bruno o Wireshark.

La diferencia más importante está en las notificaciones. RMI permite invocación remota desde el servidor hacia el cliente mediante callbacks. REST, en cambio, es un modelo petición-respuesta iniciado por el cliente. Por ello, las notificaciones se han transformado en un recurso consultable: `GET /clients/{client_id}/notifications`. El servidor mantiene una cola de notificaciones pendientes y el cliente las consulta periódicamente.

## 3. Ventajas e inconvenientes de REST

REST simplifica la interoperabilidad porque no obliga a que cliente y servidor estén escritos en el mismo lenguaje ni compartan clases Java serializables. Cualquier cliente capaz de emitir peticiones HTTP y procesar JSON puede utilizar la API. También facilita la depuración, ya que los mensajes son legibles y se pueden probar directamente desde Swagger, `curl` o Bruno.

Otra ventaja es la documentación automática. Al usar FastAPI, los modelos de datos y los endpoints generan una especificación OpenAPI y una interfaz Swagger accesible desde `/docs`. Esto permite comprobar los recursos disponibles, los parámetros necesarios y los códigos de estado esperados sin escribir documentación externa desde cero.

Como inconveniente, REST no reproduce de forma natural el callback asíncrono de RMI. Para mantener un diseño REST puro, las notificaciones deben consultarse mediante polling o modelarse como recursos pendientes. Esto introduce más peticiones HTTP y puede aumentar la latencia entre el cambio meteorológico y la recepción de la notificación por parte del cliente.

## 4. Discusión técnica

### Stateless

HTTP es stateless: cada petición debe contener la información necesaria para ser interpretada. En sockets y RMI, la suscripción estaba asociada a la conexión o al callback remoto del cliente. En REST se ha introducido un `client_id`, creado mediante `POST /clients`, para identificar al cliente en las operaciones posteriores. De esta forma, el servidor puede mantener suscripciones asociadas a un identificador explícito y no a una conexión persistente.

### Diseño de URLs

Se han evitado rutas de tipo acción como `/sendMessage`, `/getWeather` o `/subscribe`. En su lugar, las URLs representan recursos: `/cities`, `/weather/{city}`, `/clients/{client_id}/subscriptions` y `/clients/{client_id}/notifications`. La operación se decide con el método HTTP: `GET` para consultar, `POST` para crear y `DELETE` para cancelar.

### Gestión de estado

El estado principal del servidor está formado por clientes registrados, suscripciones activas, último valor enviado y cola de notificaciones. Esta información permite mantener la lógica funcional del sistema previo: evitar suscripciones duplicadas, comparar el estado meteorológico actual con el último enviado y generar notificaciones cuando cambia alguna variable suscrita.

### Problemas abordados

El primer problema ha sido traducir operaciones RPC a recursos REST sin convertir la API en una lista de acciones. El segundo ha sido adaptar el callback remoto a REST, resolviéndolo mediante una cola de notificaciones consultable. El tercero ha sido mantener códigos de estado HTTP coherentes: `200 OK` para consultas correctas, `201 Created` al crear clientes o suscripciones, `400 Bad Request` para duplicados o peticiones inválidas y `404 Not Found` cuando no existe una ciudad, cliente o suscripción.
