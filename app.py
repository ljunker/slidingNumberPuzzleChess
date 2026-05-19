from importlib import import_module

from flask import Flask

api = import_module("puzzle-chess.api").api
web = import_module("puzzle-chess.web").web

app = Flask(__name__)
app.register_blueprint(web)
app.register_blueprint(api)
