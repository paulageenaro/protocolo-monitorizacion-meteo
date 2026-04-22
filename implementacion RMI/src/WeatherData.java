package meteo;

import java.io.Serializable;
import java.util.Map;

/**
 * Objeto de transferencia de datos meteorológicos.
 * Debe ser Serializable para viajar por la red RMI.
 * Equivale al diccionario Python {"temp":..., "hum":..., "pres":..., "wind":...}
 */
public class WeatherData implements Serializable {
    private static final long serialVersionUID = 1L;

    private final String city;
    private final double temp;
    private final double hum;
    private final double pres;
    private final double wind;

    public WeatherData(String city, double temp, double hum, double pres, double wind) {
        this.city = city;
        this.temp = temp;
        this.hum = hum;
        this.pres = pres;
        this.wind = wind;
    }

    public String getCity() { return city; }
    public double getTemp() { return temp; }
    public double getHum()  { return hum; }
    public double getPres() { return pres; }
    public double getWind() { return wind; }

    @Override
    public String toString() {
        return String.format(
            "🌡️  Temp: %.1f°C  💧 Humedad: %.0f%%  🔵 Presión: %.0f hPa  💨 Viento: %.1f m/s",
            temp, hum, pres, wind
        );
    }
}
