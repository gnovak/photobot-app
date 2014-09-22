from app import app

import os.path
import subprocess
import cPickle
import hashlib
import shutil

import numpy as np
import skimage as ski
import skimage.io
import sklearn as skl
import sklearn.svm

import werkzeug
from flask import render_template,request,redirect,url_for,send_from_directory

# import MySQLdb as mdb

allowed_extensions = set(['jpg'])
landing_upload_folder = "/Users/novak/Desktop/Insight/app-pbot/app/uploads-landing"
raw_upload_folder = "/Users/novak/Desktop/Insight/app-pbot/app/uploads-raw"
proc_upload_folder = "/Users/novak/Desktop/Insight/app-pbot/app/uploads-proc"

# db = mdb.connect(user="root", host="localhost", db="photobot", charset='utf8', 
#                  passwd='small irony yacht wok')

# load the data
with open('svm-fft-level-1.pkl') as ff:
    svm_l1 = cPickle.load(ff)

with open('svm-fft-level-2.pkl') as ff:
    svm_l2 = cPickle.load(ff)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in allowed_extensions

@app.route('/')

@app.route('/index')
def index():    
    user = { } 
    return render_template("index.html", title="Blah")
    
@app.route('/flask-upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = werkzeug.secure_filename(file.filename)
            file.save(os.path.join(landing_upload_folder, filename))
            return redirect(url_for('uploaded_file',
                                    filename=filename))

    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form action="" method=post enctype=multipart/form-data>
    <p><input type=file name=file>
    <input type=submit value=Upload>
    </form>
    '''

@app.route('/uploaded_file')
def uploaded_file():
    filename = request.args.get("filename")
    base, ext = os.path.splitext(filename)
    orig_filename = os.path.join(landing_upload_folder, filename)

    # Get 'permanent' filename from sha1 digest of file contents
    sha = hashlib.sha1()
    with open(orig_filename, 'rb') as ff:
        # Read the while file and digest it... would be good to be
        # more intelligent about this part....
        sha.update(ff.read(-1))
    hash_fn = sha.hexdigest()
    # Bail on hashes for now
    hash_fn = base

    # Move file out of landing zone
    raw_filename = os.path.join(raw_upload_folder, hash_fn + ext)

    shutil.copy(orig_filename, raw_filename)
    #shutil.move(orig_filename, raw_filename)

    # Add error handling:
    # try: subprocess.check_call(blah)
    # except CalledProcessError:
    # do something useful...

    # Downsample and crop
    #
    # Might want to resize rather than crop so that I actually have
    # all the pixels contributing.
    new_filename = os.path.join(proc_upload_folder, hash_fn + ext)
    downsize = ['convert', # use convert not mogrify to not overwrite orig
           raw_filename, # input fn
           '-resize', '150x150^', # ^ => min size
           '-gravity', 'center',  # do crop in center of photo
           '-crop', '150x150+0+0', # crop to 150x150 square
           new_filename] # output fn
    subprocess.call(downsize)

    # read it
    im = ski.io.ImageCollection([new_filename])
    # convert to vector
    vv = ims_to_rgb_fourier_mag(im, downsample=256)

    # classify it
    r1 = svm_l1.predict(vv)[0]
    r2 = svm_l2.predict(vv)[0]

    # No one sees this page, classification decision is gobbled up by java script.
    if r1 < 0.5: response = "bad"
    elif r1 > 0.5 and r2 < 0.5: response = "good"
    elif r1 > 0.5 and r2 > 0.5: response = "great"
    return response

@app.route('/uploads/<filename>')
def uploads(filename):
    return send_from_directory(raw_upload_folder,filename)

@app.route('/train', methods=['GET'])
def train():
    image = request.args.get("filename")
    prediction = request.args.get("picpickr")
    success = request.args.get("agree")
    # Stuff these into a sql database
    with db:
        cur = db.cursor()
        print "insert into responses (filename, prediction, correct) values ('%s' %s %s);" % (image, prediction, success)
        cur.execute("insert into responses (filename, prediction, correct) values ('%s', %s, %s);" % (image, prediction, success))

    return render_template("train.html")

def ims_to_rgb_vecs(ims, downsample=1):
    # include color, make vector in dumbest way possible
    # but want to make sure keep color data from the same pixels
    # downsample...
    # doing this in rgb, normalize, make floating point
    result = []
    for im in ims:
        if len(im.shape) == 3:
            vv = np.concatenate(((1/256.0)*im[:,:,0].reshape(-1)[::downsample],
                                 (1/256.0)*im[:,:,1].reshape(-1)[::downsample],
                                 (1/256.0)*im[:,:,2].reshape(-1)[::downsample]))
            result.append(vv)
        elif len(im.shape) == 2: # im is already B+W
            # do something dumb
            vv = np.concatenate(((1/256.0)*im.reshape(-1)[::downsample],
                                 (1/256.0)*im.reshape(-1)[::downsample],
                                 (1/256.0)*im.reshape(-1)[::downsample]))
            result.append(vv)
        else:
            raise ValueError
    return np.array(result)


def ims_to_rgb_fourier(ims, downsample=1):
    # downsample...
    result = []

    for im in ims:
        # if im is already bw, do something dumb to make it look like color
        if len(im.shape)==2:
            the_im = np.zeros(im.shape + (3,))
            the_im[:,:,0] = im
            the_im[:,:,1] = im
            the_im[:,:,2] = im
            im = the_im

        # Normalize pixel values to 0-1
        im = im/256.0

        rfft = np.fft.fft2(im[:,:,0])
        gfft = np.fft.fft2(im[:,:,1])
        bfft = np.fft.fft2(im[:,:,2])

        # keep things order unity w/ norm factor that shows up in ffts
        rfft /= rfft.size
        gfft /= gfft.size
        bfft /= bfft.size

        # turn into vector and downsample
        result.append(np.concatenate((rfft.reshape(-1)[::downsample],
                                      gfft.reshape(-1)[::downsample],
                                      bfft.reshape(-1)[::downsample])))

    return np.array(result)

def ims_to_rgb_fourier_mag(ims, downsample=1):
    result = ims_to_rgb_fourier(ims, downsample=downsample)
    return np.sqrt(result.real**2 + result.imag**2)
