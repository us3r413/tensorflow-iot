import csv
ServerURL = 'https://class.iottalk.tw' #For example: 'https://DomainName'
MQTT_broker = 'iot.iottalk.tw' # MQTT Broker address, for example: 'DomainName' or None = no MQTT support
MQTT_port = 8883
MQTT_encryption = True
MQTT_User = 'iottalk'
MQTT_PW = 'iottalk2023'

device_model = 'Dummy_Device'
IDF_list = ['Dummy_Sensor']
ODF_list = ['Dummy_Control']
device_id = None #if None, device_id = MAC address
device_name = None
exec_interval = 0.5  # IDF/ODF interval

rowcnt = 240
fieldnames = ['AccX', 'AccY', 'AccZ', 'GyroX', 'GyroY', 'GyroZ']
csvfile = open('counterclockwise3.csv', 'w', newline='')
writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
writer.writeheader()

def Dummy_Sensor():
    return 0

def Dummy_Control(*data):
    global rowcnt, writer

    if rowcnt <= 0:
        print('Recording finished. Bye!')
        csvfile.close()
        exit()

    rowcnt -= 1

    try:
        # Extract acceleration and gyroscope readings
        acc = data[0][0][0]
        gyro = data[0][0][1]

        row = {
            'AccX': acc[0],
            'AccY': acc[1],
            'AccZ': acc[2],
            'GyroX': gyro[0],
            'GyroY': gyro[1],
            'GyroZ': gyro[2],
        }

        writer.writerow(row)
        csvfile.flush()

        print(row)

    except (IndexError, TypeError) as e:
        print(f'Invalid sensor data: {data}, error: {e}')

def on_register(r):
    print(f'Device name: {r["d_name"]}')    
    '''
    #You can write some SA routine code here, for example: 
    import time, DAI
    while True:
        DAI.push('Dummy_Sensor', [100, 200])  
        time.sleep(exec_interval)    
    '''