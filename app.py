import time
from flask import Flask
from threading import Thread
from views import AliyunDK
from app.aliyundk import get_server

app = Flask(__name__)
app.register_blueprint(AliyunDK)
inited = False

@app.before_request
def init():
    global inited
    if not inited:
        inited = True
        get_server()




if __name__ == '__main__':
    app.run(host="0.0.0.0")
