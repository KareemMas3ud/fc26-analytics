# ⚽ FC 26 Live Match Analytics (Lambda Architecture)

![Project Status](https://img.shields.io/badge/Status-Completed-success)
![Tech Stack](https://img.shields.io/badge/Tech-Kafka%20%7C%20Spark%20%7C%20Cassandra%20%7C%20ClickHouse%20%7C%20Streamlit-blue)

## 📌 Project Overview
An advanced, ultra-low latency Big Data pipeline that ingests, processes, and visualizes live E-Sports match telemetry (simulating FC 26). Built using a robust Lambda Architecture, this system handles high-velocity continuous data streams (passes, shots, X/Y coordinates) and performs complex stateful aggregations on the fly to deliver sub-millisecond real-time insights.

## 🏗️ Architecture & Tech Stack
This pipeline consists of five distributed stages running natively on Docker:
1. **Data Source (Python):** A state-machine simulator generating realistic 11v11 match events and X/Y spatial telemetry.
2. **Real-Time Ingestion (Apache Kafka):** Fault-tolerant distributed message broker buffering the JSON payloads.
3. **Stream Processing (PySpark):** Consumes the live stream, tracking continuous stateful metrics (e.g., dynamic ball possession) using sliding windows.
4. **Speed Layer Storage (Apache Cassandra):** High-speed NoSQL database optimized for continuous telemetry upserts.
5. **Batch Layer & Analytics (ClickHouse & Streamlit):** ClickHouse serves as the columnar OLAP database storing historical Wyscout baselines, while Streamlit polls the speed layer to render dynamic 2D pitch maps and FotMob-style KPIs.

## 🚀 How to Run the Project locally

### Prerequisites
- Docker Desktop installed and running.
- Python 3.9+ environment.

### Step 1: Start the Infrastructure
Spin up the Kafka, Zookeeper, Spark, ClickHouse, and Cassandra containers:
> docker-compose up -d

### Step 2: Start the Processing Pipeline
Restart the Spark container to begin listening to the Kafka stream:
> docker restart fc26_spark

### Step 3: Launch the Simulator
In a new terminal, activate your virtual environment and start the data generator:
> python simulator.py

### Step 4: Run the Dashboard
In another terminal, launch the Streamlit UI to visualize the live data:
> python -m streamlit run app.py

## 👥 Credits & Acknowledgements

- **Academy:** NTI — Huawei Egyptian Talents Academy
- **Track:** Huawei Big Data Associate (HCIP-Big Data Developer V2.0)
- **Instructor:** Eng. Ahmed Saeed Farg

**Development Team:**
- **Kareem Mas3ud** (Team Leader)
- **Omar Hisham** (Team Member)
- **Mohamed Gamal** (Team Member)
