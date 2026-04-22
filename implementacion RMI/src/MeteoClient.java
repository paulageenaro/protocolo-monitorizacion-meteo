package meteo;

import java.rmi.RemoteException;
import java.rmi.registry.LocateRegistry;
import java.rmi.registry.Registry;
import java.rmi.server.UnicastRemoteObject;
import java.text.SimpleDateFormat;
import java.util.*;

/**
 * CLIENTE RMI
 * Implementa MeteoCallback (es un objeto remoto también, para recibir notificaciones).
 * La lógica de usuario es equivalente al cliente Python, pero sin parsear JSON:
 * los métodos remotos devuelven objetos Java tipados directamente.
 */
public class MeteoClient extends UnicastRemoteObject implements MeteoCallback {

    private static final long serialVersionUID = 1L;

    // Colores ANSI (igual que en el cliente Python)
    private static final String AZUL     = "\033[94m";
    private static final String VERDE    = "\033[92m";
    private static final String AMARILLO = "\033[93m";
    private static final String ROJO     = "\033[91m";
    private static final String RESET    = "\033[0m";
    private static final String BOLD     = "\033[1m";

    private final MeteoService server; // referencia al objeto remoto
    private boolean suscrito = false;

    public MeteoClient(MeteoService server) throws RemoteException {
        super(); // exportar este objeto como remoto (necesario para el callback)
        this.server = server;
    }

    // ── Implementación del Callback (el servidor llama a este método) ──────────

    /**
     * EL SERVIDOR llama a este método de forma remota cuando el clima cambia.
     * No hay hilo de escucha manual, no hay parseo de JSON: RMI lo gestiona todo.
     */
    @Override
    public void onWeatherChange(WeatherData data) throws RemoteException {
        String hora = new SimpleDateFormat("HH:mm:ss").format(new Date());
        System.out.println("\n" + AMARILLO + BOLD
            + "⚠️  [" + hora + "] ALERTA - Cambio en " + data.getCity().toUpperCase()
            + RESET);
        System.out.println(AMARILLO + "   " + data + RESET);
        System.out.print(AZUL + "\nTú > " + RESET);
    }

    // ── Interfaz de usuario ────────────────────────────────────────────────────

    private void mostrarMenu() {
        System.out.println("\n" + BOLD + AZUL
            + "┌─────────────────────────────────────────────────────┐");
        System.out.println("│          🌤️  ASISTENTE METEO RMI v1.0  🌤️          │");
        System.out.println("├─────────────────────────────────────────────────────┤");
        System.out.println("│ " + AMARILLO + "COMANDOS DISPONIBLES:" + AZUL + "                              │");
        System.out.println("│                                                     │");
        System.out.println("│ " + VERDE + "list" + AZUL + "            → Ver ciudades disponibles 📂      │");
        System.out.println("│ " + VERDE + "get <ciudad>" + AZUL + "    → Consultar el tiempo 🌡️           │");
        System.out.println("│ " + VERDE + "sub <ciudad>" + AZUL + "    → Suscribirse a alertas 🔔         │");
        System.out.println("│ " + VERDE + "unsub" + AZUL + "           → Cancelar suscripciones ❌        │");
        System.out.println("│ " + VERDE + "salir" + AZUL + "           → Salir 👋                         │");
        System.out.println("└─────────────────────────────────────────────────────┘"
            + RESET + "\n");
    }

    public void run() {
        mostrarMenu();
        Scanner sc = new Scanner(System.in);

        while (true) {
            System.out.print(AZUL + "Tú > " + RESET);
            if (!sc.hasNextLine()) break;
            String linea = sc.nextLine().trim();
            if (linea.isEmpty()) continue;

            String[] partes = linea.split("\\s+", 2);
            String cmd = partes[0].toLowerCase();

            switch (cmd) {
                case "list" -> cmdList();
                case "get"  -> {
                    if (partes.length < 2) {
                        System.out.println(ROJO + "[!] Uso: get <ciudad>" + RESET);
                    } else {
                        cmdGet(partes[1]);
                    }
                }
                case "sub"  -> {
                    if (partes.length < 2) {
                        System.out.println(ROJO + "[!] Uso: sub <ciudad>" + RESET);
                    } else {
                        cmdSub(partes[1]);
                    }
                }
                case "unsub" -> cmdUnsub();
                case "salir", "exit", "quit" -> {
                    cmdUnsub();
                    System.out.println(VERDE + "¡Hasta pronto! 👋" + RESET);
                    return;
                }
                default -> System.out.println(AMARILLO
                    + "[!] Comando no reconocido. Escribe 'list', 'get <ciudad>', "
                    + "'sub <ciudad>', 'unsub' o 'salir'." + RESET);
            }
        }
    }

    // ── Comandos ───────────────────────────────────────────────────────────────

    private void cmdList() {
        try {
            List<String> cities = server.listCities(); // ← INVOCACIÓN REMOTA
            System.out.println(VERDE + BOLD + "\n[SERVIDOR]: Ciudades disponibles:" + RESET);
            System.out.println(AZUL + "📍 " + String.join(", ", cities) + RESET);
        } catch (RemoteException e) {
            System.out.println(ROJO + "[ERROR RED] " + e.getMessage() + RESET);
        }
    }

    private void cmdGet(String city) {
        try {
            WeatherData data = server.getWeather(city); // ← INVOCACIÓN REMOTA
            System.out.println(VERDE + BOLD + "\n[SERVIDOR]: Clima en " + city + ":" + RESET);
            System.out.println(VERDE + "  " + data + RESET);
        } catch (MeteoException e) {
            System.out.println(ROJO + "[SERVIDOR]: " + e + RESET);
        } catch (RemoteException e) {
            System.out.println(ROJO + "[ERROR RED]: " + e.getMessage() + RESET);
        }
    }

    private void cmdSub(String city) {
        try {
            WeatherData initial = server.subscribe(city, this); // ← INVOCACIÓN REMOTA
            suscrito = true;
            System.out.println(VERDE + BOLD + "\n✅ ¡Suscrito a " + city + "!" + RESET);
            System.out.println(VERDE + "  Estado inicial → " + initial + RESET);
            System.out.println(VERDE
                + "  Recibirás alertas automáticamente cuando el clima cambie. 🔔" + RESET);
        } catch (MeteoException e) {
            System.out.println(ROJO + "[SERVIDOR]: " + e + RESET);
        } catch (RemoteException e) {
            System.out.println(ROJO + "[ERROR RED]: " + e.getMessage() + RESET);
        }
    }

    private void cmdUnsub() {
        if (!suscrito) {
            System.out.println(AMARILLO + "[!] No tienes suscripciones activas." + RESET);
            return;
        }
        try {
            server.unsubscribe(this); // ← INVOCACIÓN REMOTA
            suscrito = false;
            System.out.println(VERDE + "❌ Suscripciones canceladas correctamente." + RESET);
        } catch (RemoteException e) {
            System.out.println(ROJO + "[ERROR RED]: " + e.getMessage() + RESET);
        }
    }

    // ── Main ───────────────────────────────────────────────────────────────────

    public static void main(String[] args) {
        System.out.print("\033[94mIP del servidor (Enter para 'localhost'): \033[0m");
        Scanner sc = new Scanner(System.in);
        String ip = sc.nextLine().trim();
        if (ip.isEmpty()) ip = "localhost";

        // Para que el callback funcione en red, el cliente debe ser alcanzable
        System.setProperty("java.rmi.server.hostname", ip.equals("localhost") ? "127.0.0.1" : getLocalIP());

        try {
            // Localizar el registro RMI en el servidor
            Registry registry = LocateRegistry.getRegistry(ip, 1099);

            // Obtener referencia al objeto remoto por nombre
            MeteoService service = (MeteoService) registry.lookup("MeteoService");

            System.out.println("\033[92m✅ Conectado al servidor RMI en " + ip + ":1099\033[0m");

            MeteoClient client = new MeteoClient(service);
            client.run();

        } catch (java.rmi.NotBoundException e) {
            System.err.println("\033[91m[ERROR] Servicio 'MeteoService' no encontrado en el registro.\033[0m");
        } catch (RemoteException e) {
            System.err.println("\033[91m[ERROR RED] No se pudo conectar: " + e.getMessage() + "\033[0m");
            System.err.println("  → ¿Está el servidor arrancado? ¿IP correcta?");
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    private static String getLocalIP() {
        try {
            return java.net.InetAddress.getLocalHost().getHostAddress();
        } catch (Exception e) {
            return "127.0.0.1";
        }
    }
}
