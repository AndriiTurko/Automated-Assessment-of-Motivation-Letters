import multiprocessing
import time

import numpy as np
import pandas as pd
from multiprocessing import Pool
import language_tool_python

NUM_PROCESSES = multiprocessing.cpu_count()


def check_grammar(text, tool):
    """Check grammar errors for a given text."""
    try:
        matches = tool.check(text)
    except Exception as e:
        print(f"Error checking grammar: {e}")
        matches = []
    return len(matches), matches


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
    # Use multiprocessing to process chunks
    with Pool(processes=NUM_PROCESSES) as pool:
        results = []
        for result in pool.imap_unordered(process_chunk, chunks):
            results.append(result)

    print(f"Processing time: {time.time() - start:.2f} seconds")

    df = pd.concat(results, ignore_index=True)

    df.to_csv(f"../data/letters_with_grammar.csv", index=False)


def main():
    df = pd.read_csv("../data/letters.csv")

    check_grammar_multiprocessing(df)


if __name__ == "__main__":
    main()