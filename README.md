# Edge Computing-based IoT System

This repository contains the complete implementation, datasets, deployment code,
and report for an **IoT system based on Edge Computing**.
The project focuses on processing data locally at the network edge using
resource-constrained devices instead of relying on cloud computing.

---

## Project Overview

This project applies **Edge Computing** to an IoT system where sensing,
data processing, and decision-making are performed directly on edge devices.

Key characteristics:
- Edge-level processing on **Raspberry Pi 4**
- Distributed IoT nodes using **ESP32** and **ESP8266**
- Camera-based data acquisition and local inference
- Real-time alert and communication between edge nodes

---

##  Edge Computing Architecture

- **Edge Device**: Raspberry Pi 4  
  - Runs Python-based server and local inference
  - Processes image data at the edge
- **IoT Nodes**:
  - ESP32: camera/sensing node
  - ESP8266: alert/notification node
- **Communication**:
  - HTTP and/or MQTT between nodes and edge device

This architecture reduces latency, bandwidth usage, and cloud dependency.

---

## Tools & Technologies

### Hardware
- Raspberry Pi 4
- ESP32
- ESP8266
- Camera module

### Software & Languages
- **Python**: edge processing, server, inference
- **C**: firmware for ESP32 and ESP8266
- **PlatformIO**: embedded firmware development
- **TensorFlow Lite**: lightweight inference on edge devices

---

## Repository Structure

```text
edge-computing-iot-system/
│
├── app/                       # Application-level code
│
├── data/
│   ├── images/                # Image data
│   └── labels/                # Ground truth labels
│
├── deployment/
│   ├── Alert_node/            # ESP8266 alert node (PlatformIO)
│   ├── CameraNode/            # ESP32 camera node (PlatformIO)
│   ├── Pi4_code/              # Raspberry Pi 4 edge-side code
│   └── requirement.txt        # Python dependencies for Pi 4
│
├── src/                       # Core logic / utilities
│
├── results/                   # Experimental results
│
├── report/
│   └── ELT3244_IoT_va_Ung_dung_Nhom_6.pdf
│
└── README.md
