import os
import re
from itertools import permutations
from tqdm import tqdm


def remove_technical_paragraph(letter):
    return re.sub(r"(Мотиваційний лист)\s+[^\r\n]+(?:\r?\n\s*[^\r\n]+){2,}?(?=\r?\n\s*[^\r\n]*[.,!](\r?\n|$))", "", letter).lstrip()

def remove_blank_lines(letter):
    return re.sub(r'(?<=\n)\s*\n+', '', letter)


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


def process_file(src_file_path, filename, dest_file_path):
    with open(src_file_path, "r", encoding="utf-8") as file:
        text = file.read()

    text = remove_blank_lines(text)
    text = clean_short_lines(text)
    text = depersonalize_text(filename, text)
    text = remove_technical_paragraph(text)


    with open(dest_file_path, "w", encoding="utf-8") as file:
        file.write(text)


def process_files_and_create_folders(src_dir, dest_dir):
    for root, dirs, files in os.walk(src_dir):
        folder = os.path.basename(root)
        for file in tqdm(files, desc=f'Processing files in {folder}'):
            relative_folder = os.path.relpath(root, src_dir)

            dest_folder = os.path.join(dest_dir, relative_folder)
            os.makedirs(dest_folder, exist_ok=True)

            src_file_path = os.path.join(root, file)
            splitted = file.split('_')
            output_file = splitted[0] + '_' + splitted[-1]
            dest_file_path = os.path.join(dest_folder, output_file)

            process_file(src_file_path, file, dest_file_path)


if __name__ == "__main__":
    src_directory = './motivation_letters'
    dest_directory = './depersonalized_letters'

    process_files_and_create_folders(src_directory, dest_directory)