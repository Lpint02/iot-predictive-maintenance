import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

"""
This script simulates the run-to-failure lifecycle of industrial electric motors,
generating sensor data for vibration, temperature, and current absorption.
The generated dataset includes Remaining Useful Life (RUL) as the target variable.
It also visualizes the sensor data for a randomly selected motor, highlighting
severity zones based on relevant standards.

The simulated data adheres to ISO 10816 for vibration, IEC 60034-1 for temperature, and IEC 60034-30 for current absorption.

This normative reflect a typical industrial electric motor:
- Class 2 (Flexible Montage)
- Insulation Class F
- Triphase 400V, 55kW

@param motor_id: Unique identifier for the motor
@return: DataFrame containing the simulated lifecycle data for the motor
"""
def generate_motor_lifecycle(motor_id):
    # Generate a random initial life span between 800 and 2000 cycles
    initial_life = np.random.randint(800, 2000)
    time_cycles = np.arange(initial_life)
    
    # Degradation curve
    exponent = np.random.uniform(4.0, 6.0)
    fault_progression = (time_cycles / initial_life) ** exponent

    # -- SIMULATION SENSORS (ISO 10816 & F Class) --

    # VIBRATION (ISO 10816) - Speed RMS (mm/s)
    # ISO Threshold Group 2
    # < 2.3 mm/s - Good, 2.3 to 4.5 mm/s - Acceptable, 4.5 to 7.1 mm/s - Unsatisfactory, > 7.1 mm/s - Unacceptable
    vib_base = np.random.uniform(0.5, 1.5)
    vib_failure = np.random.uniform(8.0, 10.0)

    # Generation with noise
    vib_noise = np.random.normal(0, 0.15, initial_life)
    vib_actual = vib_base + ((vib_failure - vib_base) * fault_progression) + vib_noise
    vib_actual = np.maximum(vib_actual, 0)

    # TEMPERATURE (F Class)
    #  IEC 60034-1 
    # < 105°C - Good, 105 to 130°C - Acceptable, 130 to 150°C - Unsatisfactory, > 150°C - Unacceptable

    temp_base = np.random.uniform(85.0, 95.0)
    temp_failure = np.random.uniform(152.0, 160.0)

    temp_noise = np.random.normal(0, 1.0, initial_life)
    temp_actual = temp_base + ((temp_failure - temp_base) * fault_progression) + temp_noise

    # CURRENT ABSORPTION (A)
    #IEC 60034-30 / Efficiency IE
    # < 95 A - Good, 95 to 105 A - Acceptable, 105 to 110 A - Unsatisfactory, > 110 A - Unacceptable
    curr_base = np.random.uniform(88.0, 92.0)
    curr_failure = np.random.uniform(112.0, 120.0)

    curr_noise = np.random.normal(0, 0.8, initial_life)
    curr_actual = curr_base + ((curr_failure - curr_base) * fault_progression) + curr_noise

    # -- RUL (Target) --
    rul = initial_life - time_cycles

    df = pd.DataFrame({
        'motor_id': motor_id,
        'cycle': time_cycles,
        'vibration': vib_actual,
        'temperature': temp_actual,
        'current': curr_actual,
        'RUL': rul
    })

    df = df.round({
        'vibration': 2,
        'temperature': 1,
        'current': 2,
        'RUL': 0
    })

    return df

if __name__ == "__main__":
    # Datatset generation
    num_motors = 500
    dataset_list = []

    for i in range(1, num_motors + 1):
        dataset_list.append(generate_motor_lifecycle(i))
    
    final_df = pd.concat(dataset_list, ignore_index=True)
    print(f"Generated dataset with {len(final_df)} total rows.")

    # Visualization
    sample_motor_id = np.random.randint(1, num_motors + 1)
    sample = final_df[final_df['motor_id'] == sample_motor_id]

    fig, axs = plt.subplots(3, 1, figsize=(12, 15), sharex=True)
    plt.suptitle(f'Simulazione Motore 55kW - ID: {sample_motor_id} (Run-to-Failure)', fontsize=16)

    # --- PLOT VIBRATION ---
    axs[0].plot(sample['cycle'], sample['vibration'], color='black', linewidth=1.5, label='Vibrazione (mm/s)')
    # Zone ISO 10816 Group 2 Flexible
    axs[0].axhspan(0, 2.3, facecolor='green', alpha=0.2, label='Good (< 2.3)')
    axs[0].axhspan(2.3, 4.5, facecolor='yellow', alpha=0.2, label='Acceptable (2.3 - 4.5)')
    axs[0].axhspan(4.5, 7.1, facecolor='orange', alpha=0.2, label='Unsatisfactory (4.5 - 7.1)')
    axs[0].axhspan(7.1, 12, facecolor='red', alpha=0.2, label='Unacceptable (> 7.1)')
    axs[0].set_ylabel('Vibrazione RMS (mm/s)')
    axs[0].set_title('ISO 10816 - Vibration Severity')
    axs[0].legend(loc='upper left')
    axs[0].grid(True, alpha=0.3)

    # --- PLOT TEMPERATURE ---
    axs[1].plot(sample['cycle'], sample['temperature'], color='darkblue', linewidth=1.5, label='Temp (°C)')
    # Zone IEC 60034-1 Class F
    axs[1].axhspan(0, 105, facecolor='green', alpha=0.2, label='Good (< 105)')
    axs[1].axhspan(105, 130, facecolor='yellow', alpha=0.2, label='Acceptable (105 - 130)')
    axs[1].axhspan(130, 150, facecolor='orange', alpha=0.2, label='Unsatisfactory (130 - 150)')
    axs[1].axhspan(150, 170, facecolor='red', alpha=0.2, label='Unacceptable (> 150)')
    axs[1].set_ylabel('Temperatura (°C)')
    axs[1].set_title('IEC 60034-1 - Temperature Class F')
    axs[1].legend(loc='upper left')
    axs[1].grid(True, alpha=0.3)

    # --- PLOT CURRENT ---
    axs[2].plot(sample['cycle'], sample['current'], color='purple', linewidth=1.5, label='Corrente (A)')
    # Zone IEC 60034-30 (55kW limits custom)
    axs[2].axhspan(0, 95, facecolor='green', alpha=0.2, label='Good (< 95)')
    axs[2].axhspan(95, 105, facecolor='yellow', alpha=0.2, label='Acceptable (95 - 105)')
    axs[2].axhspan(105, 110, facecolor='orange', alpha=0.2, label='Unsatisfactory (105 - 110)')
    axs[2].axhspan(110, 130, facecolor='red', alpha=0.2, label='Unacceptable (> 110)')
    axs[2].set_ylabel('Corrente (A)')
    axs[2].set_xlabel('Cicli di Vita (Tempo)')
    axs[2].set_title('Current Absorption (55kW Motor)')
    axs[2].legend(loc='upper left')
    axs[2].grid(True, alpha=0.3)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])

    filename_img = 'grafico_motore_sample.png'
    plt.savefig(filename_img)
    print(f"Grafico salvato come '{filename_img}'. Controlla la cartella del progetto!")

    filename_csv = 'dataset_motors_500.csv'
    final_df.to_csv(filename_csv, index=False)
    print(f"Dataset salvato come '{filename_csv}'.")