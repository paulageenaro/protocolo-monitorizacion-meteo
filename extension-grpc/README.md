# Ampliación Voluntaria: Evolución del Protocolo usando gRPC y Protocol Buffers

Esta carpeta contiene el planteamiento de la ampliación voluntaria. El rediseño consiste en evolucionar el protocolo original (basado en un paso de comandos genéricos JSON sobre TCP) a un contrato tipado mediante **Protocol Buffers** y **gRPC**.

## 1. Diseño y Estructura

El objetivo ha sido priorizar la simplicidad (la ruta que tomaría un estudiante para adaptar el mismo sistema sin inventar operaciones extrañas) conservando la semántica estricta del ejercicio. 

Se ha definido un documento central, el `meteo.proto` en formato estándar `proto3`. Los comandos textuales desaparecen dando paso a llamadas a métodos remotos formales y estructurados (RPC).

### Tabla de Traducción de Operaciones (TCP -> gRPC)

| Acción Original | Mensaje JSON Original (Flujo TCP) | Alternativa gRPC (.proto propuesto) | Justificación |
|---|---|---|---|
| **Catálogo** | `{"command": "LIST"}` | `ListCities(EmptyRequest)` | No hacen falta argumentos, devuelve un struct `CityListResponse` con una lista. |
| **Consultar** | `{"command": "GET", "city": "X"}` | `GetWeather(WeatherRequest)` | Un método síncrono 1 a 1 que recibe la ciudad y te devuelve su temperatura pura. |
| **Suscribir** | `{"command": "SUB", "city": "X"}` | `SubscribeWeather(SubscribeRequest) returns (stream WeatherNotification)` | Es la forma más natural y nativa de gRPC. No simulas que la suscripción está guardada eternamente; en lugar de eso le das al cliente un tubo (el `stream`) por el que el servidor te inyecta en background las actualizaciones de clima hasta que cierres el grifo. |
| **Cancelar** | `{"command": "UNSUB"}` | *(Controlado por cliente del Stream)* | Gracias al uso correcto del `stream`, al dejar de escuchar los paquetes o cerrar tu cliente de gRPC, la librería gRPC del servidor se da cuenta en milisegundos y cancela ese recurso sola. Te ahorras crear el comando `UNSUB`. |

## 2. Generación automática de Stubs

Para demostrar cómo funciona la tecnología, se proporcionan dos scripts de autogeneración. Éstos traducen el contrato `.proto` en código base de Python listo para interconectar si se fuera a codificar el microservicio real.

> **Instalar dependencias necesarias (Si lo pruebas localmente en Python):**
> ```bash
> pip install grpcio grpcio-tools
> ```

A continuación, basta ejecutar:
- **En Windows:** Ejecutar el archivo `generar_stubs.bat`.
- **En Linux/Mac:** Ejecutar el archivo `./generar_stubs.sh` en terminal.

Una vez ejecutados correctamente, gRPC creará los módulos `meteo_pb2.py` y `meteo_pb2_grpc.py`. Esto defiende y prueba la validez de tu diseño `.proto`.
