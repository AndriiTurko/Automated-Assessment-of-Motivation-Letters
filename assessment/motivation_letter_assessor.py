def count_total(row, questions_percentiles):
    total = 0

    total += 1 if row['average_score'] != '-' else 0
    total += 1 if row['mentions_average'] != '-' else 0

    total += grammar_score(row['grammar_errors'])
    total += word_count_score(row['word_count'])

    for col in row.keys():
        if col.startswith('question_'):
            total += question_score(row[col], questions_percentiles[col])

    return total


def grammar_score(grammar_errors):
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
    if 800 <= word_count <= 900:
        return 3
    elif 750 <= word_count <= 950:
        return 1
    else:
        return 0


def question_score(score, question_percentiles):
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
