from flask import Flask, redirect, url_for, render_template, request, Blueprint
from chess_guru import confidence
import requests
import math

# keep keys a secret
import json
with open('/etc/config.json') as config_file:
    config = json.load(config_file)
    weather_key = config.get('weather_key')
    key = weather_key

# used to "hash" the temperatures into a list
def index_of_likes(temperature):
    if int(temperature) < 0:
        return 2
    if int(temperature) < 10:
        return 4
    if int(temperature) < 20:
        return 6
    if int(temperature) < 30:
        return 8
    if int(temperature) < 40:
        return 10
    if int(temperature) < 50:
        return 12
    if int(temperature) < 60:
        return 14
    if int(temperature) < 70:
        return 16
    if int(temperature < 80):
        return 18
    if int(temperature < 90):
        return 20
    if int(temperature < 100):
        return 22
    else:
        return 24


# used to "hash" the temperatures into a list
def index_of_dislikes(temperature):
    if int(temperature) < 0:
        return 2 + 1
    if int(temperature) < 10:
        return 4 + 1
    if int(temperature) < 20:
        return 6 + 1
    if int(temperature) < 30:
        return 8 + 1
    if int(temperature) < 40:
        return 10 + 1
    if int(temperature) < 50:
        return 12 + 1
    if int(temperature) < 60:
        return 14 + 1
    if int(temperature) < 70:
        return 16 + 1
    if int(temperature < 80):
        return 18 + 1
    if int(temperature < 90):
        return 20 + 1
    if int(temperature < 100):
        return 22 + 1
    else:
        return 24 + 1


# to data
class michael_cera:
    def __init__(self, name, link, id, likes=0, dislikes=0):
        self._name = name
        self._link = link
        self._likes = likes
        self._dislikes = dislikes
        self._id = id

    def name(self, name=None):
        if name:
            self._name = name
        else:
            return self._name

    def link(self, link=None):
        if link:
            self._link = link
        else:
            return self._link

    def likes(self, likes=None):
        if likes:
            self._likes = likes
        else:
            return self._likes

    def dislikes(self, dislikes=None):
        if dislikes:
            self._dislikes = dislikes
        else:
            return self._dislikes

    def __lt__(self, other):
        thisone = confidence(self.likes(), self.dislikes())
        thatone = confidence(other.likes(), other.dislikes())
        return thisone < thatone

    def michael_id_sorter(self, other):
        return self._id < other._id

    def __str__(self):
        return f"{self._likes} likes, {self._dislikes} dislikes. {self._name}"


# return a list of michael ceras, list
def michael_cerafier(temperature, raining=False, snowing=False, windspeed=0, clouds=0):
    def index_of_likes(temperature):
        if int(temperature) < 0:
            return 2
        if int(temperature) < 10:
            return 4
        if int(temperature) < 20:
            return 6
        if int(temperature) < 30:
            return 8
        if int(temperature) < 40:
            return 10
        if int(temperature) < 50:
            return 12
        if int(temperature) < 60:
            return 14
        if int(temperature) < 70:
            return 16
        if int(temperature < 80):
            return 18
        if int(temperature < 90):
            return 20
        if int(temperature < 100):
            return 22
        else:
            return 24
    def index_of_dislikes(temperature):
        if int(temperature) < 0:
            return 2 + 1
        if int(temperature) < 10:
            return 4 + 1
        if int(temperature) < 20:
            return 6 + 1
        if int(temperature) < 30:
            return 8 + 1
        if int(temperature) < 40:
            return 10 + 1
        if int(temperature) < 50:
            return 12 + 1
        if int(temperature) < 60:
            return 14 + 1
        if int(temperature) < 70:
            return 16 + 1
        if int(temperature < 80):
            return 18 + 1
        if int(temperature < 90):
            return 20 + 1
        if int(temperature < 100):
            return 22 + 1
        else:
            return 24 + 1
    # from here on, we're going to define temperature as an index of a list
    temperatures = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    # store images of michael cera on a separate file
    # label, image link, likes, dislikes
    cera_file = open("ceras.txt")
    options = []
    datas = []
    index_of_likes = index_of_likes(temperature)
    index_of_dislikes = index_of_dislikes(temperature)
    for ind, cera in enumerate(cera_file):
        print(cera)
        cera = cera.split(',')
        for i in range(2, 26):
            cera[i] = int(cera[i])
        datas.append(cera)
        options.append(michael_cera(str(cera[0]), str(cera[1]), ind, likes=math.trunc(cera[index_of_likes]), dislikes=math.trunc(cera[index_of_dislikes])))
    cera_file.close()
    return options, datas


# flask blueprint
what2wear = Blueprint('what2wear', __name__, template_folder='templates')

# render home page
@what2wear.route("/", methods=['POST', 'GET'])
def weather_home():
    if request.method == "POST":
        location = request.form['location']
        return redirect(url_for("what2wear.weather", location=location))
    else:
        return render_template("what2wear.html")

# render results, process submission
@what2wear.route("/<location>/", methods=["POST", "GET"])
def weather(location):
    response = requests.get(f"https://api.weatherbit.io/v2.0/current?key={key}&postal_code={location}")
    text = response.text
    parsed_json = json.loads(text)

    city_name = parsed_json['data'][0]['city_name']

    weather = parsed_json['data'][0]['weather']['description']

    approximate_temperature = parsed_json['data'][0]['app_temp']
    fahrenheit = approximate_temperature * 1.8 + 32
    celsius = approximate_temperature

    ceras, datas = michael_cerafier(fahrenheit)
    ceras_by_id = ceras[:]
    ceras.sort()
    ceras = ceras[::-1]

    if request.method == 'POST':
        for i, cera in zip(range(len(ceras)), ceras):

            try: like = request.form[f'options{i}']
            except(KeyError):
                continue
            id = cera._id
            if like == 'like':
                datas[id][index_of_likes(fahrenheit)] += 1
            elif like == 'dislike':
                datas[id][index_of_dislikes(fahrenheit)] += 1


        # write the data
        opened_ceras = open('ceras.txt', 'w')
        for i in range(len(ceras)):
            for enumeration, item in enumerate(datas[i]):
                opened_ceras.write(str(item))
                if enumeration != len(datas[i])-1:
                    opened_ceras.write(",")
                else:
                    opened_ceras.write("\n")

        return redirect(url_for("what2wear.weather_home"))
    else:
        # display the html of the page (need to get the images, create like/dislike forms for each of them, display it)
        values = range(1, len(ceras))
        return render_template("michael_homescreen.html", ceras=ceras, values=values,
                               city=city_name, weather=weather, F=int(fahrenheit), C=celsius)


# basic api tests
if __name__ == '__main__':
    postal = "49085"
    response = requests.get(f"https://api.weatherbit.io/v2.0/current?key={key}&postal_code={postal}")
    print(f"Response status code: {response.status_code}")
    text = response.text
    parsed_json = json.loads(text)
    print("Loaded Json")
    print(parsed_json)

    city_name = parsed_json['data'][0]['city_name']
    print(f"city name: {city_name}")
