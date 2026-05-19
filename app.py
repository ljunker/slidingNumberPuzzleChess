from flask import Flask, render_template

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/newGame')
def new_game():
    fen = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
    return {'fen': fen,
            'inaccessible': ["a3", "a4", "b3", "b4"],
            'turn': 'white',
            }
