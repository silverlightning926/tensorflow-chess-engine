from keras.api.models import load_model, Model
import chess
import numpy as np
from tqdm import tqdm
import copy

from src.utils.encoding_utils import encode_board, encode_castling_rights, encode_to_move, encode_material_advantage, encode_move_count, encode_is_checked

from src.training._load_dataset import MAX_MOVES

model: Model = load_model('models/model.keras')

# Cache for legal moves
legal_moves_cache = {}

# Cache for game states
game_state_cache = {}

# Transposition table
transposition_table = {}


def get_legal_moves(board: chess.Board):
    board_key = board.fen()
    if board_key in legal_moves_cache:
        return legal_moves_cache[board_key]

    legal_moves = list(board.legal_moves)
    legal_moves_cache[board_key] = legal_moves
    return legal_moves


def update_game_state(board: chess.Board, game_state):
    encoded_board = encode_board(board)
    game_state.append(encoded_board)

    if len(game_state) > MAX_MOVES:
        game_state.pop(0)

    return game_state


def evaluate_board(game_state, color: chess.Color):
    game = list(game_state)

    for _ in range(MAX_MOVES - len(game)):
        game.append(np.zeros((8, 8, 12), dtype=np.float32))

    game = np.reshape(game, (1, MAX_MOVES, 8, 8, 12))

    prediction = model.predict(game, verbose=0, batch_size=1)
    prediction = prediction[0][0] if color == chess.WHITE else prediction[0][1]
    return np.clip(prediction, -1, 1)


def minimax(board: chess.Board, depth: int, alpha: float, beta: float, maximizing_player: bool, game_state):
    board_key = (board.fen(), depth, alpha, beta, maximizing_player)
    if board_key in transposition_table:
        return transposition_table[board_key]

    if depth == 0 or board.is_game_over():
        evaluation = evaluate_board(game_state, board.turn)
        transposition_table[board_key] = evaluation
        return evaluation

    legal_moves = get_legal_moves(board)

    if maximizing_player:
        max_eval = float('-inf')
        for move in legal_moves:
            board.push(move)
            updated_game_state = update_game_state(board, list(game_state))
            evaluation = minimax(board, depth - 1, alpha,
                                 beta, False, updated_game_state)
            board.pop()
            max_eval = max(max_eval, evaluation)
            alpha = max(alpha, evaluation)
            if beta <= alpha:
                break
        transposition_table[board_key] = max_eval
        return max_eval

    min_eval = float('inf')
    for move in legal_moves:
        board.push(move)
        updated_game_state = update_game_state(board, list(game_state))
        evaluation = minimax(board, depth - 1, alpha,
                             beta, True, updated_game_state)
        board.pop()
        min_eval = min(min_eval, evaluation)
        beta = min(beta, evaluation)
        if beta <= alpha:
            break
    transposition_table[board_key] = min_eval
    return min_eval


def minimax_root(board: chess.Board, depth: int, maximizing_player: bool, game_state):
    best_move = None
    best_eval = float('-inf') if maximizing_player else float('inf')
    legal_moves = get_legal_moves(board)

    for move in tqdm(legal_moves, desc="Finding best move", ascii=True, leave=True):
        board.push(move)
        updated_game_state = update_game_state(board, list(game_state))
        evaluation = minimax(board, depth - 1, float('-inf'),
                             float('inf'), not maximizing_player, updated_game_state)
        board.pop()
        if maximizing_player and evaluation > best_eval:
            best_eval = evaluation
            best_move = move
        elif not maximizing_player and evaluation < best_eval:
            best_eval = evaluation
            best_move = move

    return best_move


def minimax_move(board: chess.Board, depth: int, game_state):
    return minimax_root(board, depth, board.turn, game_state)


def main():
    board = chess.Board()
    game_state = []

    while not board.is_game_over():
        move = minimax_move(board, 2, game_state)
        if move is None:
            break  # No valid moves, must be a game over state
        board.push(move)
        game_state = update_game_state(board, game_state)
        print(board)
        print("===")

    print(board.result())
    print("===")
    print(f"fen: {board.fen()}")
    print("===")
    print(board)
    print("===")
    for move in board.move_stack:
        print(move)


if __name__ == '__main__':
    main()