# Implementación RMI: Protocolo de Monitorización Meteorológica

Esta carpeta contiene una implementación alternativa y mejorada del protocolo de monitorización meteorológica, sustituyendo la comunicación directa mediante sockets TCP y mensajes JSON por **Java RMI (Remote Method Invocation)**.

## 1. Diseño y Arquitectura

Con RMI, la semántica del sistema cambia de un esquema de paso de mensajes a llamadas a métodos remotos (RPC). El cliente invoca directamente los métodos definidos en el servidor, sin necesidad de parsear el formato JSON, lo cual simplifica enormemente la programación, abstrae la capa de red y hace que el contrato de comunicación esté garantizado en tiempo de compilación.

La arquitectura se basa en las siguientes interfaces y clases:

- **`MeteoService`**: Interfaz remota principal (el contrato). Define las operaciones equivalentes a los comandos del flujo TCP:
  - `getWeather(city)` $\rightarrow$ Equivalente a `GET`
  - `listCities()` $\rightarrow$ Equivalente a `LIST`
  - `subscribe(city, callback)` $\rightarrow$ Equivalente a `SUB`
  - `unsubscribe(callback)` $\rightarrow$ Equivalente a `UNSUB`
- **`MeteoServiceImpl`**: Implementación en el servidor de las operaciones descritas en `MeteoService`. Gestiona el estado y las suscripciones de los clientes.
- **`MeteoCallback`**: Interfaz remota que el cliente implementa y pasa al servidor. Es usada por el servidor para notificar al cliente de actualizaciones (Patrón Observer / Eventos).
- **`WeatherData`**: Objeto serializable que contiene la información del clima transmitida entre nodos.
- **`MeteoException`**: Excepción customizada para notificar errores de lógica de negocio (por ejemplo, si la ciudad no existe).
- **`MeteoServer`**: Ejecutable que registra el servicio en el RMI Registry.
- **`MeteoClient`**: Ejecutable que localiza el servicio en el registry y consume sus métodos remotos.

## 2. Ventajas del paso de Sockets/JSON a RMI

- **Tipado Fuerte**: En TCP/JSON se dependía de cadenas de texto y conversiones manuales. Aquí se utilizan los propios tipos de Java (`String`, `List`, `WeatherData`).
- **Adiós al Parsing**: No es necesario deserializar JSON ni mantener un bucle infinito que interprete tramas entrantes.
- **Transparencia de Ubicación**: Invocar un método remoto se ve exactamente igual que llamar a un objeto local.
- **Callbacks Directos**: La suscripción (SUB) se implementa pasando una referencia remota del cliente al servidor. El servidor simplemente invoca el método del callback y RMI se encarga de que se ejecute en la máquina del cliente, ideal para el modo asíncrono.

## 3. Instrucciones de Ejecución

Para ejecutar esta versión:

1. **Compilar** los archivos `.java` que se encuentran en el directorio `src`.
2. **Iniciar el RMI Registry** (opcional si el `MeteoServer` lo crea internamente; si no, ejecutar `rmiregistry` o similar).
3. **Ejecutar el Servidor** (`MeteoServer`).
4. **Ejecutar el Cliente** (`MeteoClient`) y probar los métodos equivalentes al menú clásico de comandos.
