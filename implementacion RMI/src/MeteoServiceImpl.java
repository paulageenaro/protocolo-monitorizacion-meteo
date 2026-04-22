package meteo;

import java.rmi.RemoteException;
import java.rmi.server.UnicastRemoteObject;
import java.util.*;
import java.util.concurrent.*;
import java.net.HttpURLConnection;
import java.net.URL;
import org.json.simple.JSONObject;
import org.json.simple.parser.JSONParser;

/**
 * IMPLEMENTACIÓN DEL SERVIDOR
 * Hereda de UnicastRemoteObject para exportarse automáticamente como objeto RMI.
 * Contiene la misma lógica de negocio que MeteoServer en Python:
 * - Consulta a OpenWeatherMap
 * - Gestión de suscripciones
 * - Hilo de actualización periódica
 */
public class MeteoServiceImpl extends UnicastRemoteObject implements MeteoService {

    private static final long serialVersionUID = 1L;
    private static final String API_KEY = "be0c11c0a23c59c181513ee2570c9cd0";

    // Lista de ciudades soportadas (igual que en Python)
    private final List<String> ciudades = Arrays.asList(
        "Madrid", "Granada", "Barcelona", "Sevilla",
        "Matalascañas", "London", "Paris", "Malaga", "Valencia", "Bilbao"
    );

    // Último estado conocido de cada ciudad
    private final Map<String, WeatherData> cityStates = new ConcurrentHashMap<>();

    // Suscripciones: callback → {ciudad → datos enviados por última vez}
    // ConcurrentHashMap para acceso seguro desde múltiples hilos
    private final Map<MeteoCallback, Map<String, WeatherData>> subscriptions
            = new ConcurrentHashMap<>();

    public MeteoServiceImpl() throws RemoteException {
        super();
        // Lanzar hilo de actualización periódica (equivalente a update_loop en Python)
        ScheduledExecutorService scheduler = Executors.newSingleThreadScheduledExecutor();
        scheduler.scheduleAtFixedRate(this::updateLoop, 60, 60, TimeUnit.SECONDS);
    }

    // ── Implementación de la interfaz ──────────────────────────────────────────

    @Override
    public WeatherData getWeather(String city) throws RemoteException, MeteoException {
        System.out.println("[GET] Solicitud para: " + city);
        return fetchWeather(city); // puede lanzar MeteoException
    }

    @Override
    public List<String> listCities() throws RemoteException {
        System.out.println("[LIST] Solicitud de catálogo");
        return Collections.unmodifiableList(ciudades);
    }

    @Override
    public WeatherData subscribe(String city, MeteoCallback callback)
            throws RemoteException, MeteoException {

        System.out.println("[SUB] Suscripción a: " + city);

        // Comprobar si ya está suscrito (equivalente al check en servidor Python)
        subscriptions.putIfAbsent(callback, new ConcurrentHashMap<>());
        Map<String, WeatherData> clientSubs = subscriptions.get(callback);

        if (clientSubs.containsKey(city)) {
            throw new MeteoException(400, "Ya estás suscrito a las alertas de " + city);
        }

        // Obtener datos iniciales
        WeatherData initial = fetchWeather(city);
        cityStates.put(city, initial);
        clientSubs.put(city, initial);

        System.out.println("[SUB] OK → " + city + " para cliente " + callback);
        return initial;
    }

    @Override
    public void unsubscribe(MeteoCallback callback) throws RemoteException {
        subscriptions.remove(callback);
        System.out.println("[UNSUB] Cliente desuscrito de todas las ciudades");
    }

    // ── Lógica interna ─────────────────────────────────────────────────────────

    /**
     * Llama a la API de OpenWeatherMap y devuelve un WeatherData.
     * Equivalente a fetch_weather() en Python.
     */
    private WeatherData fetchWeather(String city) throws MeteoException {
        try {
            String urlStr = "http://api.openweathermap.org/data/2.5/weather?q="
                    + city + "&appid=" + API_KEY + "&units=metric";
            URL url = new URL(urlStr);
            HttpURLConnection conn = (HttpURLConnection) url.openConnection();
            conn.setConnectTimeout(5000);
            conn.setReadTimeout(5000);

            int status = conn.getResponseCode();
            if (status != 200) {
                throw new MeteoException(404, "Ciudad no encontrada: " + city);
            }

            // Leer respuesta JSON
            Scanner sc = new Scanner(conn.getInputStream());
            StringBuilder sb = new StringBuilder();
            while (sc.hasNextLine()) sb.append(sc.nextLine());
            sc.close();

            JSONParser parser = new JSONParser();
            JSONObject json = (JSONObject) parser.parse(sb.toString());
            JSONObject main = (JSONObject) json.get("main");
            JSONObject wind = (JSONObject) json.get("wind");

            double temp  = toDouble(main.get("temp"));
            double hum   = toDouble(main.get("humidity"));
            double pres  = toDouble(main.get("pressure"));
            double windS = toDouble(wind.get("speed"));

            return new WeatherData(city, temp, hum, pres, windS);

        } catch (MeteoException e) {
            throw e;
        } catch (Exception e) {
            throw new MeteoException(500, "Error de conexión con la API: " + e.getMessage());
        }
    }

    private double toDouble(Object o) {
        if (o instanceof Long)   return ((Long) o).doubleValue();
        if (o instanceof Double) return (Double) o;
        return Double.parseDouble(o.toString());
    }

    /**
     * Hilo periódico que actualiza el clima y envía notificaciones.
     * Equivalente a update_loop() + process_notifications() en Python.
     */
    private void updateLoop() {
        // Recopilar ciudades con suscriptores activos
        Set<String> citiesToUpdate = new HashSet<>();
        for (Map<String, WeatherData> subs : subscriptions.values()) {
            citiesToUpdate.addAll(subs.keySet());
        }

        for (String city : citiesToUpdate) {
            try {
                WeatherData newData = fetchWeather(city);
                WeatherData oldData = cityStates.put(city, newData);

                // Notificar a cada suscriptor si algo cambió
                for (Map.Entry<MeteoCallback, Map<String, WeatherData>> entry
                        : subscriptions.entrySet()) {

                    MeteoCallback cb = entry.getKey();
                    Map<String, WeatherData> clientSubs = entry.getValue();

                    if (clientSubs.containsKey(city)) {
                        WeatherData lastSent = clientSubs.get(city);
                        // Detectar cambio significativo (temp o viento, igual que en Python)
                        boolean changed = oldData == null
                            || Math.abs(newData.getTemp() - lastSent.getTemp()) >= 0.5
                            || Math.abs(newData.getWind() - lastSent.getWind()) >= 0.5;

                        if (changed) {
                            try {
                                cb.onWeatherChange(newData);   // ← INVOCACIÓN REMOTA al cliente
                                clientSubs.put(city, newData);
                            } catch (RemoteException e) {
                                // Cliente desconectado → limpiar suscripción
                                System.out.println("[INFO] Cliente desconectado, eliminando suscripción.");
                                subscriptions.remove(cb);
                            }
                        }
                    }
                }
            } catch (MeteoException e) {
                System.err.println("[UPDATE ERROR] " + city + ": " + e.getMessage());
            }
        }
    }
}
