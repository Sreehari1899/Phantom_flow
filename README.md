# 🌊 PeriFlow — Peristaltic Pump Control System

> A Raspberry Pi 4 powered peristaltic pump controller with real-time flow rate monitoring, volume tracking, and a web-based dashboard accessible from any device on the local network.

![Python](https://img.shields.io/badge/Python-3.x-blue?style=flat-square&logo=python)
![Flask](https://img.shields.io/badge/Flask-2.x-black?style=flat-square&logo=flask)
![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-4-red?style=flat-square&logo=raspberrypi)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Hardware Requirements](#hardware-requirements)
- [Pin Connections](#pin-connections)
- [Software Requirements](#software-requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [API Endpoints](#api-endpoints)
- [Calibration](#calibration)
- [Troubleshooting](#troubleshooting)
- [Future Improvements](#future-improvements)

---

## Overview

PeriFlow is an automated peristaltic pump control system built on the **Raspberry Pi 4**. It replaces a traditional Arduino setup with a fully networked solution featuring a modern web dashboard for real-time monitoring and control.

The system controls pump speed via PWM, measures actual flow rate using a YF-S201 Hall effect flow sensor, and tracks total volume dispensed. The web dashboard is accessible from any phone, tablet, or laptop on the same local network.

```
Browser (Dashboard) ←——→ Flask API (app.py) ←——→ GPIO Pins ←——→ Hardware
```

---

## Features

- ✅ **Real-time flow rate display** — live mL/min reading updated every second
- ✅ **PWM speed control** — adjustable flow rate via slider or numeric input
- ✅ **Forward / Reverse direction** — toggle pump direction from dashboard
- ✅ **Volume tracking** — accumulates total mL dispensed with animated beaker visual
- ✅ **Target volume & auto-stop** — set a target volume and pump stops automatically
- ✅ **ETA display** — estimated time to reach target volume based on current flow rate
- ✅ **Flow rate history chart** — scrolling live chart showing actual vs target
- ✅ **Start / Stop control** — one-click pump control from the dashboard
- ✅ **Reset counter** — reset volume and elapsed time independently
- ✅ **Network accessible** — open from any device on the same WiFi or LAN

---

## Hardware Requirements

| # | Component | Model | Role |
|---|-----------|-------|------|
| 1 | Single-board Computer | Raspberry Pi 4 Model B | Main controller |
| 2 | Motor Driver Module | L293D H-Bridge Module | Drives pump motor |
| 3 | Peristaltic Pump | DC Peristaltic Pump 5–12V | Pumps fluid |
| 4 | Flow Sensor | YF-S201 Hall Effect Sensor | Measures flow rate |
| 5 | Power Supply | QUATPOWER LN-3003 (0–30V, 0–3A) | Powers pump motor |
| 6 | Ethernet/USB Cable | — | Powers and connects Pi |

---

## Pin Connections

### Raspberry Pi → L293D Motor Driver

| Raspberry Pi Pin | GPIO (BCM) | L293D Pin | Function |
|-----------------|-----------|-----------|----------|
| Pin 12 | GPIO 18 (PWM) | EN1 ⚠️ direct wire | PWM speed control |
| Pin 11 | GPIO 17 | IN1 | Direction control 1 |
| Pin 13 | GPIO 27 | IN2 | Direction control 2 |
| Pin 6 | GND | GND | Common ground |

> ⚠️ **Important:** Remove the EN1 jumper cap from the L293D module and connect GPIO 18 directly to the EN1 pin. Without this, the motor runs at full speed always and PWM has no effect.

### Power Supply → L293D

| Power Supply | L293D Terminal | Purpose |
|-------------|---------------|---------|
| RED (+) | VIN | Motor power 11.6V |
| BLACK (−) | GND | Motor ground |

### L293D → Peristaltic Pump

| L293D Terminal | Pump Wire | Purpose |
|---------------|-----------|---------|
| A+ | BLACK wire | Motor (+) positive |
| B− | YELLOW wire | Motor (−) negative |

> ℹ️ Note: On this pump the BLACK wire is the positive terminal. If pump runs in reverse, swap the wires or use the Reverse button on the dashboard.

### Raspberry Pi → YF-S201 Flow Sensor

| Raspberry Pi Pin | GPIO | Sensor Wire | Purpose |
|-----------------|------|------------|---------|
| Pin 2 | 5V | RED | Sensor power |
| Pin 6 | GND | BLACK | Sensor ground |
| Pin 18 | GPIO 24 | YELLOW | Pulse signal input |

### Common Ground (Critical)

All ground points must be connected together:
- Raspberry Pi GND (Pin 6)
- L293D top GND pin
- L293D bottom GND terminal
- Power supply BLACK (−) terminal
- YF-S201 BLACK wire

### Complete Wiring Summary

```
Raspberry Pi                L293D Motor Driver
──────────────              ──────────────────
Pin 12 (GPIO 18) ─────────► EN1   (direct wire, jumper removed)
Pin 11 (GPIO 17) ─────────► IN1
Pin 13 (GPIO 27) ─────────► IN2
Pin 6  (GND)     ─────────► GND (top)
                            VIN  ◄──── Power Supply RED (+) 11.6V
                            GND  ◄──── Power Supply BLACK (−)
                            A+   ────► Pump BLACK wire
                            B−   ────► Pump YELLOW wire

Raspberry Pi                YF-S201 Flow Sensor
──────────────              ───────────────────
Pin 2  (5V)      ─────────► RED wire
Pin 6  (GND)     ─────────► BLACK wire
Pin 18 (GPIO 24) ◄───────── YELLOW wire (pulse signal)

Laptop/Charger
──────────────
USB-C ────────────────────► Raspberry Pi USB-C (power)
```

---

## Software Requirements

- Raspberry Pi OS (Bullseye or later)
- Python 3.x
- Flask
- RPi.GPIO

---

## Installation

### Step 1 — Update the system

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip python3-venv -y
```

### Step 2 — Clone the repository

```bash
git clone https://github.com/yourusername/periflow.git
cd periflow
```

### Step 3 — Create virtual environment and install dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install flask RPi.GPIO
```

### Step 4 — Run the application

```bash
python3 app.py
```

You should see:
```
* Running on http://0.0.0.0:5000
* Running on http://192.168.x.x:5000
```

### Step 5 — Open the dashboard

Open a browser on any device on the same network and go to:
```
http://<raspberry-pi-ip>:5000
```

To find your Pi's IP address:
```bash
hostname -I
```

---

## Auto-start on Boot (Optional)

Create a systemd service so the app starts automatically when the Pi boots:

```bash
sudo nano /etc/systemd/system/periflow.service
```

Paste the following:

```ini
[Unit]
Description=PeriFlow Pump Controller
After=network.target

[Service]
WorkingDirectory=/home/pi/periflow
ExecStart=/home/pi/periflow/venv/bin/python3 app.py
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl enable periflow
sudo systemctl start periflow
```

---

## Usage

1. Power on the Raspberry Pi and power supply
2. Open the dashboard in a browser at `http://<pi-ip>:5000`
3. Set the desired flow rate using the slider or input field (0–100 mL/min)
4. Click **START PUMP** to begin pumping
5. Optionally enter a **target volume** in the volume card — the pump will stop automatically when reached
6. Click **RESET COUNTER** to zero the volume and elapsed time
7. Use **FORWARD / REVERSE** buttons to change pump direction
8. Click **STOP PUMP** at any time to stop

---

## Project Structure

```
periflow/
│
├── app.py              # Flask backend — GPIO control, flow calculation, REST API
│
└── static/
    └── index.html      # Web dashboard — live flow display, chart, controls, volume tracker
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Serves the dashboard HTML |
| `/api/status` | GET | Returns current pump state, flow rate, volume as JSON |
| `/api/start` | POST | Starts the pump at current duty cycle |
| `/api/stop` | POST | Stops the pump |
| `/api/set` | POST | Sets target flow rate and direction |
| `/api/reset_volume` | POST | Resets volume counter and elapsed time to zero |

### Example `/api/status` response

```json
{
  "running": true,
  "flow_rate": 62.5,
  "target_flow": 60.0,
  "duty_cycle": 92.0,
  "direction": "forward",
  "voltage": 11.6,
  "total_volume": 124.83,
  "volume_time": 120
}
```

### Example `/api/set` request

```json
{
  "target_flow": 60.0,
  "direction": "forward"
}
```

---

## Calibration

The system requires calibration specific to your pump and sensor. Update these values in `app.py`:

```python
MIN_DUTY = 85    # Minimum duty cycle where your pump starts spinning
MAX_DUTY = 100   # Maximum duty cycle
MIN_FLOW = 0     # Flow rate at zero
MAX_FLOW = 100   # Flow rate in mL/min at 100% duty (measured)

# In calculate_flow_rate():
flow_lpm = (pulses * 60) / 3913   # Replace 3913 with your calibration factor
```

### How to calibrate

**Finding MIN_DUTY:**
Run the pump at increasing duty cycles (50%, 60%, 70%...) and note the lowest percentage where the motor starts spinning. Set this as `MIN_DUTY`.

**Finding MAX_FLOW:**
Run the pump at 100% duty for exactly 60 seconds, collect and measure the output in mL. That value is your `MAX_FLOW`.

**Finding the pulse factor:**
```
Pulse Factor = (Average pulses per second × 60) / (Measured flow in L/min)
```

For example if you get 5 pulses/sec at 100 mL/min:
```
Pulse Factor = (5 × 60) / (100 / 1000) = 300 / 0.1 = 3000
```

---

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| Motor always full speed, PWM has no effect | EN1 jumper on L293D is still in place | Remove the jumper cap and connect GPIO 18 directly to EN1 |
| `RuntimeError: Failed to add edge detection` | GPIO pin occupied from previous run | Use polling approach (already implemented in app.py) or reboot Pi |
| `SyntaxError: Non-UTF-8 code` in app.py | Special characters pasted into file | Rewrite file using `cat > app.py << 'EOF'` command |
| Flow rate showing very high (e.g. 666 mL/min) | Wrong pulse calibration factor | Recalibrate using physical measurement |
| Site cannot be reached in browser | Flask is not running | SSH into Pi and run `python3 app.py` |
| Pump runs but wrong direction | Pump wires reversed | Swap BLACK and YELLOW wires on A+ and B− terminals |
| Motor not starting at low flow rates | Duty cycle below MIN_DUTY threshold | Increase MIN_DUTY value in app.py to match your pump |
| Two alternating readings on dashboard | Vibration noise causing false pulses | Smoothing already applied in calculate_flow_rate() |

---

## Future Improvements

- [ ] Data logging to CSV file with timestamps
- [ ] PID closed-loop control for precise flow rate maintenance
- [ ] Email or SMS alert when target volume is reached
- [ ] Multiple pump channel support
- [ ] Flow rate scheduling (run at X mL/min for Y minutes)
- [ ] Historical data graphs and export
- [ ] Mobile-optimised dashboard layout
- [ ] User authentication for remote access

---

## Acknowledgements

- [Flask](https://flask.palletsprojects.com/) — lightweight Python web framework
- [RPi.GPIO](https://pypi.org/project/RPi.GPIO/) — Raspberry Pi GPIO library
- [YF-S201 Flow Sensor](http://www.yflowsensor.com/) — Hall effect flow measurement

---

## License

This project is licensed under the MIT License.

```
MIT License — feel free to use, modify, and distribute.
```
