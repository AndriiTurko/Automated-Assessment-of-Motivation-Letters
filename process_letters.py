import csv
import os
import re
from itertools import permutations
from tqdm import tqdm

technical_paragraph_pattern = r"(Мотиваційний лист)\s+[^\r\n]+(?:\r?\n\s*[^\r\n]+){2,}?(?=\r?\n\s*[^\r\n]*[.,!](\r?\n|$))"


def extract_average_score(letter):
    match = re.search(technical_paragraph_pattern, letter)
    if not match:
        return '-'

    paragraph = match.group(0)
    score_match = re.search(
        # r"(?:(?:[Сс]ередній|[Бб]ал)\D*)(\d+([.,]\d+)?)|^\s*(\d+([.,]\d+)?)\s*$",
        r"(?:(?:[Сс]ередній|[Бб]ал)\D*)(\d+([.,]\d+)?)|^\s*(\d+([.,]\d+)?)\s*$|(\d+([.,]\d+)?)\s+[Бб]ал(ів)?",
        paragraph,
        re.IGNORECASE | re.MULTILINE)

    if not score_match:
        return '-'

    raw_score = score_match.group(1) or score_match.group(3) or score_match.group(5)
    raw_score = raw_score.replace(',', '.')

    parts = raw_score.split('.')
    if len(parts) > 2:
        return '-'

    int_part, *decimal_part = parts
    if len(int_part) > 2:
        return '-'
    if decimal_part and len(decimal_part[0]) > 4:
        return '-'

    try:
        return float(raw_score)
    except ValueError:
        return '-'

def remove_technical_paragraph(letter):
    return re.sub(technical_paragraph_pattern, "", letter, 1).lstrip()

def remove_blank_lines(letter):
    letter = re.sub(r'^\s+', '', letter, flags=re.MULTILINE)
    return re.sub(r'\s+$', '', letter, flags=re.MULTILINE)


def clean_short_lines(text):
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
    pattern = r'МЛ_([ІіЇїЄєЬьЮюйїА-Яа-я-`]+)_([ІіЇїЄєЬьЮюйїА-Яа-я-`]+)*_?([ІіЇїЄєЬьЮюйїА-Яа-я-`]+)_([ІіЇїЄєЬьЮюйїА-Яа-я-`]+)*_?\d+'
    match = re.search(pattern, filename)

    if not match:
        print(filename)
        print("Filename format is incorrect. Expecting format: 'МЛ_Прізвище_Ім'я_По-батькові_somenumber.txt'")
        return input_text

    match_groups = match.groups()

    # Create entrant's ПІБ (all combinations)
    if match_groups[3] is not None:
        surname, second_surname_or_first_name, first_name_or_patronymic_1, patronymic_1_or_patronymic_2 = match_groups
        entrant_patterns = build_name_combinations(surname, second_surname_or_first_name, first_name_or_patronymic_1, patronymic_1_or_patronymic_2)
    else:
        surname, first_name, patronymic, _ = match_groups
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

    step1 = entrant_regex.sub("[ВСТУПНИК]", input_text)
    step2 = rector_regex.sub("[РЕКТОР]", step1)
    step3 = director_regex.sub("[ДИРЕКТОР]", step2)

    return step3


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
    with open(output_csv, mode='w', encoding='utf-8', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['letter_id', 'program', 'average_score', 'mentions_average', 'length', 'text'])

        for root, dirs, files in os.walk(src_dir):
            program = os.path.basename(root).split(' - ')[0]
            for file in tqdm(files, desc=f"Processing folder: {program}"):
                letter_id = os.path.splitext(file)[0].split('_')[-1]

                file_path = os.path.join(root, file)

                average_score, mentions_average, text = process_file(file_path, file)

                writer.writerow([letter_id, program, average_score, mentions_average, len(text.split()), text])



if __name__ == "__main__":
    src_directory = './motivation_letters'
    output_csv = './letters_1.csv'
    process_files_and_write_to_csv(src_directory, output_csv)