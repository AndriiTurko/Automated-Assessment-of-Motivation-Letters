import os
import re
from itertools import permutations

import pandas as pd
from tqdm import tqdm

from src.features.criteria import get_criteria_normalized
from src.features.similarity import compute_similarity
from src.features.normalize_text import normalize_text

technical_paragraph_pattern = r"(Мотиваційний лист)\s+[^\r\n]+(?:\r?\n\s*[^\r\n]+){2,}?(?=\r?\n\s*[^\r\n]*[.,!](\r?\n|$))"


def extract_average_score(letter):
    """Extracts the average score value from the technical paragraph in the letter."""
    technical_paragraph = re.search(technical_paragraph_pattern, letter)
    if not technical_paragraph:
        return '-'

    paragraph = technical_paragraph.group(0)
    score_technical_paragraph = re.search(
        r"(?:(?:[Сс]ередній|[Бб]ал)\D*)(\d+([.,]\d+)?)|^\s*(\d+([.,]\d+)?)\s*$|(\d+([.,]\d+)?)\s+[Бб]ал(ів)?",
        paragraph,
        re.IGNORECASE | re.MULTILINE)

    if not score_technical_paragraph:
        return '-'

    score_text = score_technical_paragraph.group(1) or score_technical_paragraph.group(3) or score_technical_paragraph.group(5)
    score_text = score_text.replace(',', '.')

    parts = score_text.split('.')
    if len(parts) > 2:
        return '-'

    int_part, *decimal_part = parts
    if len(int_part) > 2:
        return '-'
    if decimal_part and len(decimal_part[0]) > 4:
        return '-'

    try:
        return float(score_text)
    except ValueError:
        return '-'


def remove_technical_paragraph(text):
    """Removes the identified technical paragraph from the letter text."""
    return re.sub(technical_paragraph_pattern, "", text, 1).lstrip()


def remove_blank_lines(text):
    text = re.sub(r'^\s+', '', text, flags=re.MULTILINE)
    return re.sub(r'\s+$', '', text, flags=re.MULTILINE)


def clean_short_lines(text):
    """Remove ,. from short lines for better technical paragraph recognition"""
    return re.sub(r"^(?!.*[Шш]ановн(ий|і|а))(.{10,60}?)[,.](?=\r?$)", r"\1", text, flags=re.MULTILINE)


def generate_name_forms(name):
    """Return regex for name with typical Ukrainian endings (declensions)."""
    name = name.lower().replace('й', 'й').replace('ї', 'ї').capitalize()

    drop_last_if = ('а', 'я', 'о', 'і', 'й', 'е', 'ь')
    suffixes = 'а|я|о|і|й|е|ь|у|ю|є|и|ї|ий|ого|ому|ої|ій'

    if name[-2:] == 'ий':
        base = name[:-2]
    elif name[-1] in drop_last_if:
        base = name[:-1]
    else:
        base = name

    return fr'{re.escape(base)}({suffixes})?'


def build_name_combinations(surname, first_name, patronymic, extra=None):
    """Return regex patterns for all 2- and 3-part combinations."""
    parts = [
        generate_name_forms(surname),
        generate_name_forms(first_name)
    ]

    if patronymic:
        parts.append(generate_name_forms(patronymic))
    if extra:
        parts.append(generate_name_forms(extra))

    combos = []
    combinations = [4, 3, 2, 1] if extra else [3, 2, 1] if patronymic else [2, 1]
    for i in combinations:
        for p in permutations(parts, i):
            combos.append(r'\b' + r'\s+'.join(p) + r'\b')

    return combos


def depersonalize_text(filename, input_text):
    pattern = r'МЛ_([ІіЇїЄєЬьЮюйїА-Яа-я-`]+)_([ІіЇїЄєЬьЮюйїА-Яа-я-`]+)_(([ІіЇїЄєЬьЮюйїА-Яа-я-`]+)*_)?(([ІіЇїЄєЬьЮюйїА-Яа-я-`]+)*_)?\d+'
    match = re.search(pattern, filename)

    if not match:
        print(filename)
        print("Filename format is incorrect. Expecting format: 'МЛ_Прізвище_Ім'я_По-батькові_somenumber.txt'")
        return input_text

    match_groups = match.groups()

    # Create entrant's ПІБ (all combinations)
    if match_groups[5] is not None:
        surname, second_surname_or_first_name, _, first_name_or_patronymic_1, _, patronymic_1_or_patronymic_2 = match_groups
        entrant_patterns = build_name_combinations(surname, second_surname_or_first_name, first_name_or_patronymic_1, patronymic_1_or_patronymic_2)
    else:
        surname,first_name, _, patronymic, _, _ = match_groups
        entrant_patterns = build_name_combinations(surname, first_name, patronymic)
        if '-' in first_name:
            first_name_parts = first_name.split('-')
            entrant_patterns += build_name_combinations(surname, ' - '.join(first_name_parts), patronymic)

    DOBKO = r'Добк(ові|о|у|а)'
    TARAS = r'Т(арас(е|у|а|ові)|.)'
    DMYTROVYCH = r'Д(митрович(у|а)|.)'

    rector_patterns = [
        fr'{DOBKO} {TARAS} ?{DMYTROVYCH}',
        fr'{TARAS} {DOBKO} {DMYTROVYCH}',
        fr'{TARAS} {DOBKO}',
        fr'{TARAS} {DMYTROVYCH} {DOBKO}',
        fr'{TARAS} {DMYTROVYCH}',
        fr'{DOBKO} {TARAS}',
    ]

    MOHYLIAK = r'Могиляк'
    IVANNA = r'Іванн(а|о|и|і)'
    ORESTIVNA = r'Орестівн(а|о|и|і)'

    director_patterns = [
        fr'{MOHYLIAK} {IVANNA} {ORESTIVNA}',
        fr'{IVANNA} {MOHYLIAK} {ORESTIVNA}',
        fr'{IVANNA} {MOHYLIAK}',
        fr'{IVANNA} {ORESTIVNA} {MOHYLIAK}',
        fr'{IVANNA} {ORESTIVNA}',
        fr'{MOHYLIAK} {IVANNA}',
        fr'{IVANNA}(?! Папа)',  # Standalone case for Іванна, excluding Іванна Папа
    ]

    entrant_regex = re.compile('|'.join(entrant_patterns), flags=re.IGNORECASE | re.UNICODE)
    rector_regex = re.compile('|'.join(rector_patterns), re.UNICODE)
    director_regex = re.compile('|'.join(director_patterns), re.UNICODE)

    text_entrant_replaced = entrant_regex.sub("[ВСТУПНИК]", input_text)
    text_rector_replaced = rector_regex.sub("[РЕКТОР]", text_entrant_replaced)
    text_director_replaced = director_regex.sub("[ДИРЕКТОР]", text_rector_replaced)

    return text_director_replaced


def mentions_average_score(text):
    return 1 if re.search(r"[Сс]ередн(і[йм]|ього) [Бб]ал(ом|у)?", text) is not None else 0


def process_file(src_file_path, filename):
    with open(src_file_path, "r", encoding="utf-8") as file:
        text = file.read()

    text = remove_blank_lines(text)
    text = clean_short_lines(text)
    text = depersonalize_text(filename, text)
    average_score = extract_average_score(text)
    text = remove_technical_paragraph(text)
    text = re.sub(r'\uFEFF', '', text)
    text = text.replace('ґ.', '')
    text = text.strip('\n')
    mentions_average = mentions_average_score(text)

    return average_score, mentions_average, text



def process_letters_and_write_to_csv(src_dir, output_csv):
    data = []

    for root, dirs, files in os.walk(src_dir):
        program = os.path.basename(root).split(' - ')[0]
        for file in tqdm(files, desc=f"Processing folder: {program}"):
            letter_id = os.path.splitext(file)[0].split('_')[-1]
            file_path = os.path.join(root, file)

            average_score, mentions_average, text = process_file(file_path, file)
            normalized_text = normalize_text(text)
            criteria_list = get_criteria_normalized(program)
            questions_scores = compute_similarity(text, criteria_list)

            questions_scores_to_data = {
                f'question_{i+1}': score for i, score in enumerate(questions_scores)
            }

            # Append row data to the list
            data.append({
                'letter_id': letter_id,
                'program': program,
                'average_score': average_score,
                'mentions_average': mentions_average,
                'word_count': len(text.split()),
                'text': text,
                'normalized_text': normalized_text,
                **questions_scores_to_data
            })

    df = pd.DataFrame(data)

    df.to_csv(output_csv, index=False, encoding='utf-8')



if __name__ == "__main__":
    src_directory = '../motivation_letters'
    output_csv = 'data/letters.csv'
    process_letters_and_write_to_csv(src_directory, output_csv)