#!/usr/bin/env python
from app import app

# How to get at code/data
# to load foo.py and app/bar.py, do this
#
# import foo
# from app import baz
#
# Beware, don't do "import app.baz" because this undoes Flask magic in
# creating the app object, causing the following line to fail.

app.run(debug = True)

