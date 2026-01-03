import json
import time
import random
import paho.mqtt.client as mqtt
from datetime import datetime
from sensor_factory import create_sensor

# Percorsi file nel container Docker
CONFIG_PATH = '/app/config/sensor_config.json'

print("--- AVVIO SIMULATORE IIoT ---")

# 1. Caricamento Configurazione
try:
    with open(CONFIG_PATH, 'r') as f:
        config = json.load(f)
except FileNotFoundError:
    print(f"ERRORE CRITICO: Non trovo il file {CONFIG_PATH}")
    print("Verifica che il volume nel docker-compose sia: - ./sensors/config:/app/config")
    exit(1)

# Parametri MQTT e Simulazione
BROKER = config['mqtt']['broker']
PORT = config['mqtt']['port']
CLIENT_ID = config['mqtt']['client_id']
INTERVAL = config['simulation']['interval_seconds']

# 2. Generazione Procedurale della Topologia
# Qui trasformiamo la configurazione "compatta" in una lista reale di sensori attivi.
active_sensors = []

topo = config['topology']
# Prendiamo il template standard per i motori
motor_template = config['templates']['standard_motor']

print(f"Generazione Topologia: {topo['sectors']['count']} Settori, {topo['lines_per_sector']['count']} Linee/Settore, {topo['assets_per_line']['count']} Motori/Linea")

# Ciclo SETTORI (Level 1)
for s in range(1, topo['sectors']['count'] + 1):
    sector_id = f"{topo['sectors']['prefix']}_{s}"
    
    # Ciclo LINEE (Level 2)
    for l in range(1, topo['lines_per_sector']['count'] + 1):
        line_id = f"{topo['lines_per_sector']['prefix']}_{l}"
        
        # Ciclo MOTORI/ASSET (Level 3)
        for a in range(1, topo['assets_per_line']['count'] + 1):
            asset_id = f"{topo['assets_per_line']['prefix']}_{a}"
            
            # Per ogni motore, applichiamo il template dei sensori
            for template_sensor in motor_template:
                # Creiamo una copia per non modificare il dizionario originale
                sensor_conf = template_sensor.copy()
                
                # --- LOGICA DI VARIANZA ---
                # Per rendere realistico il sistema, ogni motore ha un punto di lavoro leggermente diverso.
                # Calcoliamo il 'base_val' specifico per QUESTO sensore di QUESTO motore.
                avg = sensor_conf.get('base_val_avg', 0)
                variance = sensor_conf.get('base_val_variance', 0)
                
                # Valore base unico = Media +/- valore random entro la varianza
                unique_base_val = avg + random.uniform(-variance, variance)
                sensor_conf['base_val'] = unique_base_val
                
                # Creiamo l'oggetto fisico (Factory)
                sensor_obj = create_sensor(sensor_conf)
                
                # --- COSTRUZIONE TOPIC MQTT ---
                # Struttura richiesta: sector_X/line_Y/engine_Z/type
                topic = f"{sector_id}/{line_id}/{asset_id}/{sensor_conf['type']}"
                
                # Salviamo nella lista dei sensori attivi
                active_sensors.append({
                    "obj": sensor_obj,
                    "topic": topic
                })

print(f"Inizializzazione completata: {len(active_sensors)} sensori pronti.")

# 3. Setup MQTT
client = mqtt.Client(client_id=CLIENT_ID)

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connesso al Broker MQTT Mosquitto!")
    else:
        print(f"Errore connessione MQTT: codice {rc}")

client.on_connect = on_connect

# Loop di connessione resiliente (attende che Mosquitto sia pronto)
while True:
    try:
        print(f"Tentativo connessione a {BROKER}:{PORT}...")
        client.connect(BROKER, PORT, 60)
        break
    except Exception as e:
        print(f"Broker non disponibile ({e}), riprovo tra 5 secondi...")
        time.sleep(5)

client.loop_start()

# 4. Loop Principale di Simulazione
try:
    normal_state_prob = config['simulation'].get('normal_state_probability', 0.85)
    warning_state_prob = config['simulation'].get('warning_state_probability', 0.95)
    while True:
        start_time = time.time()
        
        # Iteriamo su tutti i sensori generati
        for item in active_sensors:
            sensor = item['obj']
            topic = item['topic']
            
            # A. Generazione dato fisico
            valore = sensor.simulate(normal_state_prob, warning_state_prob)
            
            # B. Creazione Payload JSON come da specifiche 
            payload = {
                "value": valore,
                "unit": sensor.unit,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": {
                    "warning_threshold": sensor.warning_threshold,
                    "critical_threshold": sensor.critical_threshold
                }
            }
            
            # C. Pubblicazione
            client.publish(topic, json.dumps(payload))
            
            # (Opzionale) Log per debug - commentare se troppi sensori
            # print(f"PUB [{topic}]: {payload}")
            
        # Calcolo tempo impiegato per non driftare troppo con sleep
        elapsed = time.time() - start_time
        sleep_time = max(0, INTERVAL - elapsed)
        
        print(f"Ciclo completato. Inviati {len(active_sensors)} messaggi. Sleep per {sleep_time:.2f}s")
        time.sleep(sleep_time)

except KeyboardInterrupt:
    print("\nSimulatore arrestato manualmente.")
    client.loop_stop()
    client.disconnect()