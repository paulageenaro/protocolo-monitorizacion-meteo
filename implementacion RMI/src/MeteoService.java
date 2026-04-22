package meteo;

import java.rmi.Remote;
import java.rmi.RemoteException;
import java.util.List;

/**
 * INTERFAZ REMOTA PRINCIPAL - MeteoService
 *
 * Define las 4 operaciones del sistema, equivalentes al protocolo JSON anterior:
 *   GET   → getWeather(city)
 *   LIST  → listCities()
 *   SUB   → subscribe(city, callback)
 *   UNSUB → unsubscribe(callback)
 *
 * VENTAJA sobre sockets: el cliente llama a métodos Java normales.
 * No hay que construir ni parsear JSON manualmente.
 */
public interface MeteoService extends Remote {

    /** Obtiene el clima actual de una ciudad. Equivale al comando GET. */
    WeatherData getWeather(String city) throws RemoteException, MeteoException;

    /** Lista las ciudades disponibles en el servidor. Equivale al comando LIST. */
    List<String> listCities() throws RemoteException;

    /**
     * Suscribe al cliente a alertas de cambio en una ciudad.
     * Equivale al comando SUB. Devuelve el estado inicial.
     * El servidor guardará la referencia remota 'callback' y la usará
     * para notificar al cliente sin que éste tenga que preguntar.
     */
    WeatherData subscribe(String city, MeteoCallback callback)
            throws RemoteException, MeteoException;

    /**
     * Cancela todas las suscripciones del cliente.
     * Equivale al comando UNSUB.
     */
    void unsubscribe(MeteoCallback callback) throws RemoteException;
}
