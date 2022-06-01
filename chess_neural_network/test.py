import chess
import chess.pgn
from chess_neural_network.network import Net
import torch
from chess_neural_network.utils import convert_to_array, Possible_States

print("loading model")
model_path = "saved_models/model.txt"
game = chess.Board()
model = Net()
model.load_state_dict(torch.load(model_path))

print("starting game")
turn = 0
while not game.is_game_over():
    if game.turn == chess.WHITE:
        print("white goes")
        print(game)
        # bot goes for white
        possible_states = Possible_States(game)
        moves = game.legal_moves
        maximum_state = None
        maximum_score = None
        for state in possible_states:
            mapping = torch.tensor(convert_to_array(state)).float()
            scoring = model.forward(mapping)
            if not maximum_score or scoring < maximum_score:
                maximum_score = scoring
                maximum_state = state
        for move in moves:
            game.push(move)
            if game.fen().split()[0] == maximum_state:
                break
            else:
                game.pop()
    elif game.turn == chess.BLACK:
        print("black goes")
        print(game)
        legal_moves = list(game.legal_moves)
        choice = None
        while not choice or chess.Move(choice) not in legal_moves:
            choice = input("pick a move (ex: e2e4)")
        game.push(chess.Move("choice"))
    else:
        print("bug get fucked")
    turn += 1
print(f"winner is {game.outcome()}")