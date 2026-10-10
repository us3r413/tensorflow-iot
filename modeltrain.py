import numpy as np
import pandas as pd
import glob
import joblib
import tensorflow as tf

from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

TIME_STEP = 20
FEATURES = [
    'AccX', 'AccY', 'AccZ',
    'GyroX', 'GyroY', 'GyroZ'
]

# Example file naming:
# circle_1.csv, circle_2.csv
# random_1.csv, random_2.csv

X_windows = []
y_windows = []

for filename in glob.glob('data/*.csv'):
    df = pd.read_csv(filename)

    # Assign labels based on the file name.
    label = 1 if 'rotate' in filename.lower() else 0

    data = df[FEATURES].apply(
        pd.to_numeric, errors='coerce'
    ).dropna().to_numpy(dtype=np.float32)

    # Create windows of 20 readings.
    for start in range(0, len(data) - TIME_STEP + 1, 2):
        window = data[start:start + TIME_STEP]

        X_windows.append(window)
        y_windows.append(label)

X = np.array(X_windows, dtype=np.float32)
y = np.array(y_windows, dtype=np.float32)

if len(X) == 0:
    raise ValueError("No valid training windows found.")

# Split into training and validation data.
indices = np.arange(len(X))
train_idx, val_idx = train_test_split(
    indices,
    test_size=0.2,
    random_state=42,
    stratify=y
)

X_train, X_val = X[train_idx], X[val_idx]
y_train, y_val = y[train_idx], y[val_idx]

# Fit scaler using training windows only.
scaler = StandardScaler()
scaler.fit(X_train.reshape(-1, len(FEATURES)))

def scale_windows(data):
    shape = data.shape
    return scaler.transform(
        data.reshape(-1, shape[-1])
    ).reshape(shape).astype(np.float32)

X_train = scale_windows(X_train)
X_val = scale_windows(X_val)

model = tf.keras.Sequential([
    tf.keras.layers.Input(shape=(TIME_STEP, 6)),
    tf.keras.layers.LSTM(32, return_sequences=True),
    tf.keras.layers.LSTM(16),
    tf.keras.layers.Dense(8, activation='relu'),
    tf.keras.layers.Dense(1, activation='sigmoid')
])

model.compile(
    optimizer='adam',
    loss='binary_crossentropy',
    metrics=['accuracy']
)

model.fit(
    X_train, y_train,
    validation_data=(X_val, y_val),
    epochs=30,
    batch_size=32,
    callbacks=[
        tf.keras.callbacks.EarlyStopping(
            monitor='val_loss',
            patience=5,
            restore_best_weights=True
        )
    ]
)

model.save('circle_detector.keras')
joblib.dump(scaler, 'sensor_scaler.pkl')

print("Model saved!")