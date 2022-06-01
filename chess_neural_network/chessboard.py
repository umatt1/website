from flask import send_file, Blueprint, redirect, url_for, request, render_template, session
import chess
from chess_neural_network.network import Net
import torch
from chess_neural_network.utils import get_move, pieces, move_to_vector_on_board, arrowedLine
import io
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import random


chess_neural_network = Blueprint('chess_neural_network', __name__, template_folder='templates')
@chess_neural_network.route("/")
def chess_home():
    # redirect the user to the starting board
    session['fen'] = chess.STARTING_BOARD_FEN
    session['turn'] = 0
    return redirect(url_for("chess_neural_network.display_board"))

@chess_neural_network.route("/display", methods=['POST','GET'])
def display_board():
    if request.method == "POST":
        # process a move inputted
        game = chess.Board(session['fen'])
        turn = session['turn']
        try:
            move = chess.Move.from_uci(request.form['move'].lower())
        except(...):
            return redirect(url_for("chess_neural_network.display_board"))
        if move not in game.legal_moves:
            return redirect(url_for("chess_neural_network.display_board"))
        game.push(move)
        turn += 1
        if game.is_game_over():
            return "game ended. winner or draw"
        else:
            model_path = "chess_neural_network/saved_models/model.txt"
            model = Net()
            model.load_state_dict(torch.load(model_path))
            move = get_move(model, game.fen(), turn, debug=True)
            game.push(move)
            if game.is_game_over():
                return "game ended. loser or draw"
            else:
                session['fen'] = game.fen()
                session['turn'] = turn+1
                return redirect(url_for("chess_neural_network.display_board"))

    elif request.method == "GET":
        print("get request")
        game = chess.Board(session['fen'])
        return render_template("chess_neural_network.html", moves=game.legal_moves)


@chess_neural_network.route("/plot.png")
def render_board():
    pieces = {
        'p':1,
        'b':2,
        'n':3,
        'r':4,
        'q':5,
        'k':6,
        'P':7,
        'B':8,
        'N':9,
        'R':10,
        'Q':11,
        'K':12
    }
    pieces_images = {
        1: "graph/BPawn.png",
        2: "graph/BBishop.png",
        3: "graph/BKnight.png",
        4: "graph/BRook.png",
        5: "graph/BQueen.png",
        6: "graph/BKing.png",
        7: "graph/WPawn.png",
        8: "graph/WBishop.png",
        9: "graph/WKnight.png",
        10: "graph/WRook.png",
        11: "graph/WQueen.png",
        12: "graph/WKing.png"
    }
    board = chess.Board(session['fen'])
    # create an easier to read mapping
    mappings = board.piece_map()
    chess_board = np.zeros(64)
    for ind, piece in zip(mappings.keys(), mappings.values()):
        chess_board[ind] = pieces[piece.symbol()]
    chess_board = chess_board.reshape((8, 8))

    # fill board with pieces
    img = Image.open('chess_neural_network/graph/chessboard.png').convert("RGB")
    for row_ind, row in enumerate(chess_board):
        for col_ind, item in enumerate(row):
            #item = chess_board[row_ind, col_ind]
            if int(item) != 0:
                to_paste = Image.open("chess_neural_network/"+pieces_images[int(item)]).convert('RGB')
                img.paste(to_paste, (col_ind*80+10, 640-(row_ind+1)*80+10))
    # render the available moves
    move_fnt = ImageFont.truetype("chess_neural_network/arial.ttf", 15)
    moves = board.legal_moves
    for move in moves:
        vector = move_to_vector_on_board(move.uci())
        coord1 = (vector[0][0], 640-vector[0][1])
        coord2 = (vector[1][0], 640-vector[1][1])
        arrowedLine(img, coord1, coord2, width=5, color=(255,0,0))
    for move in moves:
        string_repr = move.uci()
        vector = move_to_vector_on_board(string_repr)
        drawer = ImageDraw.Draw(img)
        # add some randomness so text is less likely to impede other text
        buffer = random.randint(-30, 30)
        other_buffer = random.randint(-30, 10)
        coord = vector[1]
        coord = (coord[0]+other_buffer, 640-coord[1]+buffer)
        drawer.text(coord, string_repr, fill=(255,255,0), font=move_fnt)

    # make a basic key
    key_fnt = ImageFont.truetype("chess_neural_network/arial.ttf", 15)
    drawer = ImageDraw.Draw(img)
    for num in range(8):
        row_text = chr(97+num)
        col_text = str(num+1)
        row_coordinate = (80*num, 5)
        col_coordinate = (5, 640-(80*(num+1)))
        drawer.text(row_coordinate, row_text, fill=(0,0,255), font=key_fnt)
        drawer.text(col_coordinate, col_text, fill=(0,0,255), font=key_fnt)

    # return board to display
    output = io.BytesIO()
    img.save(output, 'PNG')
    output.seek(0)
    return send_file(output, as_attachment=False, mimetype='image/png')
