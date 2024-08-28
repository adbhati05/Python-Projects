from flask import Flask

# This is a very basic Flask application, all it does is create a webpage on the local host connection that writes out "Wsg baby boy".
TaskTracker = Flask(__name__)

@TaskTracker.route('/')
def index():
    return "Wsg baby boy"

if __name__ == "__main__":
    TaskTracker.run()