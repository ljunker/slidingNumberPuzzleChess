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

KNIGHT_OFFSETS = [
    (-1, -2),
    (1, -2),
    (-2, -1),
    (2, -1),
    (-2, 1),
    (2, 1),
    (-1, 2),
    (1, 2),
]

KING_OFFSETS = [
    (-1, -1),
    (0, -1),
    (1, -1),
    (-1, 0),
    (1, 0),
    (-1, 1),
    (0, 1),
    (1, 1),
]

DIAGONAL_OFFSETS = [
    (-1, -1),
    (1, -1),
    (-1, 1),
    (1, 1),
]

ORTHOGONAL_OFFSETS = [
    (0, -1),
    (-1, 0),
    (1, 0),
    (0, 1),
]

game_state = None


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


def start_new_game():
    global game_state

    game_state = create_initial_game_state()
    return game_state_response(game_state)


def ensure_game_state():
    global game_state

    if game_state is None:
        game_state = create_initial_game_state()

    return game_state


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
                inaccessible.append(position_to_square(file_index, rank_index))

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


def apply_sliding_move(direction):
    state = ensure_game_state()

    if not slide_block(state, direction):
        return None

    return game_state_response(state)


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


def get_piece_moves(square):
    state = ensure_game_state()
    position = square_to_position(square)

    if position is None:
        return None

    file_index, rank_index = position
    piece = state["board"][rank_index][file_index]

    if piece is None or piece == INACCESSIBLE_SQUARE:
        return []

    piece_type = piece.lower()

    if piece_type == "p":
        return get_pawn_moves(state["board"], file_index, rank_index, piece)

    if piece_type == "n":
        return get_offset_moves(state["board"], file_index, rank_index, piece, KNIGHT_OFFSETS)

    if piece_type == "b":
        return get_sliding_piece_moves(state["board"], file_index, rank_index, piece, DIAGONAL_OFFSETS)

    if piece_type == "r":
        return get_sliding_piece_moves(state["board"], file_index, rank_index, piece, ORTHOGONAL_OFFSETS)

    if piece_type == "q":
        return get_sliding_piece_moves(
            state["board"],
            file_index,
            rank_index,
            piece,
            DIAGONAL_OFFSETS + ORTHOGONAL_OFFSETS,
        )

    if piece_type == "k":
        return get_offset_moves(state["board"], file_index, rank_index, piece, KING_OFFSETS)

    return []


def get_pawn_moves(board, file_index, rank_index, piece):
    moves = []
    is_white = piece.isupper()
    direction = -1 if is_white else 1
    start_rank = 6 if is_white else 1
    next_rank = rank_index + direction

    if is_on_board(file_index, next_rank) and board[next_rank][file_index] is None:
        moves.append(position_to_square(file_index, next_rank))

        double_rank = rank_index + direction * 2
        if rank_index == start_rank and board[double_rank][file_index] is None:
            moves.append(position_to_square(file_index, double_rank))

    for file_offset in [-1, 1]:
        capture_file = file_index + file_offset

        if not is_on_board(capture_file, next_rank):
            continue

        target = board[next_rank][capture_file]

        if target is not None and target != INACCESSIBLE_SQUARE and is_enemy_piece(piece, target):
            moves.append(position_to_square(capture_file, next_rank))

    return moves


def get_offset_moves(board, file_index, rank_index, piece, offsets):
    moves = []

    for file_offset, rank_offset in offsets:
        target_file = file_index + file_offset
        target_rank = rank_index + rank_offset

        if can_move_to(board, target_file, target_rank, piece):
            moves.append(position_to_square(target_file, target_rank))

    return moves


def get_sliding_piece_moves(board, file_index, rank_index, piece, offsets):
    moves = []

    for file_offset, rank_offset in offsets:
        target_file = file_index + file_offset
        target_rank = rank_index + rank_offset

        while is_on_board(target_file, target_rank):
            target = board[target_rank][target_file]

            if target == INACCESSIBLE_SQUARE:
                break

            if target is None:
                moves.append(position_to_square(target_file, target_rank))
            elif is_enemy_piece(piece, target):
                moves.append(position_to_square(target_file, target_rank))
                break
            else:
                break

            target_file += file_offset
            target_rank += rank_offset

    return moves


def can_move_to(board, file_index, rank_index, piece):
    if not is_on_board(file_index, rank_index):
        return False

    target = board[rank_index][file_index]

    return target is None or (target != INACCESSIBLE_SQUARE and is_enemy_piece(piece, target))


def is_enemy_piece(piece, target):
    return piece.isupper() != target.isupper()


def is_on_board(file_index, rank_index):
    return 0 <= file_index < BOARD_SIZE and 0 <= rank_index < BOARD_SIZE


def square_to_position(square):
    if not isinstance(square, str) or len(square) != 2:
        return None

    file_name = square[0]
    rank_name = square[1]

    if file_name not in FILES or not rank_name.isdigit():
        return None

    rank = int(rank_name)

    if rank < 1 or rank > BOARD_SIZE:
        return None

    return FILES.index(file_name), BOARD_SIZE - rank


def position_to_square(file_index, rank_index):
    return f"{FILES[file_index]}{BOARD_SIZE - rank_index}"


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
