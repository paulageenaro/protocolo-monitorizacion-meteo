package meteo;

import java.rmi.RemoteException;

/**
 * Excepción remota personalizada.
 * Se lanza cuando hay errores de lógica de negocio (ciudad no encontrada,
 * ya suscrito, etc.) y viaja por la red igual que cualquier otro objeto RMI.
 */
public class MeteoException extends Exception {
    private final int code;

    public MeteoException(int code, String message) {
        super(message);
        this.code = code;
    }

    public int getCode() { return code; }

    @Override
    public String toString() {
        return "[ERROR " + code + "] " + getMessage();
    }
}
