import numpy as np
import random

class GenericSensor:
    def __init__(self, config):
        self.type = config["type"]
        self.unit = config["unit"]

        self.min = config["min"]
        self.max = config["max"]

        self.base_val = config.get("base_val", self.min)

        thresholds = config.get("thresholds", {})
        self.warning_threshold = thresholds.get("warning", None)
        self.critical_threshold = thresholds.get("critical", None)

    def _generate_state_based_value(self, normal_state_prob, warning_state_prob):
        """
        Generate a value based on a probability of fault
        """
        dice = random.random()

        if dice < normal_state_prob:
            # Normal operation
            noise = np.random.normal(0, (self.warning_threshold - self.base_val) * 0.1)
            val = self.base_val + noise
            return min(val, self.warning_threshold - 0.1)
        elif dice < warning_state_prob:
            # Warning state
            return random.uniform(self.warning_threshold, self.critical_threshold)

        else:
            # Critical state
            return random.uniform(self.critical_threshold, self.max)

    def simulate(self, normal_state_prob, warning_state_prob):
        return round(self._generate_state_based_value(normal_state_prob, warning_state_prob), 2)


class VibrationSensor(GenericSensor):
    """
    Simulatore Accelerometro Fisico (Digital Twin).
    Invece di estrarre un numero casuale, questo sensore:
    1. Legge il target (g) dai range configurati nel config (rispetto ISO 10816).
    2. Genera un'onda sinusoidale a 50Hz (velocità motore) con quell'energia.
    3. Calcola matematicamente l'RMS (Root Mean Square) del segnale grezzo.
    
    Risultato con stessi valori del JSON, ma giustificati da calcoli di Edge Computing.
    """
    
    def _physics_engine_g_rms(self, target_peak_g):
        """
        Motore Fisico:
        Genera un segnale grezzo (accelerazione nel tempo) e ne calcola l'RMS.
        """
        # Parametri di campionamento (simuliamo un ADC reale)
        sampling_rate = 1000 # Hz
        duration = 1.0       # secondi
        
        # 1. Generazione dell'asse temporale: crea un array temporale di 1 secondo campionato a 1000 Hz (1000 punti). Un vero sensore digitale (ADC) lavora così, acquisendo campioni nel tempo
        t = np.linspace(0, duration, int(sampling_rate * duration), endpoint=False)
        
        # 2. Generazione dell'Onda Fisica (Componente Fondamentale)
        # 50Hz è la frequenza standard di rete/rotazione (3000 RPM), la velocità standard di un motore asincrono industriale a 2 poli. 
        # Stiamo simulando la rotazione fisica dell'albero motore.
        freq_hz = 50.0 
        signal = target_peak_g * np.sin(2 * np.pi * freq_hz * t)
        
        # 3. Aggiunta Rumore (Realismo)
        # Un sensore reale ha sempre rumore elettronico/meccanico di fondo, ci sono interferenze elettromagnetiche e vibrazioni meccaniche di fondo. 
        # Senza rumore, la simulazione sarebbe "finta" e troppo perfetta.
        noise = np.random.normal(0, 0.05 * target_peak_g, len(t))
        raw_signal_g = signal + noise
        
        # 4. Calcolo RMS (Edge Computing) tramite formula matematica 
        # È l'operazione matematica che trasforma l'onda nel numero "g" che vediamo su Grafana. 
        # Questo è il vero valore aggiunto: non stiamo tirando a indovinare il valore RMS. Lo stiamo calcolando matematicamente partendo dall'onda grezza.
        rms_g = np.sqrt(np.mean(raw_signal_g**2))
        
        return rms_g

    def simulate(self, normal_state_prob, warning_state_prob):
        """
        Override del metodo simulate.
        Mantiene la logica probabilistica dei colleghi, ma usa il motore fisico.
        """
        dice = random.random()
        
        # DECISIONE DELLO STATO: Il codice legge il file JSON di configurazione. Il file dice che in stato Warning, il valore deve essere tra 0.14g e 0.23g. 
        # Scelta del Target (Statistica): Il codice usa la logica originale (random.uniform) per scegliere un obiettivo, ad esempio 0.18 g.
        # Qui determiniamo in che range deve cadere il valore in base alle probabilità
        if dice < normal_state_prob:
            # Stato NORMALE
            # Usiamo base_val (es. 0.10g) con piccola fluttuazione
            target_rms = self.base_val + random.uniform(-0.01, 0.01)
            
        elif dice < warning_state_prob:
            # Stato WARNING
            # Peschiamo un target ESATTAMENTE tra le soglie del JSON (es. 0.14 - 0.23)
            target_rms = random.uniform(self.warning_threshold, self.critical_threshold)
            
        else:
            # Stato CRITICAL
            # Peschiamo un target sopra la soglia critica del JSON
            target_rms = random.uniform(self.critical_threshold, self.max)

        # SIMULAZIONE FISICA: il simulatore si chiede che tipo di onda fisica deve generare affinché, dopo aver fatto tutti i calcoli complessi, esca proprio 0.18 g. 
        # Dalla fisica sappiamo che per un seno: Picco = RMS * rad(2). Quindi il codice calcola: Picco = obiettivo scelto dalla logica originale * 1.414.
        # Per ottenere un'onda che abbia quell'RMS, dobbiamo calcolare il picco.
        # Formula fisica: RMS = Picco / sqrt(2). Picco = RMS * sqrt(2)
        required_peak_g = target_rms * np.sqrt(2)
        
        # Generiamo l'onda con quel picco e otteniamo il valore calcolato. Il numero che esce è dentro i range decisi che rispettano le normative, ma è stato generato attraverso un processo fisico completo.
        final_val = self._physics_engine_g_rms(required_peak_g)
        
        # Restituiamo il valore arrotondato, garantendo che non sia negativo
        return round(max(0.0, final_val), 2)

class TemperatureSensor(GenericSensor):
    """
    Simulate Temperature sensor data
    """
    def simulate(self, normal_state_prob, warning_state_prob):
        val = self._generate_state_based_value(normal_state_prob, warning_state_prob)
        return round(max(0.0, val), 2)


class CurrentSensor(GenericSensor):
    """
    Simulate Current sensor data
    """
    def simulate(self, normal_state_prob, warning_state_prob):
        val = self._generate_state_based_value(normal_state_prob, warning_state_prob)
        return round(max(0.0, val), 2)

def create_sensor(sensor_config):
    sensor_type = sensor_config["type"]
    if sensor_type == "vibration":
        return VibrationSensor(sensor_config)
    elif sensor_type == "temperature":
        return TemperatureSensor(sensor_config)
    elif sensor_type == "current":
        return CurrentSensor(sensor_config)
    else:
        raise ValueError(f"Unknown sensor type: {sensor_type}")