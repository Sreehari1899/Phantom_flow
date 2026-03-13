
from flask import Flask, jsonify, request, send_from_directory
import RPi.GPIO as GPIO
import threading
import time

app = Flask(__name__, static_folder='static')

# --- GPIO Setup ---
GPIO.cleanup()
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

EN1 = 18
IN1 = 17
IN2 = 27
FLOW_SENSOR_PIN = 24

GPIO.setup(EN1, GPIO.OUT)
GPIO.setup(IN1, GPIO.OUT)
GPIO.setup(IN2, GPIO.OUT)
GPIO.setup(FLOW_SENSOR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# PWM at 1000Hz
pwm = GPIO.PWM(EN1, 1000)
pwm.start(0)

# --- State ---
state = {
    "running": False,
    "duty_cycle": 0,
    "direction": "forward",
    "flow_rate": 0.0,
    "target_flow": 0.0,
    "voltage": 11.6,
    "pulse_count": 0,
}

# --- Flow Sensor (polling instead of interrupt) ---
def monitor_flow():
    last_state = GPIO.input(FLOW_SENSOR_PIN)
    while True:
        current_state = GPIO.input(FLOW_SENSOR_PIN)
        # Detect falling edge manually
        if last_state == 1 and current_state == 0:
            state["pulse_count"] += 1
        last_state = current_state
        time.sleep(0.001)  # poll every 1ms

def calculate_flow_rate():
    while True:
        time.sleep(1)
        pulses = state["pulse_count"]
        state["pulse_count"] = 0
        flow_lpm = (pulses * 60) / 3913
        state["flow_rate"] = round(flow_lpm * 1000, 1)

# Start both threads
threading.Thread(target=monitor_flow, daemon=True).start()
threading.Thread(target=calculate_flow_rate, daemon=True).start()

# --- Pump Control ---
def set_direction(direction):
    if direction == "forward":
        GPIO.output(IN1, GPIO.HIGH)
        GPIO.output(IN2, GPIO.LOW)
    else:
        GPIO.output(IN1, GPIO.LOW)
        GPIO.output(IN2, GPIO.HIGH)

def stop_pump():
    pwm.ChangeDutyCycle(0)
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.LOW)
    state["running"] = False
    state["duty_cycle"] = 0

# --- API Routes ---
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/api/status')
def get_status():
    return jsonify({
        "running": state["running"],
        "flow_rate": state["flow_rate"],
        "target_flow": state["target_flow"],
        "duty_cycle": state["duty_cycle"],
        "direction": state["direction"],
        "voltage": state["voltage"],
    })

@app.route('/api/start', methods=['POST'])
def start_pump():
    set_direction(state["direction"])
    pwm.ChangeDutyCycle(state["duty_cycle"])
    state["running"] = True
    return jsonify({"status": "started"})

@app.route('/api/stop', methods=['POST'])
def stop():
    stop_pump()
    return jsonify({"status": "stopped"})

@app.route('/api/set', methods=['POST'])
def set_flow():
    data = request.json
    target = float(data.get("target_flow", 0))
    direction = data.get("direction", "forward")
    duty = min(100, max(0, target))
    state["target_flow"] = target
    state["direction"] = direction
    state["duty_cycle"] = duty
    if state["running"]:
        set_direction(direction)
        pwm.ChangeDutyCycle(duty)
    return jsonify({"status": "updated", "duty_cycle": duty})

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        pass
    finally:
        pwm.stop()
        GPIO.cleanup()
EOF
