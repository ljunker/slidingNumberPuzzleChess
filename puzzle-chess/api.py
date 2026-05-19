from flask import Blueprint

api = Blueprint("api", __name__)

game_state = None
FILES = "abcdefgh"
INACCESSIBLE_SQUARE = "x"


def create_initial_game_state():
    return {
        "board": [
            ["r", "n", "b", "q", "k", "b", "n", "r"],
            ["p", "p", "p", "p", "p", "p", "p", "p"],
            [None, None, None, None, None, None, None, None],
            [None, None, None, None, None, None, None, None],
            [
                INACCESSIBLE_SQUARE,
                INACCESSIBLE_SQUARE,
                None,
                None,
                None,
                None,
                None,
                None,
            ],
            [
                INACCESSIBLE_SQUARE,
                INACCESSIBLE_SQUARE,
                None,
                None,
                None,
                None,
                None,
                None,
            ],
            ["P", "P", "P", "P", "P", "P", "P", "P"],
            ["R", "N", "B", "Q", "K", "B", "N", "R"],
        ],
        "active_color": "w",
        "castling": "KQkq",
        "en_passant": "-",
        "halfmove_clock": 0,
        "fullmove_number": 1,
    }


def board_to_fen(board):
    fen_rows = []

    for row in board:
        empty_count = 0
        fen_row = ""

        for square in row:
            if square is None or square == INACCESSIBLE_SQUARE:
                empty_count += 1
                continue

            if empty_count:
                fen_row += str(empty_count)
                empty_count = 0

            fen_row += square

        if empty_count:
            fen_row += str(empty_count)

        fen_rows.append(fen_row)

    return "/".join(fen_rows)


def board_to_inaccessible_squares(board):
    inaccessible = []

    for rank_index, row in enumerate(board):
        for file_index, square in enumerate(row):
            if square == INACCESSIBLE_SQUARE:
                inaccessible.append(f"{FILES[file_index]}{8 - rank_index}")

    return sorted(inaccessible, key=lambda square: (FILES.index(square[0]), int(square[1:])))


def game_state_to_fen(state):
    return " ".join(
        [
            board_to_fen(state["board"]),
            state["active_color"],
            state["castling"] or "-",
            state["en_passant"] or "-",
            str(state["halfmove_clock"]),
            str(state["fullmove_number"]),
        ]
    )


def active_color_to_turn(active_color):
    return "white" if active_color == "w" else "black"


@api.route("/newGame")
def new_game():
    global game_state

    game_state = create_initial_game_state()

    return {
        "fen": game_state_to_fen(game_state),
        "inaccessible": board_to_inaccessible_squares(game_state["board"]),
        "turn": active_color_to_turn(game_state["active_color"]),
    }
