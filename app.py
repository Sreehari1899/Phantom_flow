from flask import Flask,jsonify,request,send_from_directory
import RPi.GPIO as GPIO,threading,time

app=Flask(__name__,static_folder='static')
GPIO.cleanup();GPIO.setmode(GPIO.BCM);GPIO.setwarnings(False)
EN1,IN1,IN2,FLOW_PIN=18,17,27,24
for p in[EN1,IN1,IN2]:GPIO.setup(p,GPIO.OUT)
GPIO.setup(FLOW_PIN,GPIO.IN,pull_up_down=GPIO.PUD_UP)
pwm=GPIO.PWM(EN1,1000);pwm.start(0)

# ── Calibration (from real measurements) ──────────────────────
# 85% duty  -> 46 mL/min  (minimum where motor spins)
# 100% duty -> 110 mL/min (measured max)
# Pulse factor: 2700 (calibrated from sensor)
MIN_DUTY    = 85
MIN_FLOW    = 46.0
MAX_FLOW    = 110.0
PULSE_FACTOR= 2700
PULSE_CYCLE = 10      # seconds per ON/OFF cycle for pulsed mode

s={'running':False,'duty':0,'dir':'forward','flow':0.0,'target':0.0,
   'voltage':11.6,'pulses':0,'volume':0.0,'t':0,'mode':'continuous'}

# ── Helpers ───────────────────────────────────────────────────
def duty_for_flow(f):
    """Duty cycle for continuous mode (flows >= MIN_FLOW)."""
    if f<=0:return 0
    return round(min(100,MIN_DUTY+(f-MIN_FLOW)*(100-MIN_DUTY)/(MAX_FLOW-MIN_FLOW)),1)

def dirset(d):
    GPIO.output(IN1,GPIO.HIGH if d=='forward' else GPIO.LOW)
    GPIO.output(IN2,GPIO.LOW if d=='forward' else GPIO.HIGH)

def do_stop():
    pwm.ChangeDutyCycle(0);GPIO.output(IN1,GPIO.LOW);GPIO.output(IN2,GPIO.LOW)
    s['running']=False;s['duty']=0;s['mode']='continuous'

# ── Thread 1: Flow sensor pulse counter ──────────────────────
def monitor():
    prev=GPIO.input(FLOW_PIN)
    while True:
        cur=GPIO.input(FLOW_PIN)
        if prev==1 and cur==0:s['pulses']+=1
        prev=cur;time.sleep(0.001)

# ── Thread 2: Flow rate calculation (every 1s) ──────────────
def calc():
    while True:
        time.sleep(1)
        p=s['pulses'];s['pulses']=0
        new_flow=round((p*60/PULSE_FACTOR)*1000,1)
        s['flow']=round((s['flow']+new_flow)/2,1)
        if s['running']:
            ml=round(s['flow']/60,3)
            s['volume']=round(s['volume']+ml,2);s['t']+=1

# ── Thread 3: Pump control (owns all PWM output) ────────────
def pump_control():
    while True:
        if not s['running'] or s['target']<=0:
            time.sleep(0.5)
            continue

        target=s['target']

        if target>=MIN_FLOW:
            # CONTINUOUS MODE: steady PWM
            s['mode']='continuous'
            dc=duty_for_flow(target)
            dirset(s['dir']);pwm.ChangeDutyCycle(dc);s['duty']=dc
            time.sleep(1)
        else:
            # PULSED MODE: burst at MIN_DUTY, then off
            s['mode']='pulsed'
            on_ratio=target/MIN_FLOW
            on_time=max(0.5,round(on_ratio*PULSE_CYCLE,1))
            off_time=round(PULSE_CYCLE-on_time,1)

            # ON phase
            if s['running'] and s['target']<MIN_FLOW:
                dirset(s['dir']);pwm.ChangeDutyCycle(MIN_DUTY);s['duty']=MIN_DUTY
                time.sleep(on_time)

            # OFF phase
            if s['running'] and s['target']<MIN_FLOW:
                pwm.ChangeDutyCycle(0);s['duty']=0
                time.sleep(off_time)

threading.Thread(target=monitor,daemon=True).start()
threading.Thread(target=calc,daemon=True).start()
threading.Thread(target=pump_control,daemon=True).start()

# ── API Routes ───────────────────────────────────────────────
@app.route('/')
def index():return send_from_directory('static','index.html')

@app.route('/api/status')
def status():
    return jsonify({'running':s['running'],'flow_rate':s['flow'],'target_flow':s['target'],
        'duty_cycle':s['duty'],'direction':s['dir'],'voltage':s['voltage'],
        'total_volume':s['volume'],'volume_time':s['t'],'mode':s['mode']})

@app.route('/api/start',methods=['POST'])
def start():
    d=request.json or {}
    s['target']=float(d.get('target_flow',s['target']))
    s['dir']=d.get('direction',s['dir'])
    s['running']=True
    # pump_control thread handles all PWM from here
    return jsonify({'status':'started'})

@app.route('/api/stop',methods=['POST'])
def stop():
    do_stop();return jsonify({'status':'stopped'})

@app.route('/api/set',methods=['POST'])
def setflow():
    d=request.json
    s['target']=float(d.get('target_flow',0))
    s['dir']=d.get('direction','forward')
    # pump_control thread picks up changes automatically
    return jsonify({'status':'updated'})

@app.route('/api/reset_volume',methods=['POST'])
def reset():
    s['volume']=0.0;s['t']=0
    return jsonify({'status':'reset'})

if __name__=='__main__':
    try:app.run(host='0.0.0.0',port=5000,debug=False)
    except KeyboardInterrupt:pass
    finally:pwm.stop();GPIO.cleanup()
