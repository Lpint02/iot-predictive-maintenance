# 🏭 IoT Predictive Maintenance System (Phase 1)

[![Docker](https://img.shields.io/badge/Docker-24.0+-blue?logo=docker&logoColor=white)](https://www.docker.com/)
[![Node-RED](https://img.shields.io/badge/Node--RED-3.1+-red?logo=node-red&logoColor=white)](https://nodered.org/)
[![InfluxDB](https://img.shields.io/badge/InfluxDB-2.7-purple?logo=influxdb&logoColor=white)](https://www.influxdata.com/)
[![MQTT](https://img.shields.io/badge/MQTT-Mosquitto-green?logo=mqtt&logoColor=white)](https://mosquitto.org/)

---

## 📌 Project Overview

The IoT Predictive Maintenance System is an end-to-end **Industrial Internet of Things (IIoT)** framework designed for **real-time monitoring** and **anomaly detection** in manufacturing environments.

The project establishes a robust and scalable data pipeline that bridges the gap between physical industrial assets and data-driven insights. By leveraging **Digital Twin** technology, 
the system replicates the behavior of factory components such as motors and production lines. This allows engineers to monitor critical telemetry—including vibration (ISO 10816), temperature, 
and electrical consumption—in real-time.

This infrastructure provides the essential foundation for transitioning from traditional reactive maintenance to proactive, predictive strategies, 
ultimately reducing unplanned downtime and optimizing the overall asset lifecycle through advanced data visualization and automated alerting.

---

## 🏛️ System Architecture
The system follows a modular, layered approach to ensure industrial-grade reliability, decoupling simulation from data processing and visualization.


### Data Pipeline Flow
1.  **Simulation Layer**: **Python-based Digital Twin** scripts generating realistic telemetry for vibrations, temperature, and current consumption based on industrial physical models.
2.  **Transport Layer**: An **Eclipse Mosquitto MQTT broker** handling traffic through a strict topic hierarchy: `sector_X/line_X/asset_X/sensor`.
3.  **Intelligence Layer**: **Node-RED** acts as the central orchestrator, validating data via Regex, processing alarm thresholds, and routing packets.
4.  **Storage**: **InfluxDB** 2.7 stores time-series data, optimized for high-frequency industrial metrics.
5.  **Monitoring**: Telegraf monitors hardware performance (CPU/RAM) to ensure container stack stability.
6.  **HMI (Human-Machine Interface)**: **Grafana** provides interactive dashboards with dynamic variables to filter data by sector, production line, or specific motor.

---

## 🔧 Configuration & Structure

### MQTT Topic Hierarchy
The system enforces a rigorous topic structure for seamless integration and scalability:
Example: `sector_1/line_1/engine_3/temperature`

## Centralized Parameters `sensor_config.json`
The project utilizes a **"Single Source of Truth"** principle for all hardware and simulation parameters.
| Parameter | Description |
| :---: | :---: |
| `topology` | Defines the physical hierarchy (sectors, lines, motors). |
| `templates` | Sets Warning/Critical thresholds (e.g., ISO 10816) and base values. |
| `simulation` | Manages transmission intervals and failure probabilities. |

### Struttura Repository
```text
├── sensors/            # Python Simulator and Digital Twin logic
|   ├── config/         # sensor_config.json (Centralized parameters)
|   ├── src/            # Simulator source code and Sensor Factory
├── nodered/            # Ingestion flows, validation, and alerting
├── telegraf/           # Hardware performance monitoring config
├── docker-compose.yml  # Full stack orchestration via Docker
└── .env.template       # Environment variables template (Tokens & IDs)
```

---

## 🚀 Installation & Setup

### Prerequisites
- Docker & Docker Compose installed.
- A Telegram Bot (via @BotFather) for real-time notifications.

## Getting Started
- **Clone the repository**
```bash
git clone https://github.com/your-username/iot-predictive-maintenance.git
cd iot-predictive-maintenance
```
- **Configure Environment:**
Copy the template and fill in your InfluxDB tokens and Telegram credentials.
```bash
cp .env.template .env
```
- **Clone the repository**
```bash
docker-compose up -d
```
### Accessing Interfaces
- **Grafana Dashboards:** `http://localhost:3000` (Default: admin/admin)
- **Node-RED Flows:** `http://localhost:1880`
- **InfluxDB UI:** `http://localhost:8086`
  
---

## 🛠️ Troubleshooting
- **MQTT Connection Refused:** The simulator waits for Mosquitto to be ready. If errors persist, verify the `iot-mosquitto` container status with `docker ps`.
- **Data missing in Grafana:** Check Node-RED logs for authentication errors. Ensure the `INFLUX_TOKEN` in `.env` matches your InfluxDB setup exactly.
- **Telegram Alerts not received:** Verify the Bot API Key and ensure you have started a conversation with the bot to obtain the correct `CHAT_ID`.
  
---
## 📈 Future Developments
-  ML Integration: Deploy machine learnig models for RUL (Remaining Useful Life) prediction, enabling a predictive maintenance instead of a simple monitoring system
---

## 👥 Authors
- @flebo45
- @Lpint02
- @mattpaol441
---









