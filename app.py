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
from WordleBot import WordleBot
import datetime


# os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="/Users/sejaldua/Desktop/DESKTOP/for-fun/spotify-rewrapped/credentials.json"

orig_solutions = pd.read_csv('mystery_words.csv', header=None)[0].to_list()
orig_solutions = list(map(lambda x: x.upper(), orig_solutions))
solutions = list(map(lambda x: list(x), orig_solutions))
orig_herrings = pd.read_csv('guessable_words.csv', header=None)[0].to_list()
orig_herrings = list(map(lambda x: x.upper(), orig_herrings))
herrings = list(map(lambda x: list(x), orig_herrings))

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
    rec_df.sort_values(by=['avg_tile_score'], ascending=False)
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

def get_solution(bot, puzzle, archive_num=None, user_wordle=None):
    if puzzle == 'Current':
        bot.pick_todays_wordle()
    elif puzzle == 'From the Archives':
        bot.pick_wordle(archive_num)
    elif puzzle == 'Random':
        bot.pick_random_wordle()
    elif puzzle == 'Manual Entry':
        if not bot.check_valid(user_wordle):
            st.error('The Wordle you have entered is not valid')
        bot.set_wordle(user_wordle)
    solution = bot.wordle
    return solution.upper()


st.set_page_config(
    page_title = 'Wordle Wizard', 
    page_icon = '🥸'
)
score_system = {2: 'correct', 1: 'present', 0: 'absent'}
submitted = False
guesses = []
scores = []
bot = WordleBot()
mode = st.sidebar.selectbox('Enter a game mode', ['Wordle Assist 🤝', 'Post-Game Analysis 🥵'])

if mode == 'Wordle Assist 🤝':
    puzzle = st.sidebar.selectbox('Which puzzle do you want to solve?', ["Current", "From the Archives", "Random", "Manual Entry"])
    archive_num, user_wordle = None, None
    if puzzle == "From the Archives":
        today_puzzle_num = (datetime.datetime.now()-datetime.datetime(2021,6,19)).days
        archive_num = st.sidebar.number_input('Enter a puzzle number', min_value=0, max_value=today_puzzle_num, value=today_puzzle_num-1)
    elif puzzle == "Manual Entry":
        user_wordle = st.sidebar.text_input('Enter a 5-letter Wordle string')
    solution = get_solution(bot, puzzle, archive_num=archive_num, user_wordle=user_wordle)
    num_guesses = int(st.sidebar.number_input('How many guesses have you used so far?', min_value=1, max_value=6, value=1))
else:
    num_guesses = int(st.sidebar.number_input('How many guesses did you use?', min_value=1, max_value=6, value=6))
    solution = get_solution('Current')
print(solution)

# guess_col, col2, col3, col4, col5, col6 = st.columns([3, 1, 1, 1, 1, 1])
# score_cols = [col2, col3, col4, col5, col6]
# ABCDE = 'ABCDE'
with st.form("my_form"):
    for i in range(num_guesses):
        guesses.append(st.text_input('Guess ' + str(i+1)))
    # Every form must have a submit button.
    submitted = st.form_submit_button("ENTER")
    
if submitted:
    herring_pool = orig_herrings
    solution_pool = orig_solutions
    if not guess_validation(guesses):
        st.error('Please make sure your guesses are exactly 5 characters long')    
    for i, guess in enumerate(guesses):
        guess = guess.upper()
        if guess_validation(guesses):
            if mode == 'Wordle Assist 🤝':
                if guess in orig_herrings:
                    score = process_guess(guess, solution)
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
                        st.caption('Click on a column title / heuristic to sort in ascending or descending order and try out the top recommendation as your next answer!')
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