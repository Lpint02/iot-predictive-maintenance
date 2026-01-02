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

    def _generate_state_based_value(self):
        """
        Generate a valkuie based on a probability of fault
        """
        dice = random.random()

        if dice < 0.85:
            # Normal operation
            noise = np.random.normal(0, (self.warning_threshold - self.base_val) * 0.1)
            val = self.base_val + noise
            return min(val, self.warning_threshold - 0.1)
        elif dice < 0.95:
            # Warning state
            return random.uniform(self.warning_threshold, self.critical_threshold)

        else:
            # Critical state
            return random.uniform(self.critical_threshold, self.max)

    def simulate(self):
        return round(self._genertate_state_based_value(), 2)


class VibrationSensor(GenericSensor):
    """
    Simulate Accelerometer sensor data
    """
    def simulate(self):
        val = self._generate_state_based_value()
        return round(max(0.0, val), 2)

class TemperatureSensor(GenericSensor):
    """
    Simulate Temperature sensor data
    """
    def simulate(self):
        val = self._generate_state_based_value()
        return round(max(0.0, val), 2)


class CurrentSensor(GenericSensor):
    """
    Simulate Current sensor data
    """
    def simulate(self):
        val = self._generate_state_based_value()
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