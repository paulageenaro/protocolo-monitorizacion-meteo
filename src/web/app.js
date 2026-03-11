// ELEMENTOS DEL DOM
const ui = {
    networkSetup: document.getElementById('networkSetup'),
    controlPanel: document.getElementById('controlPanel'),
    connStatus: document.getElementById('connStatus'),
    wsHost: document.getElementById('wsHost'),
    wsPort: document.getElementById('wsPort'),
    btnConnect: document.getElementById('btnConnect'),
    
    cityInput: document.getElementById('cityInput'),
    btnGet: document.getElementById('btnGet'),
    btnSub: document.getElementById('btnSub'),
    btnUnsub: document.getElementById('btnUnsub'),
    
    weatherDisplay: document.getElementById('weatherDisplay'),
    displayCity: document.getElementById('displayCity'),
    liveIndicator: document.getElementById('liveIndicator'),
    
    valTemp: document.getElementById('valTemp'),
    valHum: document.getElementById('valHum'),
    valWind: document.getElementById('valWind'),
    valPres: document.getElementById('valPres'),
    
    systemLog: document.getElementById('systemLog'),
    subscriptionsSidebar: document.getElementById('subscriptionsSidebar'),
    subList: document.getElementById('subList'),
    btnDisconnect: document.getElementById('btnDisconnect')
};

let ws = null;
let activeSubscriptions = []; // Ahora soporte a múltiples visualmente

// FUNCIONES DE UTILIDAD
function logMsg(message, type = 'system') {
    const entry = document.createElement('div');
    entry.className = `log-entry ${type}`;
    const time = new Date().toLocaleTimeString();
    entry.textContent = `[${time}] ${message}`;
    ui.systemLog.appendChild(entry);
    ui.systemLog.scrollTop = ui.systemLog.scrollHeight;
}

function updateWeatherUI(city, data) {
    ui.weatherDisplay.classList.remove('hidden');
    ui.displayCity.textContent = city;
    
    if (data.temp !== undefined) ui.valTemp.textContent = data.temp.toFixed(1);
    if (data.hum !== undefined) ui.valHum.textContent = data.hum;
    if (data.wind !== undefined) ui.valWind.textContent = data.wind;
    if (data.pres !== undefined) ui.valPres.textContent = data.pres;
}

// GESTIÓN DE WEBSOCKETS
function renderSubscriptions() {
    ui.subList.innerHTML = ''; // Limpiar lista
    
    if (activeSubscriptions.length === 0) {
        ui.subscriptionsSidebar.classList.add('hidden');
        return;
    }
    
    ui.subscriptionsSidebar.classList.remove('hidden');
    
    activeSubscriptions.forEach(city => {
        const li = document.createElement('li');
        li.className = 'sub-item';
        
        // Destacar la última ciudad consultada/suscrita
        if (ui.displayCity.textContent.includes(city)) {
            li.classList.add('active');
        }
        
        li.innerHTML = `
            <span>📍 ${city}</span>
            <span style="font-size: 0.8rem; color: var(--success-color)">Activa</span>
        `;
        
        // Hacer click en la ciudad del sidebar la consulta inmediatamente
        li.style.cursor = 'pointer';
        li.addEventListener('click', () => {
             ui.cityInput.value = city;
             ui.btnGet.click();
        });
        
        ui.subList.appendChild(li);
    });
}

function connectWS() {
    const host = ui.wsHost.value.trim() || 'localhost';
    const port = ui.wsPort.value.trim() || '8080';
    const url = `ws://${host}:${port}`;
    
    logMsg(`Conectando a ${url}...`, 'system');
    
    try {
        ws = new WebSocket(url);
        
        ws.onopen = () => {
            ui.connStatus.textContent = 'CONECTADO';
            ui.connStatus.classList.add('connected');
            ui.networkSetup.classList.add('hidden');
            ui.controlPanel.classList.remove('hidden');
            logMsg('Conexión establecida con el Proxy WebSocket.', 'system');
        };
        
        ws.onclose = () => {
            ui.connStatus.textContent = 'DESCONECTADO';
            ui.connStatus.classList.remove('connected');
            ui.networkSetup.classList.remove('hidden');
            ui.controlPanel.classList.add('hidden');
            ui.weatherDisplay.classList.add('hidden');
            activeSubscriptions = [];
            renderSubscriptions();
            ui.liveIndicator.classList.add('hidden');
            logMsg('Desconectado del servidor Proxy.', 'error');
            ws = null;
        };
        
        ws.onerror = (error) => {
            logMsg('Error de conexión WebSocket.', 'error');
        };
        
        ws.onmessage = (event) => {
            logMsg(`RX: ${event.data}`, 'received');
            try {
                const msg = JSON.parse(event.data);
                
                // Respuesta a un GET o SUB
                if (msg.status === 200) {
                    if (msg.data || msg.current) {
                        updateWeatherUI(msg.city, msg.data || msg.current);
                    }
                } 
                // Notificación de Cambio (PUSH)
                else if (msg.type === "NOTIF") {
                    logMsg(`¡Alerta! Cambios en ${msg.city}: ${JSON.stringify(msg.data)}`, 'alert');
                    updateWeatherUI(msg.city, msg.data);
                    
                    // Efecto visual flash
                    ui.weatherDisplay.style.transform = 'scale(1.02)';
                    ui.weatherDisplay.style.borderColor = 'var(--accent-color)';
                    setTimeout(() => {
                        ui.weatherDisplay.style.transform = 'scale(1)';
                        ui.weatherDisplay.style.borderColor = 'transparent';
                    }, 300);
                }
                // Error del servidor (ej. 404)
                else if (msg.status && msg.status !== 200) {
                    logMsg(`Error Servidor: ${msg.msg}`, 'error');
                    alert(`Error: ${msg.msg}`);
                }
            } catch (e) {
                console.error("Error parseando JSON:", e);
            }
        };
    } catch (e) {
        logMsg(`Excepción al conectar: ${e}`, 'error');
    }
}

function sendCommand(cmdObj) {
    if (!ws || ws.readyState !== WebSocket.OPEN) {
        alert("No estás conectado al servidor.");
        return;
    }
    const payload = JSON.stringify(cmdObj);
    ws.send(payload);
    logMsg(`TX: ${payload}`, 'sent');
}

// EVENT LISTENERS
ui.btnConnect.addEventListener('click', connectWS);

ui.btnDisconnect.addEventListener('click', () => {
    if (ws && ws.readyState === WebSocket.OPEN) {
        logMsg('Cerrando conexión manualmente...', 'system');
        ws.close(1000, "Desconexión iniciada por el usuario");
    }
});

ui.btnGet.addEventListener('click', () => {
    const city = ui.cityInput.value.trim() || 'Madrid';
    sendCommand({ "command": "GET", "city": city });
});

ui.btnSub.addEventListener('click', () => {
    const city = ui.cityInput.value.trim() || 'Madrid';
    sendCommand({ 
        "command": "SUB", 
        "city": city, 
        "variables": ["temp", "hum", "wind", "pres"] 
    });
    
    if (!activeSubscriptions.includes(city)) {
        activeSubscriptions.push(city);
    }
    renderSubscriptions();
    
    ui.displayCity.innerHTML = `${city} <span style="font-size:1rem;color:var(--success-color);">(Suscrito)</span>`;
    ui.liveIndicator.classList.remove('hidden');
});

ui.btnUnsub.addEventListener('click', () => {
    const city = ui.cityInput.value.trim() || 'Madrid';
    // El comando de este servidor en UNSUB es global por conexión actualmente, 
    // pero borramos todas las visuales para simplificar la demostración, o borrar la ciudad actual si el backend lo soportara.
    sendCommand({ "command": "UNSUB" });
    
    activeSubscriptions = [];
    renderSubscriptions();
    ui.liveIndicator.classList.add('hidden');
    
    // Limpiar indicador de suscripción en UI
    ui.displayCity.innerHTML = city;
});

// Soporte "Enter" en el input IP
ui.wsPort.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') connectWS();
});

// Soporte "Enter" en búsqueda de ciudad para GET rápido
ui.cityInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') ui.btnGet.click();
});
