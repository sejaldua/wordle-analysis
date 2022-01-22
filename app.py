import streamlit as st
import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter
import string
import numpy as np
import random
from tqdm.auto import tqdm  # for notebooks
tqdm.pandas()

orig_solutions = pd.read_csv('mystery_words.csv', header=None)[0].to_list()
orig_solutions = list(map(lambda x: x.upper(), orig_solutions))
solutions = list(map(lambda x: list(x), orig_solutions))
orig_herrings = pd.read_csv('guessable_words.csv', header=None)[0].to_list()
orig_herrings = list(map(lambda x: x.upper(), orig_herrings))
herrings = list(map(lambda x: list(x), orig_herrings))

solution = 'PROXY'

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

def get_html(type, str_):
    return """<%(type)s>%(str)s</%(type)s>""" % {'type': type, 'str': str_ }

css = """
<style type='text/css'>
html {
  font-family: Courier;
}
green {
  color: #00ff00;
}
yellow {
  color: #FFFF00;
}
grey {
  color: #808080;
}
</style>
""" 

num_guesses = st.sidebar.number_input('How many guesses did you need today?', min_value=1, max_value=6, value=6)
solution = st.sidebar.text_input('What was the Wordle solution today?')
# go = st.sidebar.button('Analyze Wordle Strategy!')
submitted = False
guesses = []

with st.form("my_form"):
    for i in range(num_guesses):
        guesses.append(st.text_input('Guess ' + str(i+1)))
    # Every form must have a submit button.
    submitted = st.form_submit_button("ENTER")
    
if submitted:
    for guess in guesses:
        score = process_guess(guess, solution)
        st.write("".join([get_html(color_map[num], char) for num, char in zip(score, guess)]) + css, unsafe_allow_html=True)