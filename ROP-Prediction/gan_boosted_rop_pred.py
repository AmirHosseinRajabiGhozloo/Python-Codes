# -*- coding: utf-8 -*-
"""GAN-Boosted-ROP-Pred.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1IbhITZZt26oI5FJOM6KbkirhF5WpJT6x
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import tensorflow as tf
from tensorflow.keras.layers import (concatenate, Conv1D,Conv2D,Conv1D,MaxPool2D,add,Input,Dense,Flatten,Reshape,
                                     BatchNormalization,Activation)
from tensorflow.keras.models import Model,Sequential
from tensorflow.keras.optimizers import (RMSprop,Adam,Nadam)
from tensorflow.keras.activations import relu
from tensorflow.keras.layers import LeakyReLU
from tensorflow.keras.callbacks import EarlyStopping as ES
from tensorflow.keras.regularizers import l2
from tensorflow.keras.models import save_model
import matplotlib
from sklearn.model_selection import train_test_split as tts
from sklearn.metrics import mean_squared_error as MSE
from sklearn.metrics import mean_absolute_percentage_error as MAPE
from sklearn.metrics import mean_absolute_error as MAE
from scipy.io import savemat
from scipy.io import loadmat

def R2 (true,predicted):
    import numpy as np
    R2 = np.mean((predicted-predicted.mean())*(true-true.mean()))/(np.std(predicted)*np.std(true))
    return R2
def R(true,predicted):
    R = (np.sum((true-true.mean())*(predicted-predicted.mean())))/(np.sqrt((np.sum((true-true.mean())**2))*np.sum((true-true.mean())**2)))
    return R

df_14 = pd.read_excel('D:\\AmirRajabi\\ROP-Pred\\data\\F14-cleaned.xlsx')
df_14

df_15 = pd.read_excel('D:\\AmirRajabi\\ROP-Pred\\data\\F15-cleaned.xlsx')
df_15

data_14 = df_14.values[:,1:]
data_15 = df_15.values[:,1:]
data = np.r_[data_14,data_15]
df_data = pd.DataFrame(data,columns = df_14.columns[1:])
df_data

x = data[:,1:]
y = data[:,0]

xtr,xts,ytr,yts = tts(x,y,train_size=0.8,random_state=1,shuffle=True)

print('xtr shape:',xtr.shape)
print('xts shape:',xts.shape)
print('ytr shape:',ytr.shape)
print('yts shape:',yts.shape)

"""# GAN Model"""

def build_gen(shape,zdim):
    model = Sequential()
    model.add(Dense(10,input_dim=zdim))
    model.add(LeakyReLU(alpha=0.01))
    model.add(Dense(20))
    model.add(LeakyReLU(alpha=0.01))
    shp = 1
    for i in shape:
        shp *= i
    model.add(Dense(shp,activation=LeakyReLU(alpha=0.01)))
    model.add(Reshape(shape))
    return model

def build_dis(shape):
    model=Sequential()
    model.add(Flatten(input_shape=shape))
    model.add(Dense(128))
    model.add(LeakyReLU(alpha=0.01))
    model.add(Dense(1,activation=LeakyReLU(alpha=0.01)))
    return model

def build_gan(gen,dis):
    model = Sequential()
    model.add(gen)
    model.add(dis)
    return model

shape = (1,1)
dis = build_dis(shape)
dis.compile(loss='binary_crossentropy',
           optimizer=Adam(0.001),
           metrics=['accuracy'])

dis.trainable = False
zdim = 50 # in our problem, zdim is the number of nodes in last hidden layer of NN model
gen = build_gen(shape,zdim)

gen.summary()

gan = build_gan(gen,dis)
gan.compile(loss='mean_squared_error',
           optimizer=Adam(learning_rate=0.002))

# training
def train_gan(iterations,batch_size,interval):
    global ytr
    global zdim
    losses = []
    accuracies = []
    iteration_checks = []

    real = np.ones((batch_size,1))
    fake = np.zeros((batch_size,1))

    for iteration in range(iterations):
        ids = np.random.randint(0,ytr.shape[0],batch_size)
        tru = ytr[ids]
        #tru = tru.reshape(tru.shape[0],1)

        z = np.random.normal(0,1,(batch_size,zdim))
        pred = gen.predict(z)

        dis_loss_accuracy_real = dis.train_on_batch(tru,real)
        dis_loss_accuracy_fake = dis.train_on_batch(pred,fake)

        dloss,daccuracy = 0.5 * np.add(dis_loss_accuracy_real,dis_loss_accuracy_fake)

        z = np.random.normal(0, 1, (batch_size, zdim))
        gan_loss = gan.train_on_batch(z,real)

        if (iteration+1) % interval == 0:
            losses.append((dloss,gan_loss))
            accuracies.append(100.0*daccuracy)
            iteration_checks.append(iteration+1)

            print("%d [D loss: %f , acc: %.2f] [G loss: %f]" %
                  (iteration+1,dloss,100.0*daccuracy,gan_loss))
        plt.plot(losses)
train_gan(1000,16,10)

"""# GAN-ANN Models"""

# 1: GAN-Boosted MLP
inputs = Input(shape= xtr.shape[1])
############################
dns = Dense(units = zdim, activation = LeakyReLU(alpha = 0.01))(inputs)
###########################coupling with pretrained generator
MODEL = Model(inputs,dns)
model = Sequential()
model.add(MODEL)
gen.trainable = False
model.add(gen)

xtr = xtr.reshape(xtr.shape +(1,))
xtr.shape

# 2: GAN-Boosted 1D-CNN
inputs = Input(shape= xtr.shape[1:])
#########################
c1 = Conv1D(8,4,padding='same', activation = LeakyReLU(alpha=0.01))(inputs)
c2 = Conv1D(8,2,padding='same', activation = LeakyReLU(alpha=0.01))(c1)
c3 = Conv1D(8,4,padding='same', activation = LeakyReLU(alpha=0.01))(c2)
########################
fltn = Flatten()(c3)
dns = Dense(zdim, activation= LeakyReLU(alpha=0.01))(fltn)
#######################coupling with pretrained generator
MODEL = Model(inputs,dns)
model = Sequential()
model.add(MODEL)
gen.trainable = False
model.add(gen)

# 3:GAN-Boosted 1D-Res-CNN
inputs = Input(shape= xtr.shape[1:])
#########################
c1 = Conv1D(16,5,padding='same', activation = LeakyReLU(alpha=0.01))(inputs)
c2 = Conv1D(16,5,padding='same', activation = LeakyReLU(alpha=0.01))(c1)
c3 = Conv1D(16,5,padding='same', activation = LeakyReLU(alpha=0.01))(c2)
########################
conc = concatenate([c3,inputs])
fltn = Flatten()(conc)
dns = Dense(zdim, activation = LeakyReLU(alpha=0.01))(fltn)
#######################coupling with pretrained generator
MODEL = Model(inputs,dns)
model = Sequential()
model.add(MODEL)
gen.trainable = False
model.add(gen)

"""# Models without Boosting"""

# 1: MLP
inputs = Input(shape= xtr.shape[1])
############################
dns = Dense(units = zdim, activation = LeakyReLU(alpha = 0.01))(inputs)
out = Dense(1)(dns)
###########################coupling with pretrained generator
model = Model(inputs,out)

xtr = xtr.reshape(xtr.shape +(1,))
xtr.shape

# 2:1D-CNN
inputs = Input(shape= xtr.shape[1:])
#########################
c1 = Conv1D(8,4,padding='same', activation = LeakyReLU(alpha=0.01))(inputs)
c2 = Conv1D(8,2,padding='same', activation = LeakyReLU(alpha=0.01))(c1)
c3 = Conv1D(8,4,padding='same', activation = LeakyReLU(alpha=0.01))(c2)
########################
fltn = Flatten()(c3)
dns = Dense(zdim, activation= LeakyReLU(alpha=0.01))(fltn)
out = Dense(1)(dns)
#######################coupling with pretrained generator
model = Model(inputs,out)

# 1D-Res-CNN
inputs = Input(shape= xtr.shape[1:])
#########################
c1 = Conv1D(8,8,padding='same', activation = LeakyReLU(alpha=0.01))(inputs)
c2 = Conv1D(8,4,padding='same', activation = LeakyReLU(alpha=0.01))(c1)
c3 = Conv1D(8,8,padding='same', activation = LeakyReLU(alpha=0.01))(c2)
########################
conc = concatenate([c3,inputs])
fltn = Flatten()(conc)
dns = Dense(zdim, activation = LeakyReLU(alpha=0.01))(fltn)
out = Dense(1)(dns)
#######################coupling with pretrained generator
model = Model(inputs,out)

"""# Model Summary and Training"""

model.summary()

lr = 0.002
model.compile(loss='mean_squared_error',optimizer=Adam(learning_rate=lr),metrics=['mse','mae'])

hist = model.fit(xtr,ytr,
                 epochs=2000,validation_split=0.5,verbose=1,
                 callbacks = [ES(monitor='val_loss', patience=50,
                                 restore_best_weights=True)])

plt.plot(hist.history['loss'])
plt.plot(hist.history['val_loss'])

"""# Model evaluation
