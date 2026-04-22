package meteo;

import java.rmi.Remote;
import java.rmi.RemoteException;

/**
 * INTERFAZ REMOTA DE CALLBACK (patrón Observer sobre RMI).
 * El cliente implementa esta interfaz y la registra en el servidor.
 * Cuando el clima cambia, el servidor invoca onWeatherChange() en el cliente
 * de forma remota — el cliente no necesita "preguntar", el servidor "avisa".
 *
 * DIFERENCIA CLAVE con el sistema anterior:
 * - Antes: servidor enviaba JSON por socket → cliente lo parseaba manualmente.
 * - Ahora: servidor llama a un método Java en el cliente directamente.
 */
public interface MeteoCallback extends Remote {

    /**
     * El servidor invoca este método cuando detecta un cambio en el clima
     * de una ciudad a la que el cliente está suscrito.
     * @param data Nuevos datos meteorológicos
     */
    void onWeatherChange(WeatherData data) throws RemoteException;
}
