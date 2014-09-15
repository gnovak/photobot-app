from app import app

import os.path
import subprocess

import numpy as np
import skimage as ski
import skimage.io
import sklearn as skl
import sklearn.svm

import werkzeug
from flask import render_template,request,redirect,url_for

allowed_extensions = set(['jpg'])
upload_folder = "/Users/novak/Desktop/Insight/app-pbot/app/uploads"

# load the data
with open('demo-day-svm.pkl') as ff: 
    svm = cPickle.load(ff)

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
            file.save(os.path.join(upload_folder, filename))
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
    blargh = request.args.get("filename")    
    # downsize file
    ds_filename = 'ds-' + blargh
    base, ext = os.path.splitext(ds_filename)
    out_filename = base + '-0' + ext

    subprocess.call(['cp', os.path.join(upload_folder,blargh), 
                     os.path.join(upload_folder,ds_filename)])
    subprocess.call(['mogrify', '-thumbnail', 'x300', '-resize', '300x<', 
                     '-resize', '50%', '-crop', '150x150', '-gravity', 
                     'center', os.path.join(upload_folder,ds_filename)])
    # read it
    im = ski.io.ImageCollection([os.path.join(upload_folder, out_filename)])
    # convert to vector
    vv = ims_to_rgb_vecs(im,downsample=256)

    # classify it
    result = svm.predict(vv)[0]
    print result
    # say something amusing
    if result > 0.5 :
        resp = "pretty good!"
        respbool = "TRUE"
    else:
        resp = "lame!"
        respbool = "FALSE"
    # show the file
    url = '/uploads/' + blargh
    return render_template("response.html", resp=resp, respbool=respbool,
                           imageurl=url, filename=blargh)

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
