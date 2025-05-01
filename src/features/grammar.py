import json
import time
from multiprocessing import cpu_count, Pool

import numpy as np
import pandas as pd
import language_tool_python

NUM_PROCESSES = cpu_count()


def check_grammar(text, tool):
    """Check grammar errors for a given text."""
    try:
        matches = tool.check(text)
    except Exception as e:
        print(f"Error checking grammar: {e}")
        matches = []
    return len(matches), json.dumps([m.__dict__ for m in matches])


def process_chunk(chunk):
    """Process a chunk of rows."""
    print(f"Processing chunk with {len(chunk)} rows")

    with language_tool_python.LanguageTool('uk-UA') as tool:
        chunk[['grammar_errors', 'grammar_errors_description']] = chunk['text'].apply(
            lambda text: pd.Series(check_grammar(text, tool))
        )

    return chunk


def check_grammar_multiprocessing(df):
    """Check grammar errors in a DataFrame using multiprocessing."""
    # Split the DataFrame into chunks to distribute the workload
    chunks = np.array_split(df, NUM_PROCESSES)
    print(f"Number of chunks: {len(chunks)}")

    start = time.time()
    with Pool(processes=NUM_PROCESSES) as pool:
        results = []
        for result in pool.imap_unordered(process_chunk, chunks):
            results.append(result)

    print(f"Processing time: {time.time() - start:.2f} seconds")

    return pd.concat(results, ignore_index=True)


def run_check_grammar(letters_csv, output_csv):
    df = pd.read_csv(letters_csv)

    result_df = check_grammar_multiprocessing(df)

    result_df.to_csv(output_csv, index=False)


if __name__ == "__main__":
    letters_csv = "../../data/letters.csv"
    output_csv = "../data/letters_with_grammar.csv"

    run_check_grammar(letters_csv, output_csv)