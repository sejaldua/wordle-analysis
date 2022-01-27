# wordle-analysis

Analyzing the most strategic words to guess on Wordle, based on letter frequency distributions

## The Data

`12972` [guessable words](./word_list_data/guessable_words.csv)  
`2315` [mystery words](./word_list_data/mystery_words.csv)

## Exploratory Analysis

#### Most common letters

In the words of Pat Sajak, "R, S, T, L, N, E". These are the most frequently appearing letters in the English language and are, as such, used in the Bonus Round of the game Wheel of Fortune. But I wanted to start this project by verifying if they are, in fact, the most frequent letters when we limit our scope to only _5-letter_ English words.

<img src="./figures/top_eight_letters_by_freq.png" width="75%">

As it turns out, `E`, `A`, `R`, `O`, `T`, `L`, `I`, `S` are the most frequent letters that appear in 5-letter words. Now, quick, think of a 5-letter word using these letters!

#### Heatmap to analyze letter frequency by positions

<img src="./figures/solution_letter_heatmap.png" width="75%">

## Simple Scoring Heuristics

## Simulation Results

| Approach                   | Best Initial Guess |
| -------------------------- | ------------------ |
| Max-size Prioritization    | `RAISE`            |
| Max-entropy Prioritization | `SOARE`            |
| Max-splits Prioritization  | `TRACE`            |
