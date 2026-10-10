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

TIME_STEP = 20
FEATURES = 6

model = tf.keras.models.load_model('circle_detector.keras')
scaler = joblib.load('sensor_scaler.pkl')

sensor_buffer = deque(maxlen=TIME_STEP)

latest_prediction = 0
light_state = 0

POSITIVE_THRESHOLD = 0.8
NEGATIVE_THRESHOLD = 0.3
positive_count = 0
negative_count = 0
GESTURE_CONFIRMATION = 3

# Require a negative detection before accepting another gesture
gesture_armed = True

def Dummy_Control(data):
    global latest_prediction, light_state
    global positive_count, negative_count, gesture_armed

    try:
        # Extract accelerometer and gyroscope data
        sensor = data[0]
        acc = sensor[0]
        gyro = sensor[1]

        reading = list(acc) + list(gyro)

        if len(reading) != FEATURES:
            print("Unexpected feature count:", len(reading))
            return

        sensor_buffer.append(reading)

        if len(sensor_buffer) < TIME_STEP:
            return

        # Prepare input for the model
        X = np.asarray(sensor_buffer, dtype=np.float32)
        X = scaler.transform(X)
        X = X.reshape(1, TIME_STEP, FEATURES)

        probability = float(model.predict(X, verbose=0)[0, 0])
        latest_prediction = int(probability >= 0.5)

        print(
            f"Probability: {probability:.3f}, "
            f"Prediction: {latest_prediction}, "
            f"Light: {light_state}"
        )

        # Detect a circular gesture
        if probability >= POSITIVE_THRESHOLD:
            positive_count += 1
            negative_count = 0

            if (
                positive_count >= GESTURE_CONFIRMATION
                and gesture_armed
            ):
                light_state = 1 - light_state
                gesture_armed = False
                positive_count = 0

                print(f"Light toggled: {light_state}")

        # Re-arm after the gesture ends
        elif probability <= NEGATIVE_THRESHOLD:
            negative_count += 1
            positive_count = 0

            if negative_count >= GESTURE_CONFIRMATION:
                gesture_armed = True

    except (IndexError, TypeError, ValueError) as e:
        print(f"Invalid sensor data: {e}")
        
        
def Dummy_Sensor():
    return latest_prediction


def on_register(r):
    print(f'Device name: {r["d_name"]}')    
    '''
    #You can write some SA routine code here, for example: 
    import time, DAI
    while True:
        DAI.push('Dummy_Sensor', [100, 200])  
        time.sleep(exec_interval)    
    '''