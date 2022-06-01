import numpy as np


def generate_nth_order_markov_model(sentences, n=1):
    """
    sentences: list of statements to build markov model using
    n: integer of order of markov model. default = 1
    returns markov model dictionary {n length string tuples: string}
    """
    markov_model = {}
    for sentence in sentences:
        if sentence == "" or sentence == " ":
            continue
        sentence = sentence.split()
        for i in range(n):
            sentence.insert(0, "*S*")
        sentence.append("*E*")
        for i in range(0, len(sentence)-n):
            words = tuple(sentence[i:i+n])
            # check if words are in the markov model
            if words in markov_model.keys():
                # if they are, either increment the new word
                if sentence[i+n] in markov_model[words].keys():
                    markov_model[words][sentence[i+n]] += 1
                # or add the new word
                else:
                    markov_model[words][sentence[i+n]] = 1
            # if not, add to the markov model
            else:
                markov_model[words] = {}
                markov_model[words][sentence[i+n]] = 1
    return markov_model


def traverse_nth_order_markov_model(markov_model, n=1, seed=69420):
    """
    generate a read of markov model
    markov_model = dictionary of dictionaries
    n = order of model
    seed = seed for numpy
    return string
    """
    np.random.seed(seed)
    to_return = ""
    # start at the however many starts
    start = ("*S*",) * n
    item_counts = markov_model[start]
    total = 0
    for count in item_counts.keys():
        total += item_counts[count]
    item_probabilities = [markov_model[start][x]/total for x in markov_model[start].keys()]
    word = np.random.choice(list(item_counts.keys()), p=item_probabilities)
    while word != "*E*":
        to_return += (word + " ")
        start = list(start)
        start.pop(0)
        start.append(word)
        start = tuple(start)
        item_counts = markov_model[start]
        total = 0
        for count in item_counts.keys():
            total += item_counts[count]
        item_probabilities = [markov_model[start][x] / total for x in markov_model[start].keys()]
        word = np.random.choice(list(item_counts.keys()), p=item_probabilities)
    return to_return[:-1]
