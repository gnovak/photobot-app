from app import app

@app.route('/')

@app.route('/index')
def index():    
    user = { } 
    return render_template("index.html", title="Blah")
    
