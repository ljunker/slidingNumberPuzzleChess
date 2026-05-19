from flask import Blueprint, request

from . import gamestate

api = Blueprint("api", __name__)


@api.route("/newGame")
def new_game():
    return gamestate.start_new_game()


@api.route("/slidingMove", methods=["POST"])
def sliding_move():
    data = request.get_json(silent=True) or {}
    response = gamestate.apply_player_sliding_move(data.get("direction"), data.get("aiDepth"))

    if response is None:
        return {"error": "invalid sliding move"}, 400

    return response


@api.route("/pieceMoves", methods=["POST"])
def piece_moves():
    square = (request.get_json(silent=True) or {}).get("square")
    moves = gamestate.get_player_piece_moves(square)

    if moves is None:
        return {"error": "invalid square"}, 400

    return {
        "square": square,
        "moves": moves,
    }


@api.route("/pieceMove", methods=["POST"])
def piece_move():
    data = request.get_json(silent=True) or {}
    response = gamestate.apply_player_piece_move(data.get("from"), data.get("to"), data.get("aiDepth"))

    if response is None:
        return {"error": "invalid piece move"}, 400

    return response
