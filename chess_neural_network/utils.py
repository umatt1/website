import chess.pgn
import chess
import numpy as np
import json
import requests
import io
import datetime
import pandas as pd
import torch
from PIL import Image, ImageDraw
import math
from copy import deepcopy


pieces = {
            'p': 0,
            'b': 1,
            'n': 2,
            'r': 3,
            'q': 4,
            'k': 5
        }
pieces_values = {
    'p' : 1,
    'b' : 3,
    'n' : 3,
    'r' : 5,
    'q' : 9,
    'k' : 50
}

def Possible_States(board):
    # given a board, this function will generate all the other boards possible
    possible_boards = {}
    legal_moves = board.legal_moves
    for move in legal_moves:
        new_board = board.copy()
        new_board.push(move)
        possible_boards[new_board.board_fen()] = 0
    return possible_boards


def PGN_To_Labelled_States(PGN, color="white"):
    '''
    given a PGN, open all possible moves (in the chess module)
    to figure out all possible states.

    then, assign the states chosen to a +1 label, states not chosen to a -1 label.
    this makes sense create a large list, then perform the above process move by move, extending the list after setting
    the labels
    '''
    if color == "white":
        color = 1
    else:
        color = -1
    encountered_states = {}
    game = chess.pgn.read_game(PGN)
    board = game.board()
    #for turn, move in enumerate(game.mainline_moves()):
    #    if color == turn % 2:
    #        rating_changes = Possible_States(board)
    #    else:
    #        rating_changes = {}
    #    board.push(move)
    #    if color == turn % 2:
    #        rating_changes[board.board_fen()] = +1
    #    for state in rating_changes.keys():
    #        if state not in encountered_states:
    #            encountered_states[state] = 0
    #        encountered_states[state] += rating_changes[state] * adder
    board_copy = board.copy()
    for move in game.mainline_moves():
        board_copy.push(move)
    winner = board_copy.outcome()
    if winner is None:
        # game didn't finish
        return {}
    elif winner.winner == chess.WHITE:
        winner = -1
        # loss
    elif winner.winner == chess.BLACK:
        winner = 1
        # win
    else:
        winner = 0
    for turn, move in enumerate(game.mainline_moves()):
        board.push(move)
        # we want only the results of black moves
        # 0 -> white goes
        # 1 -> black goes
        # 2 -> white goes
        # etc. so we want to look at the results of moves on ODD turns
        if turn % 2 == 0:
            continue
        if board.fen() not in encountered_states:
            encountered_states[board.fen()] = [winner]
        else:
            encountered_states[board.fen()].append(winner)
    return encountered_states


def convert_to_array(to_convert):
    # https://stackoverflow.com/questions/753954/how-to-program-a-neural-network-for-chess
    '''
    I would like to use an artificial neural network which should then evaluate a given position. The output should be a
    numerical value. The higher the value is, the better is the position for the white player.

    My approach is to build a network of 385 neurons: There are six unique chess pieces and 64 fields on the board.
    So forevery field we take 6 neurons (1 for every piece). If there is a white piece, the input value is 1. If there
    is a black piece, the value is p. And if there is no piece of that sort on that field, the value is 0. In
    addition to that there should be 1 neuron for the player to move. If it is White's turn, the input value is 1 and
    if it's Black's turn, the value is -1.
    '''
    # modify so the last neuron is actually the turn!
    fen = to_convert
    input_neurons = np.zeros((6,8,8))
    extra_layer = np.zeros((1,8,8))
    board = chess.Board(fen)
    mappings = board.piece_map()
    for ind, piece in zip(mappings.keys(), mappings.values()):
        val = 0
        if piece.color == chess.WHITE:
            val = 1
        elif piece.color == chess.BLACK:
            val = -1
        row = math.floor(ind / 8 )
        col = ind % 8
        val = val
        extra_layer[0][row][col] = val * pieces_values[piece.symbol().lower()]
        input_neurons[pieces[piece.symbol().lower()]][row][col] = val
    return torch.tensor(np.insert(input_neurons, 0, extra_layer, axis=0))


def confidence(ups, downs):
    return ups/(ups+downs)
    n = ups + downs
    if n == 0:
        return 0
    z = 1.00  #1.44 = 85%, 1.96 = 95%
    phat = float(ups) / n
    return (phat + z*z/(2*n) - z * math.sqrt((phat*(1-phat)+z*z/(4*n))/n))/(1+z*z/n)


def create_dataframe(id="blunder_master6969", months=12):
    current_month = int(datetime.datetime.now().strftime("%m"))
    current_year = 2000 + int(datetime.datetime.now().strftime("%y"))
    states = {}

    for i in range(int(months)):
        year = str(current_year)
        month = str(current_month)
        if len(month) == 1:
            month = "0" + month
        response = requests.get(f"https://api.chess.com/pub/player/{id}/games/{year}/{month}")
        to_iterate = json.loads(response.text)
        for game_ind, game in enumerate(to_iterate['games']):
            if 'pgn' not in game:
                continue
            if game['white']['username'] == id:
                color = 'white'
                continue
            elif game['black']['username'] == id:
                color = 'black'
            else:
                raise KeyError("none of the ids are good")
            new_states = PGN_To_Labelled_States(io.StringIO(game['pgn']), color=color)
            # keys are (fen, color turn)
            # values are if game was won or not
            for key, val in zip(new_states.keys(), new_states.values()):
                fen = key[0]
                color_played = key[1]
                wins_or_losses = val
                if key not in states:
                    states[key] = []
                states[key].extend(wins_or_losses)

            #for key, val in zip(new_states.keys(), new_states.values()):
            #    fen = key
            #    turns = val.keys()
            #    scores = val.values()
            #    for turn, score in zip(turns, scores):
            #        if (fen, turn) not in states:
            #            states[(fen, turn)] = (score, train_or_test[game_ind % 2])
            #        else:
            #            states[(fen, turn)] = (states[(fen, turn)][0] + score, states[(fen,turn)][1])

        if current_month == 1:
            current_month = 12
            current_year -= 1
        else:
            current_month -= 1
    train_or_test = ["train", "test"]
    t = 0
    states_copy = {}
    for key, val in zip(states.keys(), states.values()):
        #states[key] = (float(sum(states[key]))/float(len(states[key])), train_or_test[t%2])
        if len(states[key]) < 2:
            continue
        #print(f"unpopped {key}")
        white_wins = 0
        black_wins = 0
        ties = 0
        for item in states[key]:
            if item == 1:
                white_wins += 1
            elif item == -1:
                black_wins += 1
            elif item == 0:
                ties += 1
            else:
                raise KeyError
        states_copy[key] = (confidence(black_wins, white_wins), train_or_test[t%2])
        t+=1
    df = pd.DataFrame.from_dict(states_copy, orient="index", columns=["y", "split"])
    df.reset_index(inplace=True)
    df = df.rename(columns={'index': 'X'})
    return df


def get_move(model, fen, turn, color="black", debug=True):
    game = chess.Board(fen)
    possible_states = Possible_States(game)
    moves = game.legal_moves
    minimum_state = None
    minimum_score = None
    for state in possible_states:
        mapping = torch.tensor(convert_to_array(state)).float()
        scoring = model.forward(mapping)[0]
        print(scoring)
        # print scores if debugging
        if debug:
            for move in moves:
                game.push(move)
                if game.fen().split()[0] == state:
                    print(f"{move}:{scoring}")
                game.pop()
        if not minimum_score or scoring > minimum_score:
            minimum_score = scoring
            minimum_state = state
    for move in moves:
        game.push(move)
        if game.fen().split()[0] == minimum_state:
            return move
        else:
            game.pop()


def move_to_vector_on_board(move, board_dims=80):
    square1 = move[0:2]
    square2 = move[2:]
    col1 = ord(square1[0])-97
    row1 = int(square1[1])-1
    col2 = ord(square2[0])-97
    row2 = int(square2[1])-1
    return (col1*board_dims+.5*board_dims, row1*board_dims+.5*board_dims), \
           (col2*board_dims+.5*board_dims, row2*board_dims+.5*board_dims)


# stolen from https://stackoverflow.com/questions/63671018/how-can-i-draw-an-arrow-using-pil
def arrowedLine(im, ptA, ptB, width=1, color=(0,255,0)):
    """Draw line from ptA to ptB with arrowhead at ptB"""
    # Get drawing context
    draw = ImageDraw.Draw(im)
    # Draw the line without arrows
    draw.line((ptA,ptB), width=width, fill=color)

    # Now work out the arrowhead
    # = it will be a triangle with one vertex at ptB
    # - it will start at 95% of the length of the line
    # - it will extend 8 pixels either side of the line
    x0, y0 = ptA
    x1, y1 = ptB
    # Now we can work out the x,y coordinates of the bottom of the arrowhead triangle
    xb = 0.95*(x1-x0)+x0
    yb = 0.95*(y1-y0)+y0

    # Work out the other two vertices of the triangle
    # Check if line is vertical
    if x0==x1:
       vtx0 = (xb-5, yb)
       vtx1 = (xb+5, yb)
    # Check if line is horizontal
    elif y0==y1:
       vtx0 = (xb, yb+5)
       vtx1 = (xb, yb-5)
    else:
       alpha = math.atan2(y1-y0,x1-x0)-90*math.pi/180
       a = 8*math.cos(alpha)
       b = 8*math.sin(alpha)
       vtx0 = (xb+a, yb+b)
       vtx1 = (xb-a, yb-b)

    #draw.point((xb,yb), fill=(255,0,0))    # DEBUG: draw point of base in red - comment out draw.polygon() below if using this line
    #im.save('DEBUG-base.png')              # DEBUG: save

    # Now draw the arrowhead triangle
    draw.polygon([vtx0, vtx1, ptB], fill=color)
    return im

if __name__ == "__main__":
    # testing suites
    opened_pgn = open("data/Romixin_vs_blunder_master6969_2022.04.07.pgn")
    labelled_states = PGN_To_Labelled_States(opened_pgn)
    print(labelled_states)
    encountered_states = 0
    for key, value in zip(labelled_states.keys(), labelled_states.values()):
        if value == 1:
            encountered_states += 1
    opened_pgn.close()

    #for key in labelled_states.keys():
        #print(convert_to_array(key))

