from collections import deque

import numpy as np
import tensorflow as tf
import joblib

ServerURL = 'https://class.iottalk.tw'

MQTT_broker = 'iot.iottalk.tw'
MQTT_port = 8883
MQTT_encryption = True
MQTT_User = 'iottalk'
MQTT_PW = 'iottalk2023'

device_model = 'Dummy_Device'
IDF_list = ['Dummy_Sensor']
ODF_list = ['Dummy_Control']

device_id = None
device_name = None
exec_interval = 0.5

TIME_STEP = 15
FEATURES = 6

model = tf.keras.models.load_model('clockwise_model.keras')
scaler = joblib.load('clockwise_scaler.pkl')

sensor_buffer = deque(maxlen=TIME_STEP)

light_state = 0

clockwise_con = 0
counterclockwise_con = 0
con_cnt = 4
certain_threshold = 0.8
def Dummy_Control(data):
    global light_state, clockwise_con, counterclockwise_con
    try:
        sensor = data[0]
        acc, gyro = sensor
        row = list(acc) + list(gyro)
    except (IndexError, TypeError, ValueError) as e:
        print(f"Invalid sensor data: {e}")
        return

    if len(row) != FEATURES:
        print(f"Invalid sensor data: expected 6 values, got {len(row)}")
        return

    sensor_buffer.append(row)

    # Wait until 20 readings are available.
    if len(sensor_buffer) < TIME_STEP:
        print(f"Collecting sensor data: {len(sensor_buffer)}/{TIME_STEP}")
        return

    # Shape: (1, 20, 6)
    model_input = np.asarray(
        sensor_buffer, dtype=np.float32
    ).reshape(1, TIME_STEP, FEATURES)

    # Use the same StandardScaler fitted during training.
    model_input = scaler.transform(
        model_input.reshape(-1, FEATURES)
    ).reshape(1, TIME_STEP, FEATURES)

    # Predict the gesture.
    probabilities = model.predict(model_input, verbose=0)[0]
    gesture = int(np.argmax(probabilities))
    confidence = float(probabilities[gesture])

    if gesture == 1 and confidence >= certain_threshold:
        clockwise_con += 1
        print(f"Clockwise detected ({confidence:.2%})")
        counterclockwise_con = 0
        if clockwise_con >= con_cnt:
            light_state = 1
            print("Light ON")
            clockwise_con = 0
            counterclockwise_con = 0

    elif gesture == 2 and confidence >= certain_threshold:
        counterclockwise_con += 1
        clockwise_con = 0
        print(f"Counterclockwise detected ({confidence:.2%}) ")
        if counterclockwise_con >= con_cnt:
            light_state = 0
            print("Light OFF")
            clockwise_con = 0
            counterclockwise_con = 0
    else:
        # Random movement does not change the current light state.
        if gesture == 0:
            clockwise_con = 0
            counterclockwise_con = 0
            print(f"Random movement ({confidence:.2%}) -> NO CHANGE")
        elif gesture == 1:
            print(f"Uncertain clockwise ({confidence:.2%}) -> NO CHANGE")
        else:
            print(f"Uncertain counterclockwise ({confidence:.2%}) -> NO CHANGE")
        
        
def Dummy_Sensor():
    return light_state


def on_register(r):
    print(f'Device name: {r["d_name"]}')    
    '''
    #You can write some SA routine code here, for example: 
    import time, DAI
    while True:
        DAI.push('Dummy_Sensor', [100, 200])  
        time.sleep(exec_interval)    
    '''