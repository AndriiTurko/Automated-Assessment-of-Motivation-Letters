import os
import re
from itertools import permutations


def clean_motivation_letter(letter):
    cleaned_letter = re.sub(r'^Вступник:.*\n?', '', letter, flags=re.MULTILINE)

    # pattern = r"""
    # (                       # Початок групи службового параграфа
    # (?:                     # Незахоплююча група для повторюваних рядків
    #     ^(?:                # Початок рядка
    #         (?:.*Ректору.*)|
    #         (?:.*Добко.*)|
    #         (?:.*вступни(ця|к).*?)|
    #         (?:.*освітня програма.*)|
    #         (?:.*бал(?!анс).*?)|
    #         (?:.*гімназія.*)|
    #         (?:.*школа.*)|
    #         (?:.*ліцей.*)|
    #         (?:.*e[-]?mail.*)|
    #         (?:.*@.*)|
    #         (?:.*тел.*)|
    #         (?:.*\+380.*)|
    #         (?:.*вул\..*?)|
    #         (?:.*м\.\s?\w+.*)
    #     ).*\n
    # ){4,}                  # Щонайменше 4 таких рядки
    # (?:\s*\n)+             # Завершується одним або кількома порожніми рядками
    # )
    # """

    # pattern = r'^(Ректору\s+Українського\s+католицького\s+університету[\s\S]+?(?:\s*(?:телефон|e\-mail|школа)[^\n]*?){2,})\s*\n?'

    pattern = re.compile(
        r"""(?mx)                            # багаторядковий та розширений режим
        (                                   # початок блоку
            ^(?:.+\n){2,15}?                 # до 15 рядків, що містять особисті дані
            (?:                             # додаткові ознаки "технічного" параграфа:
                (середній|вступниц[ья]|добко|email|тел|освітня|школа|бал|вул\.?|м\.)  # ключові слова
                .*
            )+                              # має бути хоча б одне таке слово
            \n{1,2}                         # кінець блоку з відступом (1 або 2 порожні рядки)
        )
        """)

    # Очистка тексту від службових параграфів
    # fully_cleaned_text = re.sub(pattern, '', cleaned_letter, flags=re.IGNORECASE | re.MULTILINE | re.VERBOSE)
    fully_cleaned_text = re.sub(pattern, '', cleaned_letter)

    return fully_cleaned_text.strip()


# def remove_technical_paragraph(letter):
#     return re.sub(r"Ректор(у|ові)\s+[^\r\n]+(?:\r?\n\s*[^\r\n]+){2,}?(?=\r?\n\s*\r?\n|\r?\n\s*$)", "", letter).lstrip()

def remove_vstupnyk(letter):
    return re.sub(r"^Вступник:.*\n?", "", letter, flags=re.MULTILINE).lstrip()

def remove_technical_paragraph(letter):
    return re.sub(r"([Рр])ектор(у|ові)\s+[^\r\n]+(?:\r?\n\s*[^\r\n]+){2,}?(?=\r?\n\s*[^\r\n]*[.,!]\s*(\r?\n|$))", "", letter).lstrip()

def remove_blank_lines(letter):
    return re.sub(r'(?<=\n)\s*\n+', '\n', letter)

def generate_name_forms(name):
    """Return regex for name with typical Ukrainian endings (declensions)."""
    name = name.lower().replace('й', 'й').replace('ї', 'ї').capitalize()

    drop_last_if = ('а', 'я', 'о', 'і', 'й', 'е', 'ь')
    suffixes = 'а|у|е|о|і|я|ю|є|и|ї|ий|ого|ому|ої|ій'

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
    combinations = [3, 2] if patronymic else [4, 3, 2] if extra else [2]
    for i in combinations:  # 3-part and 2-part combinations
        for p in permutations(parts, i):
            combos.append(r'\b' + r'\s+'.join(p) + r'\b')

    return combos


def depersonalize_text(filename, input_text):
    # Extract name details from filename
    # match = re.search(r'МЛ_(\w+)_(\w+)_(\w+)_\d+', filename)
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

    DOBKO = r'\bДобк(ові|о|у|а)?\b'
    TARAS = r'\bТарас(е|у|а|ові)?\b'
    DMYTROVYCH = r'\bДмитрович(у|а)?\b'

    rector_patterns = [
        fr'{DOBKO} {TARAS} {DMYTROVYCH}',
        fr'{TARAS} {DMYTROVYCH}',
        fr'{TARAS} {DOBKO}',
        fr'{DOBKO} {TARAS}',
        fr'{TARAS} {DMYTROVYCH} {DOBKO}',
    ]
    #
    # # Compile regex for efficient matching
    # pattern = re.compile('|'.join(personal_patterns), re.UNICODE | re.IGNORECASE)
    # r_pattern = re.compile('|'.join(rector_patterns), re.UNICODE | re.IGNORECASE)
    #
    # # Replace matches with placeholders or remove them
    # depersonalized_text = pattern.sub("***", input_text)
    # derectorized_text = r_pattern.sub("[РЕКТОР]", depersonalized_text)

    # Compile patterns
    entrant_regex = re.compile('|'.join(entrant_patterns), flags=re.IGNORECASE | re.UNICODE)
    rector_regex = re.compile('|'.join(rector_patterns), flags=re.IGNORECASE | re.UNICODE)

    # Replace
    step1 = entrant_regex.sub("[ВСТУПНИК]", input_text)
    step2 = rector_regex.sub("[РЕКТОР]", step1)

    return step2


def process_file(src_file_path, filename, dest_file_path):
    with open(src_file_path, "r", encoding="utf-8") as file:
        text = file.read()

    cleaned_text = remove_vstupnyk(text)
    cleaned_text = remove_technical_paragraph(cleaned_text)

    depersonalized_text = depersonalize_text(filename, cleaned_text)

    result = remove_blank_lines(depersonalized_text)

    with open(dest_file_path, "w", encoding="utf-8") as file:
        file.write(result)


def process_files_and_create_folders(src_dir):
    # print(f"Source directory: {src_dir}")
    # Walk through the source directory
    for root, dirs, files in os.walk(src_dir):
        # print(f"Processing folder: {root}")
        # print(f"Subfolders: {dirs}")
        # print(f"Files in folder: {files}")

        # For each folder, create the corresponding folder in the destination directory
        for file in files:
            # Get the relative folder path from the root
            relative_folder = os.path.relpath(root, src_dir)
            # Create the new folder structure in the destination directory
            dest_folder = os.path.join("./TEST", relative_folder)
            os.makedirs(dest_folder, exist_ok=True)

            # print(f"Relative folder: {relative_folder}, Destination folder: {dest_folder}")

            src_file_path = os.path.join(root, file)
            splitted = file.split('_')
            output_file = splitted[0] + '_' + splitted[-1]
            dest_file_path = os.path.join(dest_folder, output_file)

            # print(f"Copying {src_file_path} to {dest_file_path}")

            process_file(src_file_path, file, dest_file_path)


if __name__ == "__main__":
    src_directory = './motivation_letters'
    process_files_and_create_folders(src_directory)