# -*- coding: utf-8 -*-
"""extract stories from games

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/125KH9KaYANHAXywwFQZ8zqJrT2PWjWbd

# Demo2: extract story from game log by using GPT-2 Summary

## Env setup

Install older TensorFlow version

Source code relies on older TensorFlow version. Installing TF v1.15 seems to fix the issue of *ModuleNotFoundError when training the model*. (Workaround found here: https://colab.research.google.com/notebooks/tensorflow_version.ipynb#scrollTo=8UvRkm1JGUrk)
"""

# Commented out IPython magic to ensure Python compatibility.
# %tensorflow_version 1.x
!pip -q install tensorflow==1.15 && pip -q install tensorflow-gpu==1.15
!pip -q install 'tensorflow-estimator<1.15.0rc0,>=1.14.0rc0' --force-reinstall

import tensorflow
import os
print(tensorflow.__version__)
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'   # disable all debugging logs

!git clone https://github.com/zhangabner/gpt-2/
os.chdir('gpt-2')
#Download model weights
# !python download_model.py 117M
# !python download_model.py 345M
# !python download_model.py 774M
!python download_model.py 117M # XL Model
!pip3 -q install -r /content/gpt-2/reqs.txt
#!pip3 -q install -r /content/gpt-2/requirements.txt

from google.colab import drive
drive.mount('/content/drive')

# os.mkdir("/content/drive/MyDrive/mlheart/stories")

# for world_size in (3,5,7):
#   for nb_objects in (3,5,7,9,11): 
#     for quest_length in (3,5,7):
#       for seed in (42,1234):
#         mainfold = "/content/drive/MyDrive/mlheart/"
#         gamefold = mainfold+"games/"
#         file_playlog = '/content/drive/MyDrive/mlheart/playlogs/'+gamename+'.play.txt'
#         f_r=open(file_playlog, 'r')
#         raw_text = fr.read() 

#         file_write = '/content/drive/MyDrive/mlheart/stories/'+gamename+'.story.txt'
#         fw = open(file_write,"w")

# read from S3  and save in S3      ai play textgames save as log
# read from S3  and save in S3      gpt2 read play log save as summary
# in comprehend  read summary  save as topic modeling

import os
os.chdir('src')

import fire
import json
import numpy as np
import tensorflow as tf

import model, sample, encoder
model_name='117M'
seed=None
nsamples=100 # 100 samples for each story
batch_size=1
length=300
temperature=1
top_k=0
top_p=1
models_dir='/content/gpt-2/models'

models_dir = os.path.expanduser(os.path.expandvars(models_dir))
if batch_size is None:
    batch_size = 1
assert nsamples % batch_size == 0

enc = encoder.get_encoder(model_name, models_dir)
hparams = model.default_hparams()
with open(os.path.join(models_dir, model_name, 'hparams.json')) as f:
    hparams.override_from_dict(json.load(f))

if length is None:
    length = hparams.n_ctx // 2
elif length > hparams.n_ctx:
    raise ValueError("Can't get samples longer than window size: %s" % hparams.n_ctx)

with tf.Session(graph=tf.Graph()) as sess:
    context = tf.placeholder(tf.int32, [batch_size, None])
    np.random.seed(seed)
    tf.set_random_seed(seed)
    output = sample.sample_sequence(
        hparams=hparams, length=length,
        context=context,
        batch_size=batch_size,
        temperature=temperature, top_k=top_k, top_p=top_p
    )

    saver = tf.train.Saver()
    ckpt = tf.train.latest_checkpoint(os.path.join(models_dir, model_name))
    saver.restore(sess, ckpt)
    for world_size in (3,5,7):
      for nb_objects in (3,5,7,9,11): 
        for quest_length in (5,7):
          for seed in (42,1234):
            mainfold = "/content/drive/MyDrive/mlheart/"
            gamefold = mainfold+"games/"
            gamename = "o"+str(world_size)+"r"+str(nb_objects)+"q"+str(quest_length)+"game"+str(seed)+".ulx"
            file_playlog = '/content/drive/MyDrive/mlheart/playlogs/'+gamename+'.play.txt'
            fr=open(file_playlog, 'r')
            raw_text = fr.read() 


            context_tokens = enc.encode(raw_text)
            generated = 0
            for j in range(nsamples // batch_size):
                out = sess.run(output, feed_dict={
                    context: [context_tokens for j in range(batch_size)]
                })[:, len(context_tokens):]
                for i in range(batch_size):
                    generated += 1
                    text = enc.decode(out[i])
                    print("=" * 40 + " SAMPLE " + str(generated) + " " + "=" * 40)
                    print(text)
                    file_write = '/content/drive/MyDrive/mlheart/stories/'+gamename+str(j)+str(i)+'.story.txt'
                    print (j,i,file_write )
                    fw = open(file_write,"w") 
                    fw.write(text)
            # print("=" * 80)