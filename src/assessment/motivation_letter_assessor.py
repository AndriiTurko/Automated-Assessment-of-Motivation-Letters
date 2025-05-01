import pandas as pd
import numpy as np


def count_total(record, questions_percentiles):
    """Calculate total assessment score for a motivation letter record."""
    total = 0

    total += 1 if record['average_score'] != '-' else 0
    total += 1 if record['mentions_average'] != '-' else 0

    total += grammar_score(record['grammar_errors'])
    total += word_count_score(record['word_count'])

    for col in record.keys():
        if col.startswith('question_'):
            total += question_score(record[col], questions_percentiles[col])

    return total


def grammar_score(grammar_errors):
    """Score based on the number of grammar errors."""
    if grammar_errors <= 4:
        return 5
    elif grammar_errors <= 8:
        return 4
    elif grammar_errors <= 12:
        return 3
    elif grammar_errors <= 16:
        return 2
    elif grammar_errors <= 20:
        return 1
    return 0


def word_count_score(word_count):
    """Score based on word count range."""
    if 800 <= word_count <= 900:
        return 3
    elif 750 <= word_count <= 950:
        return 1
    else:
        return 0


def question_score(score, question_percentiles):
    """Score individual question based on its percentile thresholds."""
    p5, p20, p40, p70, p90 = question_percentiles

    if score >= p90:
        return 5
    elif score >= p70:
        return 4
    elif score >= p40:
        return 3
    elif score >= p20:
        return 2
    elif score >= p5:
        return 1
    else:
        return 0


def assess_letters(letters_csv, output_csv):
    df = pd.read_csv(letters_csv)

    questions_percentiles = {}

    for col in df.columns:
        if col.startswith('question_'):
            all_scores = df[col].dropna()  # Drop NaN values to avoid errors
            questions_percentiles[col] = np.percentile(all_scores, [5, 20, 40, 70, 90])

    df['total_score'] = df.apply(lambda row: count_total(row.to_dict(), questions_percentiles), axis=1)

    df.to_csv(output_csv, index=False)


if __name__ == "__main__":
    letters_csv = '../../data/letters_with_grammar.csv'
    output_csv = '../../data/letters_with_total_score.csv'

    assess_letters(letters_csv, output_csv)