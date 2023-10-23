# -*- coding: utf-8 -*-
"""2D_Simple_Seg_Net.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1pL9DvrM0xVPnipFHtll5mp-7k3CA4RH1
"""

from google.colab import drive
drive.mount('/content/gdrive')

# 1. Import Required Modules

import os
import glob
import keras
import random
import numpy as np
import tensorflow as tf
from keras.layers import *
import keras.backend as k
from keras.models import *
from keras.optimizers import *
import matplotlib.pyplot as plt
from skimage.transform import resize
from skimage.io import imread, imshow, imsave, imread_collection
from keras.losses import categorical_crossentropy
from keras.callbacks import ModelCheckpoint, LearningRateScheduler, EarlyStopping

# 2. Define Train & Test Path (Images + Mask Path for Train and Test Stages)

TRAIN_IMAGE_PATH = 'gdrive/My Drive/Berea_Sand_Texas/Image_Berea_512'
TRAIN_MASK_PATH = 'gdrive/My Drive/Berea_Sand_Texas/Mask_Berea_512_'

# 3. Initialize Images and Mask Size

IMG_HEIGHT, IMG_WIDTH, IMG_CHANNELS = 512, 512, 1

import glob
import cv2

Train_Input = [cv2.imread(file, cv2.IMREAD_GRAYSCALE) for file in sorted(glob.glob("gdrive/My Drive/Parker_Sand/Image_512x512/*.png"))]
Train_Mask = [cv2.imread(file, cv2.IMREAD_GRAYSCALE) for file in sorted(glob.glob("gdrive/My Drive/Parker_Sand/Label_512x512/*.png"))]

Train_Input = np.array(Train_Input)
Train_Mask = np.array(Train_Mask)

Train_Mask = cv2.normalize(Train_Mask, None, alpha=1,beta=0, norm_type=cv2.NORM_MINMAX)

Train_Mask.shape

imshow(Train_Input[20])

imshow(Train_Mask[20], cmap='Greys_r')

Train_Mask[28].shape

print('Training Input')
imshow(Train_Input[45])
plt.show()

print('Training Mask')
imshow(np.squeeze(Train_Mask[45]), cmap='Greys_r')
plt.show()

def dice_loss(y_true, y_pred):
    y_true = tf.cast(y_true, tf.float32)
    y_pred = tf.math.sigmoid(y_pred)
    numerator = 2 * tf.reduce_sum(y_true * y_pred)
    denominator = tf.reduce_sum(y_true + y_pred)

    return 1 - numerator / denominator

def jacard_coef(y_true, y_pred):
    y_true_f = k.flatten(y_true)
    y_pred_f = k.flatten(y_pred)
    intersection = k.sum(y_true_f * y_pred_f)
    return (intersection + 1.0) / (k.sum(y_true_f) + k.sum(y_pred_f) - intersection + 1.0)

def iou_coef(y_true, y_pred, smooth=1):
  intersection = k.sum(k.abs(y_true * y_pred), axis=[1,2])
  union = k.sum(y_true,[1,2])+k.sum(y_pred,[1,2])-intersection
  iou = k.mean((intersection+smooth) / (union+smooth), axis=0)
  return iou

def recall_m(y_true, y_pred):
    true_positives = k.sum(k.round(k.clip(y_true * y_pred, 0, 1)))
    possible_positives = k.sum(k.round(k.clip(y_true, 0, 1)))
    recall = true_positives / (possible_positives + k.epsilon())
    return recall

def precision_m(y_true, y_pred):
    true_positives = k.sum(k.round(k.clip(y_true * y_pred, 0, 1)))
    predicted_positives = k.sum(k.round(k.clip(y_pred, 0, 1)))
    precision = true_positives / (predicted_positives + k.epsilon())
    return precision

def f1_m(y_true, y_pred):
   precision = precision_m(y_true, y_pred)
   recall = recall_m(y_true, y_pred)
   return 2*((precision*recall)/(precision+recall+k.epsilon()))

class MaxPoolingWithArgmax2D(Layer):
    def __init__(self, pool_size=(2, 2), strides=(2, 2), padding="same", **kwargs):
        super(MaxPoolingWithArgmax2D, self).__init__(**kwargs)
        self.padding = padding
        self.pool_size = pool_size
        self.strides = strides

    def call(self, inputs, **kwargs):
        padding = self.padding
        pool_size = self.pool_size
        strides = self.strides
        if k.backend() == "tensorflow":
            ksize = [1, pool_size[0], pool_size[1], 1]
            padding = padding.upper()
            strides = [1, strides[0], strides[1], 1]
            output, argmax = k.tf.nn.max_pool_with_argmax(
                inputs, ksize=ksize, strides=strides, padding=padding
            )
        else:
            errmsg = "{} backend is not supported for layer {}".format(
                k.backend(), type(self).__name__
            )
            raise NotImplementedError(errmsg)
        argmax = k.cast(argmax, k.floatx())
        return [output, argmax]

    def compute_output_shape(self, input_shape):
        ratio = (1, 2, 2, 1)
        output_shape = [
            dim // ratio[idx] if dim is not None else None
            for idx, dim in enumerate(input_shape)
        ]
        output_shape = tuple(output_shape)
        return [output_shape, output_shape]

    def compute_mask(self, inputs, mask=None):
        return 2 * [None]


class MaxUnpooling2D(Layer):
    def __init__(self, size=(2, 2), **kwargs):
        super(MaxUnpooling2D, self).__init__(**kwargs)
        self.size = size

    def call(self, inputs, output_shape=None):
        updates, mask = inputs[0], inputs[1]
        with k.tf.compat.v1.variable_scope(self.name):
            mask = k.cast(mask, "int32")
            input_shape = k.tf.shape(updates, out_type="int32")
            #  calculation new shape
            if output_shape is None:
                output_shape = (
                    input_shape[0],
                    input_shape[1] * self.size[0],
                    input_shape[2] * self.size[1],
                    input_shape[3],
                )
            self.output_shape1 = output_shape

            # calculation indices for batch, height, width and feature maps
            one_like_mask = k.ones_like(mask, dtype="int32")
            batch_shape = k.concatenate([[input_shape[0]], [1], [1], [1]], axis=0)
            batch_range = k.reshape(
                k.tf.range(output_shape[0], dtype="int32"), shape=batch_shape
            )
            b = one_like_mask * batch_range
            y = mask // (output_shape[2] * output_shape[3])
            x = (mask // output_shape[3]) % output_shape[2]
            feature_range = k.tf.range(output_shape[3], dtype="int32")
            f = one_like_mask * feature_range

            # transpose indices & reshape update values to one dimension
            updates_size = k.tf.size(updates)
            indices = k.transpose(k.reshape(k.stack([b, y, x, f]), [4, updates_size]))
            values = k.reshape(updates, [updates_size])
            ret = k.tf.scatter_nd(indices, values, output_shape)
            return ret

    def compute_output_shape(self, input_shape):
        mask_shape = input_shape[1]
        return (
            mask_shape[0],
            mask_shape[1] * self.size[0],
            mask_shape[2] * self.size[1],
            mask_shape[3],
        )

def Seg_Net_2D_Segmentation(input_size=(IMG_HEIGHT, IMG_WIDTH, IMG_CHANNELS)):

    inputs = Input(input_size)
    n = Lambda(lambda x:x/255)(inputs)


    c1 = Conv2D(16, (3,3), activation='relu', padding='same', kernel_initializer=tf.keras.initializers.Ones())(n)
    c1 = Dropout(0.1)(c1)
    c1 = Conv2D(16, (3,3), activation='relu', padding='same')(c1)


    #p1 = MaxPooling2D((2,2))(c1)
    p1, mask_1 = MaxPoolingWithArgmax2D((2,2))(c1)


    c2 = Conv2D(32, (3,3), activation='relu', padding='same')(p1)
    c2 = Dropout(0.1)(c2)
    c2 = Conv2D(32, (3,3), activation='relu', padding='same')(c2)


    #p2 = MaxPooling2D((2,2))(c2)
    p2, mask_2 = MaxPoolingWithArgmax2D((2,2))(c2)


    c3 = Conv2D(64, (3,3), activation='relu', padding='same')(p2)
    c3 = Dropout(0.2)(c3)
    c3 = Conv2D(64, (3,3), activation='relu', padding='same')(c3)
    c3 = Dropout(0.2)(c3)
    c3 = Conv2D(64, (3,3), activation='relu', padding='same')(c3)


    #p3 = MaxPooling2D((2,2))(c3)
    p3, mask_3 = MaxPoolingWithArgmax2D((2,2))(c3)


    c4 = Conv2D(128, (3,3), activation='relu', padding='same')(p3)
    c4 = Dropout(0.2)(c4)
    c4 = Conv2D(128, (3,3), activation='relu', padding='same')(c4)
    c4 = Dropout(0.2)(c4)
    c4 = Conv2D(128, (3,3), activation='relu', padding='same')(c4)

    #p4 = MaxPooling2D((2,2))(c4)
    p4, mask_4 = MaxPoolingWithArgmax2D((2,2))(c4)


    c5 = Conv2D(256, (3,3), activation='relu', padding='same')(p4)
    c5 = Dropout(0.2)(c5)
    c5 = Conv2D(256, (3,3), activation='relu', padding='same')(c5)
    c5 = Dropout(0.2)(c5)
    c5 = Conv2D(256, (3,3), activation='relu', padding='same')(c5)


    p5, mask_5 = MaxPoolingWithArgmax2D((2,2))(c5)


    #u6 = Conv2DTranspose(128, (2,2), strides=(2,2), padding='same')(c5)
    #u6 = concatenate([u6, c4])
    up1 = MaxUnpooling2D((2,2))([p5, mask_5])


    c6 = Conv2D(256, (3,3), activation='relu', padding='same')(up1)
    c6 = Dropout(0.2)(c6)
    c6 = Conv2D(256, (3,3), activation='relu', padding='same')(c6)
    c6 = Dropout(0.2)(c6)
    c6 = Conv2D(128, (3,3), activation='relu', padding='same')(c6)


    #u7 = Conv2DTranspose(64, (2,2), strides=(2,2), padding='same')(c6)
    #u7 = concatenate([u7, c3])
    up2 = MaxUnpooling2D((2,2))([c6, mask_4])


    c7 = Conv2D(128, (3,3), activation='relu', padding='same')(up2)
    c7 = Dropout(0.2)(c7)
    c7 = Conv2D(128, (3,3), activation='relu', padding='same')(c7)
    c7 = Dropout(0.2)(c7)
    c7 = Conv2D(64, (3,3), activation='relu', padding='same')(c7)


    #u8 = Conv2DTranspose(32, (2,2), strides=(2,2), padding='same')(c7)
    #u8 = concatenate([u8, c2])
    up3 = MaxUnpooling2D((2,2))([c7, mask_3])


    c8 = Conv2D(64, (3,3), activation='relu', padding='same')(up3)
    c8 = Dropout(0.1)(c8)
    c8 = Conv2D(64, (3,3), activation='relu', padding='same')(c8)
    c8 = Dropout(0.1)(c8)
    c8 = Conv2D(32, (3,3), activation='relu', padding='same')(c8)


    #u9 = Conv2DTranspose(16, (2,2), strides=(2,2), padding='same')(c8)
    #u9 = concatenate([u9, c1], axis = 3)
    up4 = MaxUnpooling2D((2,2))([c8, mask_2])


    c9 = Conv2D(32, (3,3), activation='relu', padding='same')(up4)
    c9 = Dropout(0.1)(c9)
    c9 = Conv2D(16, (3,3), activation='relu', padding='same')(c9)


    up5 = MaxUnpooling2D((2,2))([c9, mask_1])


    c10 = Conv2D(16, (3,3), activation='relu', padding='same')(up5)


    outputs = Conv2D(1,(1,1), activation='sigmoid')(c10)

    model = Model(inputs=[inputs], outputs=[outputs])
    model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.0001), loss = ['binary_crossentropy'], metrics=[tf.keras.metrics.IoU(num_classes=2, target_class_ids=[0, 1]), tf.keras.metrics.IoU(num_classes=2, target_class_ids=[0]), tf.keras.metrics.IoU(num_classes=2, target_class_ids=[1]), f1_m ,precision_m , recall_m, 'accuracy'])
    model.summary()
    return model

model = Seg_Net_2D_Segmentation()

# 7. Show The Results per Epoch

class loss_history(keras.callbacks.Callback):

    def __init__ (self, x=4):
        self.x = x

    def on_epoch_begin(self, epoch, logs={}):

        imshow(np.squeeze(Train_Input[self.x]))
        plt.show()

        imshow(np.squeeze(Train_Mask[self.x]), cmap='Greys_r')
        plt.show()

        preds_train = self.model.predict(np.expand_dims(Train_Input[self.x], axis = 0))
        imshow(np.squeeze(preds_train[0]), cmap='Greys_r')
        plt.show()

Model_Path = 'gdrive/My Drive/Saved_Models/2D_Seg_Net/Parker_IoU_Modified_2D_Seg_Net'

earlystopper = EarlyStopping(patience=4, verbose=1)
checkpointer = ModelCheckpoint(Model_Path, verbose = 1, save_best_only=True)

Validation_Input = Train_Input[:100]
Train_Input = Train_Input[100:]
Validation_Mask = Train_Mask[:100]
Train_Mask = Train_Mask[100:]

# 8. Train U_NET Model using Training Samples

results = model.fit(Train_Input, Train_Mask,
                    validation_data=(Validation_Input, Validation_Mask),
                    batch_size=10,
                    epochs=150
                    , callbacks=[earlystopper, checkpointer, loss_history()])
#earlystopper

# 11. Show Loss and ACC Plots


# 11.1. Summarize History for Loss

plt.plot(results.history['loss'])
plt.plot(results.history['val_loss'])
plt.title('Model Loss')
plt.ylabel('loss')
plt.xlabel('epochs')
plt.legend(['Training','Validation'], loc = 'upper left')
plt.show()


# 11.1. Summarize History for IOU

plt.plot(results.history['io_u'])
plt.plot(results.history['val_io_u'])
plt.title('iou_coef')
plt.ylabel('IOU')
plt.xlabel('epochs')
plt.legend(['Training','Validation'], loc = 'upper left')
plt.show()

Test_Input = [cv2.imread(file, cv2.IMREAD_GRAYSCALE) for file in sorted(glob.glob("gdrive/My Drive/Image_512x512/*.png"))]
Test_Mask = [cv2.imread(file, cv2.IMREAD_GRAYSCALE) for file in sorted(glob.glob("gdrive/My Drive/Label_512x512/*.png"))]

Test_Input = np.array(Test_Input)
Test_Mask = np.array(Test_Mask)

Test_Mask = cv2.normalize(Test_Mask, None, alpha=1,beta=0, norm_type=cv2.NORM_MINMAX)

cv2.subtract(Train_Input[1],Train_Mask[1])



intersection = numpy.logical_and(result1, result2)
union = numpy.logical_or(result1, result2)
iou_score = numpy.sum(intersection) / numpy.sum(union)