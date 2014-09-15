
from flask import Flask
app = Flask(__name__)
from app import views

# How to get at code/data
# to load foo.py and app/bar.py, do this
# 
# import foo  # somewhat mysteriously works
# import bar  # works
# from app import bar  # also works
