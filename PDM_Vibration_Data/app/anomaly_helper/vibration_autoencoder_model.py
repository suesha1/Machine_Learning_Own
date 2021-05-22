import os
import pandas as pd
import numpy as np
from sklearn import preprocessing
import seaborn as sns
sns.set(color_codes=True)
import matplotlib.pyplot as plt
from numpy.random import seed
import tensorflow as tf
#tf.random.set_seed(seed)

from keras.layers import Input, Dropout
from keras.layers.core import Dense 
from keras.models import Model, Sequential, load_model
from keras import regularizers
from keras.models import model_from_json


def vibration_autoencoder_model(input_dims):
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

    seed(10)
#set_random_seed(10)
    act_func = 'elu'

# Input layer:
# First hidden layer, connected to input vector X. 
    inputLayer = Input(shape=(input_dims,))
    h = Dense(10,activation=act_func,
                kernel_initializer='glorot_uniform',
                kernel_regularizer=regularizers.l2(0.0),
                input_shape=(X_train.shape[1],)
               )(inputLayer)
    h = Dense(2,activation=act_func,
                kernel_initializer='glorot_uniform')(h)
    h = Dense(10,activation=act_func,
                kernel_initializer='glorot_uniform')(h)
    h = Dense(input_dims,
                kernel_initializer='glorot_uniform')(h)

    return Model(inputs=inputLayer, outputs=h)
    

def load_model_vibration():
   
    model_vibration = load_model(os.path.join('.','app','anomaly_helper','vibration_autoencoder_model','saved_model.h5'))
    #model_vibration = vibration_autoencoder_model(input_dims)
    return model_vibration
    