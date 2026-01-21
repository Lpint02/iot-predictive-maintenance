import json
import time
import random
import paho.mqtt.client as mqtt
from datetime import datetime
from sensor_factory import create_sensor
from prediction_engine import PredictionEngine

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

PREDICTION_ID = "sector_1/line_1/engine_1"
prediction_engine = PredictionEngine(PREDICTION_ID)


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
            
            full_id = f"{sector_id}/{line_id}/{asset_id}"
            is_prediction_engine = (full_id == PREDICTION_ID)

            # Per ogni motore, applichiamo il template dei sensori
            for template_sensor in motor_template:
                sensor_type = template_sensor['type']
                topic = f"{full_id}/{sensor_type}"

                sensor_entry = {
                    "topic": topic,
                    "type": sensor_type,
                    "unit": template_sensor['unit'],
                    "limits": {
                        "warning_threshold": template_sensor['thresholds']['warning'],
                        "critical_threshold": template_sensor['thresholds']['critical']
                    }
                }

                if is_prediction_engine:
                    sensor_entry['obj'] = prediction_engine
                    sensor_entry['mode'] = 'prediction_engine'
                else:

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

                    sensor_entry['obj'] = create_sensor(sensor_conf)
                    sensor_entry['mode'] = 'standard'
                
                # Salviamo nella lista dei sensori attivi
                active_sensors.append(sensor_entry)

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
        loop_timestamp = datetime.utcnow().isoformat()

        prediction_engine.step()  # Aggiorna il motore di predizione
        
        # Iteriamo su tutti i sensori generati
        for item in active_sensors:
            sensor = item['obj']
            topic = item['topic']

            if item['mode'] == 'prediction_engine':
                # Usare il motore di predizione per generare il dato
                valore = sensor.get_value(item['type'])

            else:
            
                # A. Generazione dato fisico
                valore = sensor.simulate(normal_state_prob, warning_state_prob)
            
            # B. Creazione Payload JSON come da specifiche 
            payload = {
                "value": valore,
                "unit": item['unit'],
                "timestamp": loop_timestamp,
                "metadata": {
                    "warning_threshold": item['limits']['warning_threshold'],
                    "critical_threshold": item['limits']['critical_threshold']
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