import os
from flask import Flask

__author__="jlon"
__date__ ="$Dec 1, 2012 11:50:19 AM$"

app = Flask(__name__)

@app.route('/')
def hello():
    return "Hello World"


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
