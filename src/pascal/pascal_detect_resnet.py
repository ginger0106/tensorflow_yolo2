"""Use trained resnet50 to detect"""

import tensorflow as tf
import numpy as np
import cv2

import os
import sys
FILE_DIR = os.path.dirname(__file__)
sys.path.append(FILE_DIR + '/../')

from slim_dir.nets import resnet_v1
import config as cfg
from img_dataset.pascal_voc import pascal_voc
from utils.timer import Timer
from yolo2_nets.net_utils import restore_resnet_tf_variables, show_yolo_detection
from yolo2_nets.tf_resnet import resnet_v1_50

slim = tf.contrib.slim

# TODO: make the image path to be user input
image_path = '/home/wenxi/Projects/tensorflow_yolo2/experiments/fig1.jpg'

IMAGE_SIZE = cfg.IMAGE_SIZE
S = cfg.S
B = cfg.B
# create database instance
imdb = pascal_voc('trainval')
NUM_CLASS = imdb.num_class
CKPTS_DIR = cfg.get_ckpts_dir('resnet50', imdb.name)

input_data = tf.placeholder(tf.float32, [None, 224, 224, 3])

# read in the test image
image = cv2.imread(image_path)
image = cv2.resize(image, (IMAGE_SIZE, IMAGE_SIZE))
image = image.astype(np.float32)
image = (image / 255.0) * 2.0 - 1.0
image = image.reshape((1, 224, 224, 3))


# get the right arg_scope in order to load weights
with slim.arg_scope(resnet_v1.resnet_arg_scope()):
    # net is shape [batch_size, S, S, 2048] if input size is 244 x 244
    net, end_points = resnet_v1_50(input_data, is_training=False)

net = slim.flatten(net)

fcnet1 = slim.fully_connected(net, 4096, scope='yolo_fc1')

# in this case 7x7x30
fcnet2 = slim.fully_connected(
    fcnet1, S * S * (5 * B + NUM_CLASS), scope='yolo_fc2')

grid_net = tf.reshape(fcnet2, [-1, S, S, (5 * B + NUM_CLASS)])

######################
# Initialize Session #
######################
tfconfig = tf.ConfigProto(allow_soft_placement=True)
tfconfig.gpu_options.allow_growth = True
sess = tf.Session(config=tfconfig)

# Load checkpoint
_ = restore_resnet_tf_variables(sess, imdb, 'resnet50', save_epoch=False)

predicts = sess.run(grid_net, {input_data: image})
show_yolo_detection(image_path, predicts, imdb)