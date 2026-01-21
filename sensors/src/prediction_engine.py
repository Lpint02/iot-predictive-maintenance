import numpy as np
import random

class PredictionEngine:
    def __init__(self, motor_id):
        self.motor_id = motor_id
        self.current_values = {}
        self.reset_lifecycle()

    
    def reset_lifecycle(self):
        """ 
        Start New Lifecycle Simulation 
        """
        # Radom total life between 800 and 2000 cycles
        self.total_life = np.random.randint(800, 2000)
        self.current_tick = 0
        
        # Degradation exponent
        self.exponent = np.random.uniform(4.0, 6.0)
        
        # Base and failure values for sensors
        self.vib_base = np.random.uniform(0.5, 1.5)
        self.vib_failure = np.random.uniform(8.0, 10.0)

        self.temp_base = np.random.uniform(85.0, 95.0)
        self.temp_failure = np.random.uniform(152.0, 160.0)

        self.curr_base = np.random.uniform(88.0, 92.0)
        self.curr_failure = np.random.uniform(112.0, 120.0)

        self.step()  # Initial step to set starting values
        
        print(f"[{self.motor_id}] New lifecycle started: will last {self.total_life} cycles. Degradation exponent: {self.exponent:.2f}")

    def step(self):
        """
        Simulate one time cycle
        Return a dictionary with the 3 sensors values
        """

        # Once lifecycle is over, reset
        if self.current_tick >= self.total_life:
            self.reset_lifecycle()
        
        # Calculate fault progression
        fault_progression = (self.current_tick / self.total_life) ** self.exponent

        # Vibration ISO 10816
        # Convert in g cause other motors have acceleration in g
        vib_noise = np.random.normal(0, 0.15)
        vibration = self.vib_base + ((self.vib_failure - self.vib_base) * fault_progression) + vib_noise
        vibration = np.maximum(vibration, 0)

        # Conversion from mm/s^2 to g (assuming 50Hz frequency)
        omega = 2 * np.pi * 50
        vibration_g = (vibration * omega) / 9806.65

        # Temperature
        temp_noise = np.random.normal(0, 1.0)
        temperature = self.temp_base + ((self.temp_failure - self.temp_base) * fault_progression) + temp_noise

        # Current
        curr_noise = np.random.normal(0, 0.8)
        current = self.curr_base + ((self.curr_failure - self.curr_base) * fault_progression) + curr_noise

        self.current_values = {
            "motor_id": self.motor_id,
            "vibration": round(vibration_g, 2),
            "temperature": round(temperature, 2),
            "current": round(current, 2)
        }

        # Increment tick
        self.current_tick += 1
    
    def get_value(self, sensor_type):
        return self.current_values.get(sensor_type, 0.0)
