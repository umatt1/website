from flask import Flask, redirect, url_for, render_template, request, Blueprint
import requests
import json
from requests.structures import CaseInsensitiveDict

# for plotting
import base64
from io import BytesIO
from matplotlib.figure import Figure


# keep keys a secret
import json
with open('/etc/config.json') as config_file:
    config = json.load(config_file)
    clash_key = config.get('clash_key')

headers = CaseInsensitiveDict()
headers["Authorization"] = f"Bearer {clash_key}"

# flask blueprint
warweight = Blueprint('warweight', __name__, template_folder='templates')


def getMaxLevel(townHallLevel, builderHallLevel, troop):
    response = open("troopUpgradeStats.json")
    loaded = json.load(response)

    for upgrade in loaded:
        # skip upgradeables that aren't what we're looking for
        if upgrade["name"] != troop.name() or upgrade["village"] != troop.village():
            continue

        # even though this is in a for loop, we plan on executing this once
        # (ONLY when we find the correct troop)
        # we will be returning from in here after we find the maximum value
        # the maximum value is in ["upgrades"]["levels"]["hall-1"]
        if troop.village() == "home":
            return upgrade["levels"][townHallLevel-1]
        else:
            return upgrade["levels"][builderHallLevel-1]

    raise Exception(f"{troop.name()} not found in troopUpgradeStats.json")


# for filling data
class Upgradeable:
    def __init__(self, **kwargs):
        self._level = kwargs['level']
        self._max_level = kwargs['maxLevel']
        self._village = kwargs['village']
        self.name(kwargs['name'])

    def name(self, name=None):
        if name:
            if name == "Baby Dragon" and self.village() == "builderBase":
                self._name = "Baby Dragon (Night)"
            else:
                self._name = name
        return self._name

    def level(self, level=None):
        if level:
            self._level = level
        return self._level

    def max_level(self, max_level=None):
        if max_level:
            self._max_level = max_level
        return self._max_level

    def village(self, village=None):
        if village:
            self._village = village
        return self._village

    def difference(self):
        return self._max_level - self._level

supers = {"Super Barbarian", "Super Archer", "Super Wall Breaker", "Sneaky Goblin", "Super Giant", "Inferno Dragon",
          "Super Valkyrie", "Super Witch", "Ice Hound", "Super Wizard", "Super Minion", "Rocket Balloon"}

def grapher(upgradeables):
    heroes = upgradeables

    # graph heroes
    fig = Figure(figsize=(10,10))
    ax = fig.subplots()

    labels = [k.name() for k in heroes]
    current_levels = [int(k.level()) for k in heroes]
    max_levels = [int(k.max_level()) for k in heroes]

    width = 0.35
    ax.barh(labels, max_levels, width, label="Maximum Level")
    ax.barh(labels, current_levels, width, label="Current Level")
    ax.legend(loc='best', fontsize=10)

    # save graph
    buf = BytesIO()
    fig.savefig(buf, format="png")
    data = base64.b64encode(buf.getbuffer()).decode("ascii")
    return f'data:image/png;base64,{data}'


def categorizer(upgradeables):
    # take in a series of upgradeables, sort them into a dictionary with the .difference() function as the key
    dictionary = {}
    for upgrade in upgradeables:
        diff = upgrade.difference()
        if diff not in dictionary:
            dictionary[diff] = {upgrade.name()}
        else:
            dictionary[diff].add(upgrade.name())
    to_return = {}
    for i in sorted(dictionary):
        to_return[i] = dictionary[i]
    return to_return


# render home page
@warweight.route("/", methods=['POST', 'GET'])
def coc_home():
    if request.method == "POST":
        key = request.form['key']
        village = request.form['village']
        return redirect(url_for("warweight.coc", key=key, village=village))
    else:
        return render_template("clash.html")

# render results, process submission
@warweight.route("/<key>/<village>/", methods=["POST", "GET"])
def coc(key, village):
    # Correct the #
    if '#' in key:
        key = key.replace("#", "%23")
    else:
        key = "%23" + key

    # Scrape data
    response = requests.get(f"https://api.clashofclans.com/v1/players/{key}", headers=headers)
    text = response.text
    parsed_json = json.loads(text)

    # Get ready to parse data
    heroes = []
    troops = []
    spells = []


    # find max level for town hall
    townHallLevel = int(parsed_json["townHallLevel"])
    try: builderHallLevel = int(parsed_json["builderHallLevel"])
    except KeyError: builderHallLevel = 0

    # fill heroes
    for header in parsed_json['heroes']:
        header_dict = dict(header)
        item = Upgradeable(**header_dict)
        try:
            item.max_level(getMaxLevel(townHallLevel, builderHallLevel, item))
        except Exception:
            item.max_level(0)
        if item.village() != village and village != 'all':
            continue
        heroes.append(item)

    # fill troops
    for header in parsed_json['troops']:
        header_dict = dict(header)
        item = Upgradeable(**header_dict)
        if item.name() in supers:
            continue
        try:
            item.max_level(getMaxLevel(townHallLevel, builderHallLevel, item))
        except Exception:
            item.max_level(0)
        if item.village() != village and village != 'all':
            continue
        troops.append(item)

    # fill spells
    for header in parsed_json['spells']:
        header_dict = dict(header)
        item = Upgradeable(**header_dict)
        try:
            item.max_level(getMaxLevel(townHallLevel, builderHallLevel, item))
        except Exception:
            item.max_level(0)
        if item.village() != village and village != 'all':
            continue
        spells.append(item)

    # get categorized
    categorized_heroes = categorizer(heroes)
    categorized_troops = categorizer(troops)
    categorized_spells = categorizer(spells)

    # graph everything
    heroes = grapher(heroes)
    troops = grapher(troops)
    spells = grapher(spells)
    return render_template("clash_results.html", heroes=heroes, troops=troops, spells=spells,
                           categorized_heroes=categorized_heroes, categorized_troops=categorized_troops, categorized_spells=categorized_spells)


# basic api tests
if __name__ == '__main__':
    key = '#Y9UGURY0'
    village = 'all'
    # Correct the #
    if '#' in key:
        key = key.replace("#", "%23")
    else:
        key = "%23" + key

    # Scrape data
    response = requests.get(f"https://api.clashofclans.com/v1/players/{key}", headers=headers)
    text = response.text
    parsed_json = json.loads(text)
    for k in parsed_json["troops"]:
        print(k["name"], k["village"])