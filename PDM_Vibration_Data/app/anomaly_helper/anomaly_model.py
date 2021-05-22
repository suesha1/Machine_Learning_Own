import pickle

import tensorflow as tf
import tensorflow.keras as keras
from tensorflow.keras import backend as K
from tensorflow.keras import Input
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Dense
from tensorflow.keras.optimizers import Adam
import os

def autoencoder_model(input_dims):
    """
    Defines a Keras model for performing the anomaly detection. 
    This model is based on a simple dense autoencoder.
    
    PARAMS
    ======
        inputs_dims (integer) - number of dimensions of the input features
        
    RETURN
    ======
        Model (tf.keras.models.Model) - the Keras model of our autoencoder
    """
    
    # Autoencoder definition:
    inputLayer = Input(shape=(input_dims,))
    
    h = Dense(128, activation="relu")(inputLayer)
    #h = Dense(64, activation="relu")(inputLayer)
    h = Dense(64, activation="relu")(h)
    h = Dense(8, activation="relu")(h)
    h = Dense(64, activation="relu")(h)
    #h = Dense(64, activation="relu")(h)
    h = Dense(128, activation="relu")(h)
    h = Dense(input_dims, activation=None)(h)

    return Model(inputs=inputLayer, outputs=h)
    

def load_model_anomaly(input_dims):
	model = autoencoder_model(input_dims)
    #print(os.getcwd())
	model = tf.keras.models.load_model(os.path.join('.','app','anomaly_helper','model_weights_fan'))
	return model