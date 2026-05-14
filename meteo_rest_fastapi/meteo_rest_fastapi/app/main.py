from __future__ import annotations

import asyncio
import os
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional

import httpx
from fastapi import FastAPI, Query, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    # dotenv es opcional; también se puede configurar la variable de entorno manualmente.
    pass


# =========================
# Configuración de dominio
# =========================

DEFAULT_CITY = "Madrid"
VALID_VARIABLES = {"temp", "hum", "pres", "wind"}
SUPPORTED_CITIES = [
    "Madrid",
    "Granada",
    "Barcelona",
    "Sevilla",
    "Matalascañas",
    "London",
    "Paris",
    "Malaga",
    "Valencia",
    "Bilbao",
]

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
UPDATE_INTERVAL_SECONDS = int(os.getenv("UPDATE_INTERVAL_SECONDS", "60"))
OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"


# =========================
# Modelos de datos REST/JSON
# =========================

class WeatherValues(BaseModel):
    temp: float = Field(..., description="Temperatura en grados Celsius")
    hum: float = Field(..., description="Humedad relativa en porcentaje")
    pres: float = Field(..., description="Presión atmosférica en hPa")
    wind: float = Field(..., description="Velocidad del viento en m/s")


class WeatherResponse(BaseModel):
    status: int = Field(200, description="Código de estado de la operación")
    city: str
    data: WeatherValues


class CityListResponse(BaseModel):
    status: int = 200
    type: str = "RESP_LIST"
    data: List[str]
    msg: str


class ClientCreateResponse(BaseModel):
    status: int = 201
    client_id: str
    msg: str


class SubscriptionCreate(BaseModel):
    city: str = Field(DEFAULT_CITY, description="Ciudad a monitorizar")
    variables: List[str] = Field(
        default_factory=lambda: ["temp", "hum", "pres", "wind"],
        description="Variables meteorológicas a monitorizar",
    )

    @field_validator("variables")
    @classmethod
    def validate_variables(cls, variables: List[str]) -> List[str]:
        if not variables:
            raise ValueError("Debe indicarse al menos una variable")
        invalid = [v for v in variables if v not in VALID_VARIABLES]
        if invalid:
            raise ValueError(
                f"Variables no permitidas: {invalid}. Permitidas: {sorted(VALID_VARIABLES)}"
            )
        return variables


class SubscriptionResponse(BaseModel):
    status: int = 201
    msg: str
    client_id: str
    city: str
    variables: List[str]
    current: WeatherValues


class SubscriptionInfo(BaseModel):
    city: str
    variables: List[str]
    last_sent: WeatherValues


class SubscriptionListResponse(BaseModel):
    status: int = 200
    client_id: str
    data: List[SubscriptionInfo]


class Notification(BaseModel):
    type: str = "NOTIF"
    city: str
    data: Dict[str, float]
    timestamp: str


class NotificationListResponse(BaseModel):
    status: int = 200
    client_id: str
    data: List[Notification]
    msg: str


class MessageResponse(BaseModel):
    status: int
    msg: str


# =========================
# Estado interno del servidor
# =========================

@dataclass
class SubscriptionState:
    city: str
    variables: List[str]
    last_sent: WeatherValues


clients: set[str] = set()
subscriptions: Dict[str, Dict[str, SubscriptionState]] = {}
notifications: Dict[str, List[Notification]] = {}
city_states: Dict[str, WeatherValues] = {}
state_lock = asyncio.Lock()


# =========================
# Errores de dominio
# =========================

class MeteoError(Exception):
    def __init__(self, code: int, msg: str):
        self.code = code
        self.msg = msg


async def meteo_error_handler(_: Request, exc: MeteoError) -> JSONResponse:
    return JSONResponse(status_code=exc.code, content={"status": exc.code, "msg": exc.msg})


async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"status": 400, "msg": "Petición incorrecta", "detail": exc.errors()},
    )


def require_client(client_id: str) -> None:
    if client_id not in clients:
        raise MeteoError(404, f"Cliente no encontrado: {client_id}")


# =========================
# Lógica de negocio equivalente
# =========================

async def fetch_weather(city: str) -> WeatherValues:
    """
    Equivalente REST de la lógica fetchWeather/fetch_weather del sistema previo.
    Consulta OpenWeatherMap y devuelve únicamente temp, hum, pres y wind.
    """
    if not OPENWEATHER_API_KEY:
        raise MeteoError(
            500,
            "No se ha configurado OPENWEATHER_API_KEY. Define la variable de entorno o usa un fichero .env.",
        )

    params = {
        "q": city,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(OPENWEATHER_URL, params=params)
    except httpx.RequestError as exc:
        raise MeteoError(500, f"Error de conexión con la API externa: {exc}")

    if response.status_code != 200:
        raise MeteoError(404, f"Ciudad no encontrada o no válida: {city}")

    payload = response.json()
    try:
        return WeatherValues(
            temp=float(payload["main"]["temp"]),
            hum=float(payload["main"]["humidity"]),
            pres=float(payload["main"]["pressure"]),
            wind=float(payload.get("wind", {}).get("speed", 0.0)),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise MeteoError(500, f"Respuesta inesperada de la API externa: {exc}")


def detect_changes(current: WeatherValues, last_sent: WeatherValues, variables: List[str]) -> Dict[str, float]:
    """
    Mantiene la semántica del protocolo original: se comparan los valores actuales con
    los últimos valores enviados al cliente y solo se notifican las variables que cambian.
    """
    changes: Dict[str, float] = {}
    for variable in variables:
        current_value = getattr(current, variable)
        previous_value = getattr(last_sent, variable)
        if current_value != previous_value:
            changes[variable] = current_value
    return changes


async def update_loop() -> None:
    """
    Tarea periódica equivalente al hilo update_loop del servidor con sockets/RMI.
    En REST no se invoca un callback remoto; se almacenan notificaciones para que el
    cliente las consulte mediante GET /clients/{client_id}/notifications.
    """
    while True:
        await asyncio.sleep(UPDATE_INTERVAL_SECONDS)

        async with state_lock:
            cities_to_update = {
                sub.city for client_subs in subscriptions.values() for sub in client_subs.values()
            }

        for city in cities_to_update:
            try:
                current = await fetch_weather(city)
            except MeteoError as exc:
                print(f"[UPDATE ERROR] {city}: {exc.msg}")
                continue

            async with state_lock:
                city_states[city] = current
                for client_id, client_subs in subscriptions.items():
                    if city not in client_subs:
                        continue

                    sub = client_subs[city]
                    changes = detect_changes(current, sub.last_sent, sub.variables)
                    if changes:
                        sub.last_sent = current
                        notifications.setdefault(client_id, []).append(
                            Notification(
                                city=city,
                                data=changes,
                                timestamp=datetime.now(timezone.utc).isoformat(),
                            )
                        )


@asynccontextmanager
async def lifespan(_: FastAPI):
    task = asyncio.create_task(update_loop())
    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


# =========================
# Aplicación FastAPI
# =========================

app = FastAPI(
    title="MeteoApp REST API",
    version="1.0.0",
    description=(
        "Transformación del sistema de monitorización meteorológica basado en sockets/RMI "
        "a una API REST con HTTP y JSON. La API mantiene las operaciones LIST, GET, "
        "SUB y UNSUB como recursos REST."
    ),
    contact={"name": "Grupo MeteoApp"},
    license_info={"name": "Uso académico"},
    lifespan=lifespan,
)

app.add_exception_handler(MeteoError, meteo_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)


@app.get("/health", response_model=MessageResponse, tags=["Sistema"])
async def health() -> MessageResponse:
    return MessageResponse(status=200, msg="Servidor REST activo")


@app.get("/cities", response_model=CityListResponse, tags=["Ciudades"])
async def list_cities() -> CityListResponse:
    """Equivalente REST del comando LIST / método remoto listCities()."""
    return CityListResponse(
        data=SUPPORTED_CITIES,
        msg=f"Actualmente tengo {len(SUPPORTED_CITIES)} ciudades disponibles.",
    )


@app.get("/weather", response_model=WeatherResponse, tags=["Meteorología"])
async def get_default_weather(
    city: str = Query(DEFAULT_CITY, description="Ciudad consultada; por defecto Madrid")
) -> WeatherResponse:
    """Consulta puntual del clima. Equivale a GET sin ciudad explícita en el protocolo original."""
    data = await fetch_weather(city)
    return WeatherResponse(city=city, data=data)


@app.get("/weather/{city}", response_model=WeatherResponse, tags=["Meteorología"])
async def get_weather(city: str) -> WeatherResponse:
    """Equivalente REST del comando GET / método remoto getWeather(city)."""
    data = await fetch_weather(city)
    return WeatherResponse(city=city, data=data)


@app.post(
    "/clients",
    response_model=ClientCreateResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Clientes"],
)
async def create_client() -> ClientCreateResponse:
    """
    Crea una identidad de cliente REST.
    Sustituye la conexión TCP o el objeto callback RMI usado para asociar suscripciones.
    """
    client_id = str(uuid.uuid4())
    async with state_lock:
        clients.add(client_id)
        subscriptions[client_id] = {}
        notifications[client_id] = []
    return ClientCreateResponse(client_id=client_id, msg="Cliente REST creado")


@app.delete("/clients/{client_id}", response_model=MessageResponse, tags=["Clientes"])
async def delete_client(client_id: str) -> MessageResponse:
    """Elimina el cliente y todas sus suscripciones, equivalente a cerrar la conexión."""
    async with state_lock:
        require_client(client_id)
        clients.remove(client_id)
        subscriptions.pop(client_id, None)
        notifications.pop(client_id, None)
    return MessageResponse(status=200, msg="Cliente eliminado y suscripciones canceladas")


@app.post(
    "/clients/{client_id}/subscriptions",
    response_model=SubscriptionResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Suscripciones"],
)
async def create_subscription(client_id: str, request: SubscriptionCreate) -> SubscriptionResponse:
    """Equivalente REST del comando SUB / método remoto subscribe(city, callback)."""
    async with state_lock:
        require_client(client_id)
        if request.city in subscriptions[client_id]:
            raise MeteoError(400, f"Ya estás suscrito a las alertas de {request.city}. ✅")

    initial_data = await fetch_weather(request.city)

    async with state_lock:
        subscriptions[client_id][request.city] = SubscriptionState(
            city=request.city,
            variables=request.variables,
            last_sent=initial_data,
        )
        city_states[request.city] = initial_data

    return SubscriptionResponse(
        msg=f"Suscrito a {request.city}",
        client_id=client_id,
        city=request.city,
        variables=request.variables,
        current=initial_data,
    )


@app.get(
    "/clients/{client_id}/subscriptions",
    response_model=SubscriptionListResponse,
    tags=["Suscripciones"],
)
async def list_subscriptions(client_id: str) -> SubscriptionListResponse:
    """Lista las suscripciones activas de un cliente REST."""
    async with state_lock:
        require_client(client_id)
        data = [
            SubscriptionInfo(city=sub.city, variables=sub.variables, last_sent=sub.last_sent)
            for sub in subscriptions[client_id].values()
        ]
    return SubscriptionListResponse(client_id=client_id, data=data)


@app.delete(
    "/clients/{client_id}/subscriptions",
    response_model=MessageResponse,
    tags=["Suscripciones"],
)
async def delete_all_subscriptions(client_id: str) -> MessageResponse:
    """Equivalente REST de UNSUB sin ciudad: cancela todas las suscripciones del cliente."""
    async with state_lock:
        require_client(client_id)
        subscriptions[client_id].clear()
    return MessageResponse(status=200, msg="Todas las suscripciones canceladas")


@app.delete(
    "/clients/{client_id}/subscriptions/{city}",
    response_model=MessageResponse,
    tags=["Suscripciones"],
)
async def delete_subscription(client_id: str, city: str) -> MessageResponse:
    """Equivalente REST de UNSUB con ciudad: cancela una suscripción concreta."""
    async with state_lock:
        require_client(client_id)
        if city not in subscriptions[client_id]:
            raise MeteoError(404, f"No existe una suscripción activa a {city}")
        del subscriptions[client_id][city]
    return MessageResponse(status=200, msg=f"Suscripción a {city} cancelada")


@app.get(
    "/clients/{client_id}/notifications",
    response_model=NotificationListResponse,
    tags=["Notificaciones"],
)
async def get_notifications(
    client_id: str,
    consume: bool = Query(True, description="Si es true, vacía la cola tras devolverla"),
) -> NotificationListResponse:
    """
    Sustituto REST del callback RMI onWeatherChange(data).
    En lugar de invocar al cliente, el servidor expone las notificaciones como recurso consultable.
    """
    async with state_lock:
        require_client(client_id)
        pending = list(notifications.get(client_id, []))
        if consume:
            notifications[client_id] = []

    return NotificationListResponse(
        client_id=client_id,
        data=pending,
        msg=f"{len(pending)} notificaciones pendientes",
    )
