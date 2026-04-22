package meteo;

import java.rmi.registry.LocateRegistry;
import java.rmi.registry.Registry;

/**
 * MAIN DEL SERVIDOR
 * Arranca el registro RMI y publica el objeto remoto bajo el nombre "MeteoService".
 * Equivalente al método start() de MeteoServer en Python.
 */
public class MeteoServer {

    public static void main(String[] args) {
        try {
            // 1. Crear la implementación del servicio
            MeteoServiceImpl service = new MeteoServiceImpl();

            // 2. Arrancar el registro RMI en el puerto 1099 (puerto estándar RMI)
            //    Equivalente a server_sock.bind() + server_sock.listen() en Python
            Registry registry = LocateRegistry.createRegistry(1099);

            // 3. Publicar el objeto bajo el nombre "MeteoService"
            //    Los clientes usarán este nombre para localizarlo
            registry.rebind("MeteoService", service);

            System.out.println("╔══════════════════════════════════════════════╗");
            System.out.println("║      🌤️  SERVIDOR METEO RMI ACTIVO  🌤️        ║");
            System.out.println("╠══════════════════════════════════════════════╣");
            System.out.println("║  Puerto RMI : 1099                           ║");
            System.out.println("║  Servicio   : MeteoService                   ║");
            System.out.println("║  Esperando conexiones...                     ║");
            System.out.println("╚══════════════════════════════════════════════╝");

        } catch (Exception e) {
            System.err.println("[ERROR FATAL] No se pudo arrancar el servidor: " + e.getMessage());
            e.printStackTrace();
        }
    }
}
