from flask import Flask, session
from chess_neural_network.chessboard import chess_neural_network
from datetime import timedelta

app = Flask(__name__)
app.permanent_session_lifetime = timedelta(minutes=10)
app.secret_key = "secrecy"
app.register_blueprint(chess_neural_network)


if __name__ == "__main__":
    app.run(debug=True)