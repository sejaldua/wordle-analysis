from re import S
import streamlit as st
import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
from collections import Counter
import collections
import string
import numpy as np
import random
from tqdm.auto import tqdm  # for notebooks
tqdm.pandas()
import os
os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="/Users/sejaldua/Desktop/DESKTOP/for-fun/spotify-rewrapped/credentials.json"

orig_solutions = pd.read_csv('mystery_words.csv', header=None)[0].to_list()
orig_solutions = list(map(lambda x: x.upper(), orig_solutions))
solutions = list(map(lambda x: list(x), orig_solutions))
orig_herrings = pd.read_csv('guessable_words.csv', header=None)[0].to_list()
orig_herrings = list(map(lambda x: x.upper(), orig_herrings))
herrings = list(map(lambda x: list(x), orig_herrings))

solution = 'PROXY'

def detect_text(uploaded_file):
    """Detects text in the file."""
    from google.cloud import vision
    import io
    client = vision.ImageAnnotatorClient()

    if uploaded_file is not None:
        # To read file as bytes:
        bytes_data = uploaded_file.getvalue()

    image = vision.Image(content=bytes_data)

    response = client.text_detection(image=image)
    texts = response.text_annotations
    print(texts)

    if response.error.message:
        raise Exception(
            '{}\nFor more info on error messages, check: '
            'https://cloud.google.com/apis/design/errors'.format(
                response.error.message))

def process_guess(herring, solution):
    score = []
    for i, letter in enumerate(herring):
        # right letter, right place
        if herring[i] == solution[i]:
            score.append(2)
        # right letter, wrong place
        elif letter in solution:
            score.append(1)
        # wrong letter, wrong place
        else:
            score.append(0)
    return score

def filter_list(pool, guess, score):
    for i, char in enumerate(guess):
        if score[i] == 2:
            pool = [word for word in pool if word[i] == char]
        elif score[i] == 1:
            pool = [word for word in pool if char in word]
        else:
            pool = [word for word in pool if char not in word]
    return pool

color_map = {2: 'green', 1: 'yellow', 0: 'red'}

def simulate_round(guess, solution, herring_df, solution_pool):
    score = process_guess(guess, solution)
    # colored_guess = "".join([f"[{color_map[num]}]{char}[/{color_map[num]}]" for num, char in zip(score, guess)])
    print(f"{guess} (guess) | {solution} (solution)")
    if guess == solution:
        return True
    solution_pool = filter_list(solution_pool, guess, score)
    herring_pool = filter_list(list(herring_df['herring']), guess, score)
    if guess in herring_pool: herring_pool.remove(guess)
    new_herring_df = herring_df.copy()
    new_herring_df = new_herring_df[new_herring_df.herring.isin(herring_pool)]
    # re-run simulation to get new heuristic scoring metrics
    new_herring_df['greens'], new_herring_df['yellows'], new_herring_df['sum'] = zip(*new_herring_df['herring'].map(lambda x: simulate_guess_for_all_solutions(x, solution_pool)))
    return solution_pool, new_herring_df

color_map = {2: 'green', 1: 'yellow', 0: 'grey'}
css = """
<style type='text/css'>
green {
    color: #00ff00;
}
yellow {
    color: #FFFF00;
}
grey {
    color: #808080;
}
white {
    color: #fff;
}
</style>
""" 

def get_html(type, str_):
    return """<%(type)s>%(str)s</%(type)s>""" % {'type': type, 'str': str_ }

def get_letter_map_fig(pool):
    # print(len([word for word in pool if word.startswith('A')]))
    pool = list(map(lambda x: list(x), pool))
    letter_map = pd.DataFrame(pool)
    letter_map.columns = ['1', '2', '3', '4', '5']
    counters = [Counter(letter_map[str(i+1)]) for i in range(len(letter_map.columns))]
    for i, counter in enumerate(counters):
        zero_cntr = Counter({uppercase: 0 for uppercase in string.ascii_uppercase if uppercase not in counters[i]})
        counters[i].update(zero_cntr)
        counters[i] = collections.OrderedDict(sorted(counters[i].items(), key=lambda pair: pair[0]))
    fig = plt.figure(figsize=(20, 5))
    num_letters = pd.DataFrame(counters)
    sns.heatmap(num_letters, xticklabels=list(string.ascii_uppercase), yticklabels=list(range(1,6)), cmap=sns.color_palette("light:b", as_cmap=True))
    return fig

def get_best_next_word(herring_pool):
    best_herring_df = pd.read_csv('./all_herrings_all_heuristics.csv')
    rec_df = best_herring_df.copy()
    rec_df = rec_df[rec_df.herring.isin(herring_pool)]
    rec_df.sort_values(by=['avg_info_gain'], ascending=False)
    return rec_df

def guess_validation(guesses):
    for guess in guesses:
        if not len(guess) == 5:
            return False
    return True

def score_validation(scores):
    for score in scores:
        for char in score:
            try:
                if int(char) >= 0 and int(char) <= 2:
                    pass
                else:
                    return False
            except:
                return False
    return True
        
def score_transformation(scores):
    return [list(map(int, score)) for score in scores]

# set custom font
system_fonts = matplotlib.font_manager.findSystemFonts(fontpaths='/Users/sejaldua/Library/Fonts/', fontext='ttf')
font_list = matplotlib.font_manager.createFontList(system_fonts)
matplotlib.font_manager.fontManager.ttflist.extend(font_list)
# print([f.name for f in matplotlib.font_manager.fontManager.ttflist])
plt.rcParams['font.family'] = 'Circular Pro Book'
plt.rcParams['font.size'] = 15

# uploaded_file = st.file_uploader("Choose a file")
# go = st.sidebar.button('Analyze Wordle Strategy!')
# if go:
#     detect_text(uploaded_file)

score_system = {2: 'correct', 1: 'present', 0: 'absent'}
submitted = False
guesses = []
scores = []
mode = st.sidebar.selectbox('Enter a game mode', ['Wordle Assist', 'Post-Game Analysis'])
if mode == 'Wordle Assist':
    num_guesses = int(st.sidebar.number_input('How many guesses have you used?', min_value=1, max_value=6, value=6))
else:
    num_guesses = int(st.sidebar.number_input('How many guesses did you use?', min_value=1, max_value=6, value=6))
    solution = st.sidebar.text_input('What was the Wordle solution today?')

guess_col, col2, col3, col4, col5, col6 = st.columns([3, 1, 1, 1, 1, 1])
score_cols = [col2, col3, col4, col5, col6]
with st.form("my_form"):
    if mode == 'Wordle Assist':
        with guess_col:
            for i in range(num_guesses):
                guesses.append(st.text_input('Guess ' + str(i+1)))
        for i in range(num_guesses):
            guess_score = []
            for j in range(5):
                with score_cols[j]:
                    guess_score.append(st.text_input('Score ' + str(i+1)+str(j+1)))
            scores.append(guess_score)
                        
    else:
        for i in range(num_guesses):
            guesses.append(st.text_input('Guess ' + str(i+1)))
    # Every form must have a submit button.
    submitted = st.form_submit_button("ENTER")
    
if submitted:
    herring_pool = orig_herrings
    solution_pool = orig_solutions
    if not guess_validation(guesses):
        st.error('Please make sure your guesses are exactly 5 characters long')    
    if mode == 'Wordle Assist':
        if not score_validation(scores):
            st.error('Please make sure your scores are all integers (0, 1, or 2')
        else:
            scores = score_transformation(scores)
    else:
        if solution == "":
            st.error("Please enter today's Wordle solution")
    for i, guess in enumerate(guesses):
        guess = guess.upper()
        if guess_validation(guesses):
            if mode == 'Wordle Assist':
                if guess in orig_herrings:
                    score = scores[i]
                    st.write("".join([get_html(color_map[num], char) for num, char in zip(score, guess)]) + css, unsafe_allow_html=True)
                    prev_h_size = len(herring_pool)
                    prev_s_size = len(solution_pool)
                    # print("prev size", prev_h_size, prev_s_size)
                    herring_pool = filter_list(herring_pool, guess, score)
                    print(len(herring_pool))
                    solution_pool = filter_list(solution_pool, guess, score)
                    with st.expander('Get strategic recommendations'):
                        st.write("".join([get_html(color_map[num], f"{score.count(num)} {score_system[num]}<br/>") + " " for num in score_system.keys()]) + css, unsafe_allow_html=True)
                        st.progress(round(((prev_h_size - len(herring_pool))/prev_h_size)*100))
                        st.write(str(len(herring_pool)) + "  guesses remaining")
                        st.pyplot(get_letter_map_fig(herring_pool))
                        st.write(get_best_next_word(herring_pool))
                elif guess == "":
                    pass
                else:
                    print(guess)
                    st.warning('Sorry... your guess is not in our archive of possible guesses')
            else:
                score = process_guess(guess, solution)
                st.write("".join([get_html(color_map[num], char) for num, char in zip(score, guess)]) + css, unsafe_allow_html=True)
                if guess in orig_herrings:
                    prev_h_size = len(herring_pool)
                    prev_s_size = len(solution_pool)
                    # print("prev size", prev_h_size, prev_s_size)
                    herring_pool = filter_list(herring_pool, guess, score)
                    print(len(herring_pool))
                    solution_pool = filter_list(solution_pool, guess, score)
                    with st.expander('See analysis'):
                        st.write("".join([get_html(color_map[num], f"{score.count(num)} {score_system[num]}<br/>") + " " for num in score_system.keys()]) + css, unsafe_allow_html=True)
                        st.progress(round(((prev_h_size - len(herring_pool))/prev_h_size)*100))
                        st.write("eliminated " + str((prev_h_size - len(herring_pool))) + " / " + str(prev_h_size) + " guesses")
                        # st.write(str(len(solution_pool)) + " / " + str(prev_s_size) + " solutions remaining")
                        st.pyplot(get_letter_map_fig(herring_pool))
                        # st.write(get_best_next_word(herring_pool).head())
                elif guess == "":
                    st.warning('Perhaps you used less guesses than you have specified')
                else:
                    print(guess)
                    st.warning('Sorry... your guess is not in our archive of possible guesses')