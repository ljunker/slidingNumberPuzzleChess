from flask import Blueprint, request

api = Blueprint("api", __name__)

game_state = None
FILES = "abcdefgh"
INACCESSIBLE_SQUARE = "x"
BLOCK_SIZE = 2
BOARD_SIZE = 8
MOVE_SOURCE_OFFSETS = {
    "up": (0, 2),
    "right": (-2, 0),
    "down": (0, -2),
    "left": (2, 0),
}


def create_initial_game_state():
    return {
        "board": [
            ["r", "n", "b", "q", "k", "b", "n", "r"],
            ["p", "p", "p", "p", "p", "p", "p", "p"],
            [None, None, None, None, None, None, None, None],
            [None, None, None, None, None, None, None, None],
            [
                None,
                None,
                INACCESSIBLE_SQUARE,
                INACCESSIBLE_SQUARE,
                None,
                None,
                None,
                None,
            ],
            [
                None,
                None,
                INACCESSIBLE_SQUARE,
                INACCESSIBLE_SQUARE,
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


def get_inaccessible_block(board):
    positions = []

    for rank_index, row in enumerate(board):
        for file_index, square in enumerate(row):
            if square == INACCESSIBLE_SQUARE:
                positions.append((file_index, rank_index))

    if len(positions) != BLOCK_SIZE * BLOCK_SIZE:
        return None

    files = [position[0] for position in positions]
    ranks = [position[1] for position in positions]
    min_file = min(files)
    max_file = max(files)
    min_rank = min(ranks)
    max_rank = max(ranks)

    if max_file - min_file != BLOCK_SIZE - 1 or max_rank - min_rank != BLOCK_SIZE - 1:
        return None

    return {
        "file": min_file,
        "rank": min_rank,
    }


def is_block_on_board(block):
    return (
            block["file"] >= 0
            and block["rank"] >= 0
            and block["file"] + BLOCK_SIZE <= BOARD_SIZE
            and block["rank"] + BLOCK_SIZE <= BOARD_SIZE
    )


def slide_block(state, direction):
    if direction not in MOVE_SOURCE_OFFSETS:
        return False

    inaccessible_block = get_inaccessible_block(state["board"])

    if inaccessible_block is None:
        return False

    file_offset, rank_offset = MOVE_SOURCE_OFFSETS[direction]
    source_block = {
        "file": inaccessible_block["file"] + file_offset,
        "rank": inaccessible_block["rank"] + rank_offset,
    }

    if not is_block_on_board(source_block):
        return False

    board = state["board"]
    source_values = []

    for rank_offset in range(BLOCK_SIZE):
        row = []

        for file_offset in range(BLOCK_SIZE):
            row.append(board[source_block["rank"] + rank_offset][source_block["file"] + file_offset])

        source_values.append(row)

    for rank_offset in range(BLOCK_SIZE):
        for file_offset in range(BLOCK_SIZE):
            target_rank = inaccessible_block["rank"] + rank_offset
            target_file = inaccessible_block["file"] + file_offset
            source_rank = source_block["rank"] + rank_offset
            source_file = source_block["file"] + file_offset

            board[target_rank][target_file] = source_values[rank_offset][file_offset]
            board[source_rank][source_file] = INACCESSIBLE_SQUARE

    return True


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


def game_state_response(state):
    return {
        "fen": game_state_to_fen(state),
        "inaccessible": board_to_inaccessible_squares(state["board"]),
        "turn": active_color_to_turn(state["active_color"]),
    }


@api.route("/newGame")
def new_game():
    global game_state

    game_state = create_initial_game_state()

    return game_state_response(game_state)


@api.route("/slidingMove", methods=["POST"])
def sliding_move():
    global game_state

    if game_state is None:
        game_state = create_initial_game_state()

    direction = (request.get_json(silent=True) or {}).get("direction")

    if not slide_block(game_state, direction):
        return {"error": "invalid sliding move"}, 400

    return game_state_response(game_state)
