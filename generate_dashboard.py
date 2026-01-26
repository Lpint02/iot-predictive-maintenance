import json
import os

# --- CONFIGURAZIONE ---
CONFIG_PATH = 'sensors/config/sensor_config.json'
# Assicurati che il tuo template sia qui!
TEMPLATE_PATH = 'templates/iot-maintenance-template.json' 
OUTPUT_PATH = 'dashboards/iot-maintenance-generated.json'

G_TO_MMS_FACTOR = 31.22

def load_json(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"ERRORE: Non trovo il file: {path}")
        exit(1)

def save_json(data, path):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    print(f"\n✅ Dashboard salvata in: {path}")

def get_thresholds(config):
    # Estrae le soglie dal file di configurazione
    templates = config['templates']['standard_motor']
    thresholds = {}
    
    print("\n--- 1. LETTURA CONFIGURAZIONE ---")
    for t in templates:
        s_type = t['type']
        warn = t['thresholds']['warning']
        crit = t['thresholds']['critical']
        
        # Conversione per vibrazioni
        if s_type == 'vibration':
            warn = round(warn * G_TO_MMS_FACTOR, 1)
            crit = round(crit * G_TO_MMS_FACTOR, 1)
            
        thresholds[s_type] = {'warn': warn, 'crit': crit}
        print(f"   Sensore [{s_type}]: Giallo > {warn}, Rosso > {crit}")
    return thresholds

def process_panel(panel, thresholds):
    # Questa funzione aggiorna un singolo pannello
    title = panel.get('title', 'No Title').lower()
    p_type = panel.get('type', 'unknown')  # Leggiamo anche il tipo
    # Cerca corrispondenze
    s_type = None
    if 'vibration' in title and p_type == 'gauge': 
        s_type = 'vibration'
    elif 'temperature' in title and p_type == 'gauge': 
        s_type = 'temperature'
    elif 'current' in title and p_type == 'gauge': 
        s_type = 'current'
    
    if s_type and s_type in thresholds:
        t = thresholds[s_type]
        print(f"Trovato GAUGE '{panel.get('title')}': Applico soglie {s_type.upper()}")
        
        # Aggiorna Colori
        steps = [
            {"color": "green", "value": None},
            {"color": "#EAB839", "value": t['warn']},
            {"color": "red", "value": t['crit']}
        ]
        
        # Gestione sicurezza per path diversi dentro il JSON di Grafana
        if 'fieldConfig' not in panel: panel['fieldConfig'] = {}
        if 'defaults' not in panel['fieldConfig']: panel['fieldConfig']['defaults'] = {}
        if 'thresholds' not in panel['fieldConfig']['defaults']: panel['fieldConfig']['defaults']['thresholds'] = {}
        
        panel['fieldConfig']['defaults']['thresholds']['steps'] = steps
        
        # Aggiorna Max Value (estetico)
        if panel['type'] in ['gauge', 'bargauge']:
             panel['fieldConfig']['defaults']['max'] = int(t['crit'] * 1.25)
             
        return True # Modifica effettuata
    else:
        # Debug per capire cosa sta ignorando
        # print(f"   Ignorato pannello: '{panel.get('title')}'")
        return False

def scan_dashboard_recursive(panels, thresholds):
    # Funzione ricorsiva che cerca pannelli ovunque (anche dentro le righe)
    count = 0
    for panel in panels:
        # Se è una RIGA, entra dentro (ricorsione)
        if panel['type'] == 'row':
            if 'panels' in panel and len(panel['panels']) > 0:
                count += scan_dashboard_recursive(panel['panels'], thresholds)
        
        # Altrimenti processa il pannello
        else:
            if process_panel(panel, thresholds):
                count += 1
    return count

if __name__ == '__main__':
    print("--- START SCRIPT ---")
    
    conf = load_json(CONFIG_PATH)
    dash = load_json(TEMPLATE_PATH)
    limits = get_thresholds(conf)
    
    print("\n--- 2. AGGIORNAMENTO DASHBOARD ---")
    # Grafana moderno usa 'panels', Grafana vecchio usava 'rows'. Copriamo tutto.
    total_updates = 0
    
    if 'panels' in dash:
        total_updates += scan_dashboard_recursive(dash['panels'], limits)
    elif 'rows' in dash:
        # Vecchia struttura Grafana
        for row in dash['rows']:
            if 'panels' in row:
                total_updates += scan_dashboard_recursive(row['panels'], limits)
                
    print(f"\n📊 Totale pannelli aggiornati: {total_updates}")
    
    if total_updates == 0:
        print("ATTENZIONE: Non ho aggiornato nessun pannello. Controlla i titoli nel Template!")
    
    save_json(dash, OUTPUT_PATH)