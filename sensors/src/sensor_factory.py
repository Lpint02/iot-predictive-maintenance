import numpy as np

class GenericSensor:
    def __init__(self, config):
        self.type = config["type"]
        self.unit = config["unit"]
        self.min = config["min"]
        self.max = config["max"]
        self.current_val = config.get('base_val', (self.min + self.max)/2)

    def simulate(self):
        return self.current_val


class VibrationSensor(GenericSensor):
    """
    Simulate Accelerometer sensor data
    """
    def simulate(self):
        # Rumore di fondo (vibrazione normale)
        noise = np.random.normal(0, 0.1)
        
        # Occasionali picchi transitori (colpi meccanici)
        spike = np.random.choice([0, 0.8], p=[0.98, 0.02])
        
        reading = self.current_val + noise + spike
        # La vibrazione fisica (magnitudo) non può essere negativa
        return round(max(0.0, reading), 3)

class TemperatureSensor(GenericSensor):
    """
    Simulate Temperature sensor data
    """
    def simulate(self):
        # Drift lento (inerzia)
        drift = np.random.normal(0, 0.15)
        self.current_val += drift
        
        # Logica elastica: se si allontana troppo dal range operativo, tende a tornare indietro
        # Questo simula il termostato o l'equilibrio termico naturale
        if self.current_val < self.min: self.current_val += 0.2
        if self.current_val > self.max: self.current_val -= 0.2
        
        return round(self.current_val, 1)


class CurrentSensor(GenericSensor):
    """
    Simulate Current sensor data
    """
    def simulate(self):
        # Fluttuazione elettrica
        electrical_noise = np.random.normal(0, 0.2)
        reading = self.current_val + electrical_noise
        return round(max(0.0, reading), 2)

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