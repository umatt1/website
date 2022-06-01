from markov_chainer import generate_nth_order_markov_model, traverse_nth_order_markov_model
import numpy as np
import tweepy
from flask import Flask, redirect, url_for, render_template, request, Blueprint

# stuff for tweepy
api_key = "WTa1zA2zS1uhVspg3JkVse7O7"
api_secret = "2X9EAiBCFZ7TbdX4LrF2jFQIPBdoXP9vfriC9JZisX7Jgcj5fI"
access_token = "3226209644-GNh9ZIUZOFcwWJo2xbyvL8ILo2kMjkgFuJH9SVp"
access_secret = "NYt3zyI9967KseNLwyX35x00Eyqjptq0PwXePEHuOMKN2"

auth = tweepy.OAuthHandler(api_key, api_secret)
auth.set_access_token(access_token, access_secret)

api = tweepy.API(auth)

synthetic_parrot = Blueprint('synthetic_parrot', __name__, template_folder='templates')
@synthetic_parrot.route("/", methods=["POST", "GET"])
def twitter_home():
    if request.method == "POST":
        id = request.form["id"]
        n = request.form["n"]
        return redirect(url_for("synthetic_parrot.twitter", id=id, n=n))
    else:
        return render_template("twitter.html")


@synthetic_parrot.route("/<id>/<n>")
def twitter(id, n):
    tweets = api.user_timeline(screen_name=id,
                               count=200,
                               include_rts=False,
                               tweet_mode='extended')
    string = ""
    for info in tweets:
        string += info.full_text + "\n"

    model = generate_nth_order_markov_model(string.split("\n"), n=int(n))
    to_display = ""
    for k in range(0,200):
        tweet = traverse_nth_order_markov_model(model, seed=np.random.randint(69420), n=int(n))
        to_display += "<p>" + tweet + "</p>"
    return f"<p>{to_display}</p>"