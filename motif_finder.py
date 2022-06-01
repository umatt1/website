# functions to Gibbs sample
import numpy as np

# to make searching for bases easier
bases = {
    'A' : 0,
    'C' : 1,
    'G' : 2,
    'T' : 3,
    0 : 'A',
    1 : 'C',
    2 : 'G',
    3 : 'T'
}


def Profile(kmers):
    '''
    :param kmers: list of strings (k-mers) to build profile using
    :return: 4xk numpy matrix
    '''
    #import pdb; pdb.set_trace()
    # pseudocount of 1
    if kmers[0] != '':
        length = len(kmers[0])
        count = np.ones((4, len(kmers[0])))
    else:
        length = len(kmers[1])
        count = np.ones((4, len(kmers[1])))
    # go through each kmer
    for kmer in kmers:
        # count each base
        for index, base in enumerate(kmer):
            count[bases[base], index] += 1
    # turn count matrix into profile matrix
    sums = np.sum(count, axis=0)
    profile = np.zeros((4, length))
    for col in range(length):
        # count total items in row
        for row in range(4):
            profile[row, col] = count[row, col] / sums[col]
    return profile


def GetKmer(sequence, profile, k):
    kmers = {}
    total = 0.0
    # sliding window
    for i in range(len(sequence)-k+1):
        kmer = sequence[i:i+k]
        score = 1
        for index, base in enumerate(kmer):
            score = score * profile[bases[base], index]
        if kmer in kmers:
            kmers[kmer] = kmers[kmer] + score
        else:
            kmers[kmer] = score
        total += score
    # pick random kmer
    print(sequence, kmers)
    for kmer in kmers:
        kmers[kmer] = kmers[kmer] / total
    return np.random.choice(list(kmers.keys()), p=list(kmers.values()))


def Score(motifs):
    """
    :param motifs: list of strings (motifs)
    :return: number of unpopular bases
    """
    k = len(motifs[0])
    # get a count matrix
    count = np.zeros((4, k))
    for motif in motifs:
        # count each base
        for index, base in enumerate(motif):
            count[bases[base], index] += 1
    # find the most popular at each position
    max = count.max(axis=0)
    best = ""
    # go across positions
    for index in range(k):
        # go across bases
        for base in range(4):
            if count[base, index] == max[index]:
                best += bases[base]
                break
    # now get the score
    score = 0
    for motif in motifs:
        for index, base in enumerate(motif):
            if base != best[index]:
                score += 1
    return score


def GibbsSampler(dna_strands, k, N):
    '''
    :param dna_strands: list of strings (dna strands) to search for motifs in
    :param k: length of k-mer
    :param N: number of iterations of unchanging before convergence
    :return: best motifs, list of best scores each iteration, total iterations
    '''
    motifs_and_scores = {}
    t = len(dna_strands)
    # initialize motifs
    motif_indexes = np.zeros(t)
    motifs = []
    # get random motifs
    for id, strand in enumerate(dna_strands):
        index = np.random.randint(len(strand)-k+1)
        motif_indexes[id] = index
        motifs.append(strand[index:index+k])
    # save best motifs
    best_motifs = motifs.copy()
    best_scores = []
    # iterate
    iterations_without_change = 0
    best_score = -1
    while best_score != 0:
        print(iterations_without_change)
        if iterations_without_change == N:
            break
        # pick a random kmer to remove
        i = np.random.randint(t)
        motifs[i] = ""
        # generate profile
        profile = Profile(motifs)
        # get profile-randomly generated kmer in i-th sequence
        motifs[i] = GetKmer(dna_strands[i], profile, k)
        current_score = Score(motifs)
        if current_score < best_score or best_score == -1:
            best_motifs = motifs.copy()
            best_score = current_score
            motifs_and_scores[tuple(best_motifs)] = (best_score, iterations_without_change)
            iterations_without_change = 0
        else:
            iterations_without_change += 1
        best_scores.append(best_score)
    motifs_and_scores[tuple(best_motifs)] = (best_score, iterations_without_change)
    return best_motifs, best_scores, len(best_scores), motifs_and_scores


def Profile_no_pseudocount(kmers):
    '''
    :param kmers: list of strings (k-mers) to build profile using
    :return: 4xk numpy matrix
    '''
    #import pdb; pdb.set_trace()
    if kmers[0] != '':
        length = len(kmers[0])
        count = np.zeros((4, len(kmers[0])))
    else:
        length = len(kmers[1])
        count = np.zeros((4, len(kmers[1])))
    # go through each kmer
    for kmer in kmers:
        # count each base
        for index, base in enumerate(kmer):
            count[bases[base], index] += 1
    # turn count matrix into profile matrix
    sums = np.sum(count, axis=0)
    profile = np.zeros((4, length))
    for col in range(length):
        # count total items in row
        for row in range(4):
            profile[row, col] = count[row, col] / sums[col]
    return profile


def motif_choices(motif):
    if '|' not in motif:
        return motif
    else:
        choices = {}
        motif = list(motif)
        motif.append('*')
        motif.insert(0, '*')
        to_return = ""
        for index, character in enumerate(motif):
            # prevent falling off the end or adding the beginning
            if character == '*':
                continue
            # only add characters on either non choices or first char of each choice
            if motif[index-1] == '|' or character == '|':
                continue
            # do choices on character before the slash
            if motif[index + 1] == '|':
                choice1 = motif[index+2]
                choice2 = character
                to_return = to_return + np.random.choice([choice1, choice2])
            else:
                to_return = to_return + character
        motif = "".join(motif[1:-1])
        return to_return


# stuff to make a flask site
from flask import Flask, redirect, url_for, render_template, request, Blueprint
from matplotlib.figure import Figure
import base64
from io import BytesIO

# logomaker
import pandas as pd
import logomaker as lm

motifer = Blueprint('motifer', __name__, template_folder='templates')
@motifer.route("/", methods=["POST", "GET"])
def motif_finder_home():
    if request.method == "POST":
        motif = request.form["motif"]
        n = request.form["n"]
        extra_bases = request.form['extra-bases']
        strands = request.form['strands']
        return redirect(url_for("motifer.motif_finder", motif=motif, n=n, extra_bases=extra_bases, strands=strands))
    else:
        return render_template("motif_finder.html")

@motifer.route("/<motif>/<n>/<extra_bases>/<strands>")
def motif_finder(motif, n, extra_bases, strands):
    webpage = f"<h1>{motif}</h1>"
    webpage += "Your DNA strands:"

    strands_list = []
    motif = motif.upper()
    # generate random bases to insert motif into
    choices = ['A', 'T', 'G', 'C']
    # iterate through strands
    for strand in range(int(strands)):
        if int(extra_bases) != 0:
            # choose extra-base number bases
            dna = np.random.choice(choices, int(extra_bases))
            strands_list.append(''.join(dna))
            # insert motif into strand
            index = np.random.randint(int(extra_bases)+1)
            strands_list[-1] = strands_list[-1][0:index] + motif_choices(motif) + strands_list[-1][index:]
        else:
            # if no extra bases, strand is just the motif
            strands_list.append(motif_choices(motif))
        webpage += f"<p>{strands_list[-1]}</p>"
    k = len(motif_choices(motif))
    print(motif_choices(motif))
    print(strands_list, k, int(n))
    best_motifs, best_scores, iterations, motifs_and_scores = GibbsSampler(strands_list, k, int(n))

    # logomaker stuff
    profile = Profile_no_pseudocount(best_motifs)
    profile = np.rot90(profile, 3)
    profile = pd.DataFrame(profile, columns=['T', 'G', 'C', 'A'])
    logo = lm.Logo(profile, font_name='Arial Rounded MT Bold')

    # graph scores over time
    fig = Figure()
    ax = fig.subplots()
    ax.plot(best_scores)
    ax.set_xlabel("iteration")
    ax.set_ylabel("best score found")
    ax.set_title("Best Score Over Iterations")
    buf = BytesIO()
    fig.savefig(buf, format="png")
    data = base64.b64encode(buf.getbuffer()).decode('ascii')
    webpage += f"<img src='data:image/png;base64,{data}'/></img>"

    # save logo
    ax2 = logo.ax
    buf2 = BytesIO()
    ax2.figure.savefig(buf2, format='png')
    data2 = base64.b64encode(buf2.getbuffer()).decode('ascii')
    webpage += f"<img src='data:image/png;base64,{data2}'/></img>"

    webpage += f"<h1>Final score: </h1>"
    webpage += f"<p>{best_scores[-1]}</p>"
    webpage += f"<h1>Final motifs: </h1>"
    for motif in best_motifs:
        webpage += f"<p>{motif}</p>"
    webpage += f"<h1>Motif cycles:</h1>"
    for motif_list in motifs_and_scores:
        score = list(motifs_and_scores[motif_list])
        webpage += f"<p>{motif_list} -> Score: {score[0]}, Iterations kept: {score[1]}</p>"
    return webpage


@motifer.route("/custom/", methods=["POST", "GET"])
def custom_motif_finder_home():
    if request.method == "POST":
        motifs = request.form["text"]
        k = request.form["k"]
        n = request.form["n"]
        return redirect(url_for("motifer.custom_motif_finder", motifs=motifs, k=k, n=n))
    else:
        return render_template("custom_motif_finder.html")


@motifer.route("/custom/<motifs>/<k>/<n>")
def custom_motif_finder(motifs, k, n):
    motifs = motifs.split("|")
    k = int(k)
    motifs = [x for x in motifs if x != ""]

    best_motifs, best_scores, iterations, motifs_and_scores = GibbsSampler(motifs, k, int(n))
    webpage = "<p>DNA strands:</p>"
    for motif in motifs:
        webpage += f"<p>{motif}</p>"

    # logomaker stuff
    profile = Profile_no_pseudocount(best_motifs)
    profile = np.rot90(profile, 3)
    profile = pd.DataFrame(profile, columns=['T', 'G', 'C', 'A'])
    logo = lm.Logo(profile, font_name='Arial Rounded MT Bold')

    # graph scores over time
    fig = Figure()
    ax = fig.subplots()
    ax.plot(best_scores)
    ax.set_xlabel("iteration")
    ax.set_ylabel("best score found")
    ax.set_title("Best Score Over Iterations")
    buf = BytesIO()
    fig.savefig(buf, format="png")
    data = base64.b64encode(buf.getbuffer()).decode('ascii')
    webpage += f"<img src='data:image/png;base64,{data}'/></img>"

    # save logo
    ax2 = logo.ax
    buf2 = BytesIO()
    ax2.figure.savefig(buf2, format='png')
    data2 = base64.b64encode(buf2.getbuffer()).decode('ascii')
    webpage += f"<img src='data:image/png;base64,{data2}'/></img>"

    webpage += f"<h1>Final score: </h1>"
    webpage += f"<p>{best_scores[-1]}</p>"
    webpage += f"<h1>Final motifs: </h1>"
    for motif in best_motifs:
        webpage += f"<p>{motif}</p>"
    webpage += f"<h1>Motif cycles:</h1>"
    for motif_list in motifs_and_scores:
        score = list(motifs_and_scores[motif_list])
        webpage += f"<p>{motif_list} -> Score: {score[0]}, Iterations kept: {score[1]}</p>"
    return webpage