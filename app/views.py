from app import app

import os.path

import werkzeug
from flask import render_template,request,redirect,url_for

allowed_extensions = set(['jpg'])
upload_folder = "/Users/novak/Desktop/Insight/app-pbot/app/uploads"

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
    return "Got file " + blargh
