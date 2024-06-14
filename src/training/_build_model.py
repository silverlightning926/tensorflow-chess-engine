import os

from src.utils import find_project_directory
from keras.api.layers import Dense, Conv2D, Dropout, Input, BatchNormalization, \
    GlobalAveragePooling2D, LeakyReLU, SpatialDropout2D


def build_model():
    project_dir = find_project_directory()

    if os.path.exists(os.path.join(project_dir, 'models/model.keras')):
        print('Model already exists. Loading model...')
        model = load_model('models/model.keras')

    else:
        model = Sequential([
            Input(shape=(8, 8, 12)),
            Conv2D(64, (3, 3), padding='same'),
            LeakyReLU(negative_slope=0.1),
            BatchNormalization(),
            Conv2D(128, (3, 3), padding='same'),
            LeakyReLU(negative_slope=0.1),
            BatchNormalization(),
            SpatialDropout2D(0.2),
            Conv2D(256, (3, 3), padding='same'),
            LeakyReLU(negative_slope=0.1),
            BatchNormalization(),
            GlobalAveragePooling2D(),
            Dense(512),
            Dropout(0.5),
            Dense(256),
            Dense(1, activation='tanh')
        ])

    model.compile(
        optimizer='adam',
        loss='mean_squared_error',
        metrics=['accuracy']
    )

    return model
