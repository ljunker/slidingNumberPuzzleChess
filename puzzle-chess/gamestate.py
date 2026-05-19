FILES = "abcdefgh"
INACCESSIBLE_SQUARE = "x"
BLOCK_SIZE = 2
BOARD_SIZE = 8
PLAYER_COLOR = "w"
AI_COLOR = "b"
MIN_AI_DEPTH = 2
MAX_AI_DEPTH = 10
AI_SEARCH_WIDTH = 6
AI_NODE_LIMIT = 50000
PIECE_VALUES = {
    "p": 1,
    "n": 3,
    "b": 3,
    "r": 5,
    "q": 9,
    "k": 100,
}
PIECE_NOTATION = {
    "p": "",
    "n": "S",
    "b": "L",
    "r": "T",
    "q": "D",
    "k": "K",
}
SLIDE_NOTATION = {
    "up": "SL↑",
    "right": "SL→",
    "down": "SL↓",
    "left": "SL←",
}

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
        "move_history": [],
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


def apply_player_sliding_move(direction, ai_depth=MIN_AI_DEPTH):
    state = ensure_game_state()
    ai_depth = clamp_ai_depth(ai_depth)
    player_move = next(
        (move for move in get_sliding_moves(state, PLAYER_COLOR) if move["direction"] == direction),
        None,
    )

    if state["active_color"] != PLAYER_COLOR or player_move is None:
        return None

    slide_block(state, direction)
    state["halfmove_clock"] += 1
    state["active_color"] = AI_COLOR
    player_move["notation"] = format_move_notation(state, player_move, AI_COLOR)
    history_entry = append_move_history(state, player_move["notation"])
    ai_move = apply_ai_move(state, ai_depth)

    if ai_move is not None:
        history_entry["black"] = ai_move["notation"]

    return {
        **game_state_response(state),
        "move": player_move,
        "aiMove": ai_move,
        "aiDepth": ai_depth,
    }


def get_player_piece_moves(square):
    state = ensure_game_state()
    position = square_to_position(square)

    if position is None:
        return None

    piece = get_piece_at(state["board"], position)

    if piece is None or get_piece_color(piece) != PLAYER_COLOR or state["active_color"] != PLAYER_COLOR:
        return []

    return get_legal_piece_moves_for_position(state, position)


def apply_player_piece_move(from_square, to_square, ai_depth=MIN_AI_DEPTH):
    state = ensure_game_state()
    from_position = square_to_position(from_square)
    to_position = square_to_position(to_square)
    ai_depth = clamp_ai_depth(ai_depth)

    if from_position is None or to_position is None or state["active_color"] != PLAYER_COLOR:
        return None

    piece = get_piece_at(state["board"], from_position)

    if piece is None or get_piece_color(piece) != PLAYER_COLOR:
        return None

    if to_square not in get_legal_piece_moves_for_position(state, from_position):
        return None

    player_move = move_piece(state, from_position, to_position)
    state["active_color"] = AI_COLOR
    player_move["notation"] = format_move_notation(state, player_move, AI_COLOR)
    history_entry = append_move_history(state, player_move["notation"])
    ai_move = apply_ai_move(state, ai_depth)

    if ai_move is not None:
        history_entry["black"] = ai_move["notation"]

    return {
        **game_state_response(state),
        "move": player_move,
        "aiMove": ai_move,
        "aiDepth": ai_depth,
    }


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

    return get_legal_piece_moves_for_position(state, position)


def get_legal_piece_moves_for_position(state, position):
    piece = get_piece_at(state["board"], position)

    if piece is None or piece == INACCESSIBLE_SQUARE:
        return []

    color = get_piece_color(piece)
    moves = []

    for target_square in get_pseudo_piece_moves_for_position(state, position):
        target_position = square_to_position(target_square)
        next_state = copy_game_state(state)
        move_piece(next_state, position, target_position)

        if not is_in_check(next_state, color):
            moves.append(target_square)

    return moves


def get_pseudo_piece_moves_for_position(state, position):
    file_index, rank_index = position
    piece = get_piece_at(state["board"], position)

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


def get_all_piece_moves(state, color):
    moves = []

    for rank_index, row in enumerate(state["board"]):
        for file_index, piece in enumerate(row):
            if piece is None or piece == INACCESSIBLE_SQUARE or get_piece_color(piece) != color:
                continue

            from_square = position_to_square(file_index, rank_index)

            for to_square in get_legal_piece_moves_for_position(state, (file_index, rank_index)):
                target_position = square_to_position(to_square)
                target = get_piece_at(state["board"], target_position)
                moves.append(
                    {
                        "type": "piece",
                        "from": from_square,
                        "to": to_square,
                        "piece": piece,
                        "capture": target,
                    }
                )

    return moves


def get_sliding_moves(state, color=None):
    moves = []
    for direction in MOVE_SOURCE_OFFSETS:
        move = describe_sliding_move(state, direction)

        if move is not None and (color is None or is_legal_sliding_move(state, direction, color)):
            moves.append(move)

    return moves


def describe_sliding_move(state, direction):
    if direction not in MOVE_SOURCE_OFFSETS:
        return None

    inaccessible_block = get_inaccessible_block(state["board"])

    if inaccessible_block is None:
        return None

    file_offset, rank_offset = MOVE_SOURCE_OFFSETS[direction]
    source_block = {
        "file": inaccessible_block["file"] + file_offset,
        "rank": inaccessible_block["rank"] + rank_offset,
    }

    if not is_block_on_board(source_block):
        return None

    return {
        "type": "sliding",
        "direction": direction,
        "fromSquares": get_block_squares(source_block),
        "toSquares": get_block_squares(inaccessible_block),
    }


def is_legal_sliding_move(state, direction, color):
    next_state = copy_game_state(state)

    if not slide_block(next_state, direction):
        return False

    return not is_in_check(next_state, color)


def apply_ai_move(state, ai_depth=MIN_AI_DEPTH):
    moves = get_search_moves(state, AI_COLOR)

    if not moves:
        return None

    move = choose_ai_move(state, moves, ai_depth)

    if move["type"] == "piece":
        move = move_piece(state, square_to_position(move["from"]), square_to_position(move["to"]))
    else:
        slide_block(state, move["direction"])
        state["halfmove_clock"] += 1

    state["active_color"] = PLAYER_COLOR
    state["fullmove_number"] += 1
    move["notation"] = format_move_notation(state, move, PLAYER_COLOR)

    return move


def choose_ai_move(state, moves, ai_depth):
    ai_depth = clamp_ai_depth(ai_depth)
    candidates = limit_candidate_moves(moves, AI_COLOR)
    search_context = {
        "nodes": 0,
        "limit": AI_NODE_LIMIT,
        "cache": {},
    }
    best_move = candidates[0]
    best_score = float("-inf")

    for move in candidates:
        next_state = copy_game_state(state)
        apply_generated_move(next_state, move)
        score = minimax(
            next_state,
            ai_depth - 1,
            PLAYER_COLOR,
            float("-inf"),
            float("inf"),
            search_context,
        )

        if score > best_score:
            best_score = score
            best_move = move

    return best_move


def minimax(state, depth, color, alpha, beta, search_context):
    search_context["nodes"] += 1

    if depth <= 0 or search_context["nodes"] >= search_context["limit"]:
        return evaluate_state(state)

    cache_key = (board_to_fen(state["board"]), depth, color)

    if cache_key in search_context["cache"]:
        return search_context["cache"][cache_key]

    moves = limit_candidate_moves(get_search_moves(state, color), color)

    if not moves:
        if is_in_check(state, color):
            return -100000 if color == AI_COLOR else 100000

        return 0

    if color == AI_COLOR:
        value = float("-inf")

        for move in moves:
            next_state = copy_game_state(state)
            apply_generated_move(next_state, move)
            value = max(value, minimax(next_state, depth - 1, PLAYER_COLOR, alpha, beta, search_context))
            alpha = max(alpha, value)

            if beta <= alpha:
                break
    else:
        value = float("inf")

        for move in moves:
            next_state = copy_game_state(state)
            apply_generated_move(next_state, move)
            value = min(value, minimax(next_state, depth - 1, AI_COLOR, alpha, beta, search_context))
            beta = min(beta, value)

            if beta <= alpha:
                break

    search_context["cache"][cache_key] = value
    return value


def get_search_moves(state, color):
    return get_all_piece_moves(state, color) + get_sliding_moves(state, color)


def limit_candidate_moves(moves, color):
    sliding_moves = [move for move in moves if move["type"] == "sliding"]
    piece_moves = [move for move in moves if move["type"] == "piece"]
    ordered_piece_moves = sorted(piece_moves, key=lambda move: score_move_order(move, color), reverse=True)

    return ordered_piece_moves[:AI_SEARCH_WIDTH] + sliding_moves


def score_move_order(move, color):
    if move["type"] == "sliding":
        return 0.5

    capture = move["capture"]
    capture_score = PIECE_VALUES.get(capture.lower(), 0) * 10 if capture else 0
    piece_penalty = PIECE_VALUES.get(move["piece"].lower(), 0) * 0.1
    target_position = square_to_position(move["to"])
    center_score = 0

    if target_position is not None:
        file_index, rank_index = target_position
        center_score = 3.5 - max(abs(file_index - 3.5), abs(rank_index - 3.5))

    pawn_push_score = 0

    if move["piece"].lower() == "p" and target_position is not None:
        pawn_push_score = target_position[1] if color == AI_COLOR else BOARD_SIZE - 1 - target_position[1]

    return capture_score + center_score + pawn_push_score * 0.05 - piece_penalty


def evaluate_state(state):
    if is_checkmate(state, AI_COLOR):
        return -100000

    if is_checkmate(state, PLAYER_COLOR):
        return 100000

    score = 0

    for rank_index, row in enumerate(state["board"]):
        for file_index, piece in enumerate(row):
            if piece is None or piece == INACCESSIBLE_SQUARE:
                continue

            piece_score = PIECE_VALUES.get(piece.lower(), 0) * 100
            center_score = 3.5 - max(abs(file_index - 3.5), abs(rank_index - 3.5))

            if piece.lower() == "p":
                advancement = rank_index if piece.islower() else BOARD_SIZE - 1 - rank_index
                piece_score += advancement * 4

            piece_score += center_score

            if get_piece_color(piece) == AI_COLOR:
                score += piece_score
            else:
                score -= piece_score

    score += len(get_all_piece_moves(state, AI_COLOR)) * 0.5
    score -= len(get_all_piece_moves(state, PLAYER_COLOR)) * 0.5

    return score


def apply_generated_move(state, move):
    if move["type"] == "piece":
        return move_piece(state, square_to_position(move["from"]), square_to_position(move["to"]))

    slide_block(state, move["direction"])
    state["halfmove_clock"] += 1
    return move


def copy_game_state(state):
    return {
        "board": [row.copy() for row in state["board"]],
        "active_color": state["active_color"],
        "castling": state["castling"],
        "en_passant": state["en_passant"],
        "halfmove_clock": state["halfmove_clock"],
        "fullmove_number": state["fullmove_number"],
        "move_history": [entry.copy() for entry in state.get("move_history", [])],
    }


def clamp_ai_depth(ai_depth):
    try:
        depth = int(ai_depth)
    except (TypeError, ValueError):
        return MIN_AI_DEPTH

    return max(MIN_AI_DEPTH, min(MAX_AI_DEPTH, depth))


def move_piece(state, from_position, to_position):
    board = state["board"]
    from_file, from_rank = from_position
    to_file, to_rank = to_position
    piece = board[from_rank][from_file]
    capture = board[to_rank][to_file]

    board[to_rank][to_file] = promote_pawn_if_needed(piece, to_rank)
    board[from_rank][from_file] = None
    state["en_passant"] = "-"

    if piece.lower() == "p" or capture is not None:
        state["halfmove_clock"] = 0
    else:
        state["halfmove_clock"] += 1

    return {
        "type": "piece",
        "from": position_to_square(from_file, from_rank),
        "to": position_to_square(to_file, to_rank),
        "piece": piece,
        "capture": capture,
    }


def promote_pawn_if_needed(piece, rank_index):
    if piece == "P" and rank_index == 0:
        return "Q"

    if piece == "p" and rank_index == BOARD_SIZE - 1:
        return "q"

    return piece


def get_block_squares(block):
    squares = []

    for rank_offset in range(BLOCK_SIZE):
        for file_offset in range(BLOCK_SIZE):
            squares.append(
                position_to_square(block["file"] + file_offset, block["rank"] + rank_offset)
            )

    return squares


def append_move_history(state, white_notation):
    entry = {
        "number": state["fullmove_number"],
        "white": white_notation,
        "black": None,
    }
    state["move_history"].append(entry)
    return entry


def format_move_notation(state, move, opponent_color):
    if move["type"] == "sliding":
        notation = format_sliding_notation(move)
    else:
        notation = format_piece_notation(move)

    if is_checkmate(state, opponent_color):
        return f"{notation}#"

    if is_in_check(state, opponent_color):
        return f"{notation}+"

    return notation


def format_piece_notation(move):
    piece = move["piece"]
    prefix = PIECE_NOTATION[piece.lower()]
    separator = "x" if move["capture"] else "-"
    promotion = ""

    if piece.lower() == "p" and move["to"][1] in ["1", "8"]:
        promotion = "=D"

    return f"{prefix}{move['from']}{separator}{move['to']}{promotion}"


def format_sliding_notation(move):
    return f"{SLIDE_NOTATION[move['direction']]} {format_square_block(move['fromSquares'])}→{format_square_block(move['toSquares'])}"


def format_square_block(squares):
    positions = [square_to_position(square) for square in squares]
    files = [position[0] for position in positions]
    ranks = [position[1] for position in positions]

    return f"{position_to_square(min(files), min(ranks))}-{position_to_square(max(files), max(ranks))}"


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

        if (
                target is not None
                and target != INACCESSIBLE_SQUARE
                and target.lower() != "k"
                and is_enemy_piece(piece, target)
        ):
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
            elif target.lower() != "k" and is_enemy_piece(piece, target):
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

    return (
            target is None
            or (target != INACCESSIBLE_SQUARE and target.lower() != "k" and is_enemy_piece(piece, target))
    )


def is_checkmate(state, color):
    return is_in_check(state, color) and not has_legal_moves(state, color)


def is_stalemate(state, color):
    return not is_in_check(state, color) and not has_legal_moves(state, color)


def has_legal_moves(state, color):
    return bool(get_search_moves(state, color))


def is_in_check(state, color):
    king_position = find_king(state["board"], color)

    if king_position is None:
        return True

    return is_square_attacked(state, king_position, opposite_color(color))


def find_king(board, color):
    king = "K" if color == PLAYER_COLOR else "k"

    for rank_index, row in enumerate(board):
        for file_index, piece in enumerate(row):
            if piece == king:
                return file_index, rank_index

    return None


def is_square_attacked(state, position, by_color):
    board = state["board"]

    return (
            is_attacked_by_pawn(board, position, by_color)
            or is_attacked_by_knight(board, position, by_color)
            or is_attacked_by_king(board, position, by_color)
            or is_attacked_by_slider(board, position, by_color)
    )


def is_attacked_by_pawn(board, position, by_color):
    file_index, rank_index = position
    pawn = "P" if by_color == PLAYER_COLOR else "p"
    pawn_rank = rank_index + (1 if by_color == PLAYER_COLOR else -1)

    for file_offset in [-1, 1]:
        pawn_file = file_index + file_offset

        if is_on_board(pawn_file, pawn_rank) and board[pawn_rank][pawn_file] == pawn:
            return True

    return False


def is_attacked_by_knight(board, position, by_color):
    file_index, rank_index = position
    knight = "N" if by_color == PLAYER_COLOR else "n"

    for file_offset, rank_offset in KNIGHT_OFFSETS:
        attacker_file = file_index + file_offset
        attacker_rank = rank_index + rank_offset

        if is_on_board(attacker_file, attacker_rank) and board[attacker_rank][attacker_file] == knight:
            return True

    return False


def is_attacked_by_king(board, position, by_color):
    file_index, rank_index = position
    king = "K" if by_color == PLAYER_COLOR else "k"

    for file_offset, rank_offset in KING_OFFSETS:
        attacker_file = file_index + file_offset
        attacker_rank = rank_index + rank_offset

        if is_on_board(attacker_file, attacker_rank) and board[attacker_rank][attacker_file] == king:
            return True

    return False


def is_attacked_by_slider(board, position, by_color):
    file_index, rank_index = position

    for file_offset, rank_offset in ORTHOGONAL_OFFSETS:
        if ray_has_attacker(board, file_index, rank_index, file_offset, rank_offset, by_color, {"r", "q"}):
            return True

    for file_offset, rank_offset in DIAGONAL_OFFSETS:
        if ray_has_attacker(board, file_index, rank_index, file_offset, rank_offset, by_color, {"b", "q"}):
            return True

    return False


def ray_has_attacker(board, file_index, rank_index, file_offset, rank_offset, by_color, attacker_types):
    target_file = file_index + file_offset
    target_rank = rank_index + rank_offset

    while is_on_board(target_file, target_rank):
        piece = board[target_rank][target_file]

        if piece == INACCESSIBLE_SQUARE:
            return False

        if piece is not None:
            return get_piece_color(piece) == by_color and piece.lower() in attacker_types

        target_file += file_offset
        target_rank += rank_offset

    return False


def get_piece_at(board, position):
    file_index, rank_index = position
    return board[rank_index][file_index]


def get_piece_color(piece):
    return "w" if piece.isupper() else "b"


def opposite_color(color):
    return AI_COLOR if color == PLAYER_COLOR else PLAYER_COLOR


def is_enemy_piece(piece, target):
    return get_piece_color(piece) != get_piece_color(target)


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
    active_color = state["active_color"]
    check = is_in_check(state, active_color)
    legal_moves_available = has_legal_moves(state, active_color)
    checkmate = check and not legal_moves_available
    stalemate = not check and not legal_moves_available
    winner = None

    if checkmate:
        winner = "black" if active_color == PLAYER_COLOR else "white"

    return {
        "fen": game_state_to_fen(state),
        "inaccessible": board_to_inaccessible_squares(state["board"]),
        "turn": active_color_to_turn(active_color),
        "check": check,
        "checkmate": checkmate,
        "stalemate": stalemate,
        "winner": winner,
        "legalSlidingMoves": [move["direction"] for move in get_sliding_moves(state, active_color)],
        "moveHistory": state.get("move_history", []),
    }
