# MeteoApp PRO ☁️ - Sistema de Monitorización Meteorológica

Este proyecto conforma un Asistente Meteorológico de arquitectura distribuida diseñado para **entornos aislados (Máquinas Virtuales)**, compuesto por un motor base TCP estándar (`servidor.py` y `cliente.py`), extendido a través de una App Web interactiva de aspecto premium usando WebSockets.

---

## 🏗️ Arquitectura del Sistema

El proyecto opera con los siguientes componentes principales:

1. **`servidor.py` (Backend Meteorológico)**: Obtiene datos del clima en vivo usando OpenWeatherMap. Trabaja en el puerto TCP nativo `5000`. Manténe un estado reactivo y envía notificaciones PUSH al detectar variaciones climáticas en ciudades suscritas.
2. **`proxy.py` (Puente Web-TCP)**: Actúa como pasarela intermedia bidireccional entre la app web (que corre en un navegador) y el servidor Python. Escucha peticiones WebSocket en el puerto `8080`.
3. **`web/index.html` (MeteoApp PRO)**: El frontend de cliente gráfico. Diseño *Glassmorphism* usando CSS puro e interactividad asíncrona garantizada con Vanilla Javascript.
4. **`cliente.py` (Consola Alternativa)**: Cliente legacy de terminal para interactuar manualmente con JSONs puros si se desea evitar la interfaz gráfica.

---

## 🚀 Requisitos Previos (Instalación)

Como el servidor base está programado en Python, asegúrate de tener instalada una versión moderna del lenguaje en tus distintas Máquinas Virtuales (>= 3.9). Para ejecutar el proxy web, necesitarás instalar su única dependencia moderna:

```bash
pip install websockets
```

*(Opcional: Si careces de `requests` instalado globalmente, ejecútalo también para el servidor base: `pip install requests`)*

---

## 🕹️ Cómo Ejecutar la App Web

El protocolo está diseñado para operar abriendo varias pestañas de terminal a la vez antes de consumir el entorno visual:

1. **Paso 1: Arrancar el Servidor Principal**
   En la primera pestaña de tu terminal/consola, ponte en el directorio principal y ejecuta:
   ```bash
   python src/servidor.py
   ```
   *(Verás el aviso `--- SERVIDOR ACTIVO EN 0.0.0.0:5000 ---`)*

2. **Paso 2: Levantar el Puente de Comunicaciones (Proxy)**
   En una segunda pestaña de terminal independiente, ejecuta:
   ```bash
   python src/proxy.py
   ```
   *(Verás el aviso `--- PROXY WEBSOCKETS INICIADO EN ws://0.0.0.0:8080 ---`)*

3. **Paso 3: Abrir la Interfaz de Usuario Visual**
   Navega a la carpeta `src/web/` y abre el archivo **`index.html`** haciendo doble clic sobre él (o ábrelo usando Visual Studio Code / tu navegador favorito).  
   Pulsa en **Conectar** (usando los puertos `localhost` y `8080` por defecto si los procesos se encuentran hospedados en tu misma MV local) y ¡listo!

### Funcionalidades
- **Consulta Puntual:** Solicitud `GET` simple que imprime el último estado meteorológico registrado.
- **Suscripción a Alertas:** Solicitud `SUB`. A partir de esto, si la temperatura o presión cambian, la aplicación destellará automáticamente con los nuevos datos recibidos.
- **Menú Lateral de Cancelaciones:** Usa el Sidebar Izquierdo (haciendo clic en la 'x' o usando la desconexión manual) para interrumpir el WebSocket local o enviar a tu servidor un comando de cierre `UNSUB`.
