# Automated Motivation Letter Assessment

This project automates the preprocessing, anonymization, and semantic evaluation of motivation letters, as well as grammar analysis and scoring. It is part of a Bachelor's thesis focused on Automated Motivation Letter Assessment.

---

## 📁 Project Structure

```
src/
├── process_letters.py                # Preprocess, clean, anonymize and evaluate letters
├── features/
│   ├── grammar.py                    # Run grammar analysis on processed letters CSV
│   ├── criteria.py                   # Holds normalized semantic evaluation criteria
│   ├── normalize_text.py             # Prepares letter content for analysis
│   └── similarity.py                 # Semantic similarity scoring
├── assessment/
│   └── motivation_letter_assessor.py  # Final scoring system and aggregation
```

---

## ⚙️ Workflow Overview

### 1. **Preprocess and Evaluate Letters**

```bash
python src/process_letters.py
```

This script:
- Removes technical and personal data
- Normalizes and cleans the text
- Computes semantic similarity scores for 7 key questions
- Outputs `data/letters.csv`

> Ensure paths are updated in the script:
```python
src_directory = '../motivation_letters'
output_csv = 'data/letters.csv'
```

---

### 2. **Run Grammar Evaluation**

After the CSV is generated, run:

```bash
python src/features/grammar.py
```

This script:
- Adds grammar error counts and descriptions
- Appends results to the same CSV (or saves a new one)
> Ensure paths are updated in the script:
```python
letters_csv = "../../data/letters.csv"
output_csv = "../data/letters_with_grammar.csv"
```

---

### 3. **Score and Aggregate**

After the CSV is generated, run:

```bash
python src/features/motivation_letter_assessor.py
```

This script:
- Reads the enriched CSV (from step 2)
- Calculates the total score
- Exports a final scored CSV

> Ensure paths are updated in the script:
```python
letters_csv = '../../data/letters_with_grammar.csv'
output_csv = '../../data/letters_with_total_score.csv'
```

---

## 🧠 Scoring Logic Overview

### From `motivation_letter_assessor.py`:

| Component            | Score Range | Notes                                    |
|---------------------|-------------|------------------------------------------|
| Avg. Score Present  | 0 or 1      | Extracted from technical paragraph       |
| Mentions Avg. Score | 0 or 1      | Based on keywords in text                |
| Word Count          | 1 or 3      | 3: 800–900, 1: 750-950                   |
| Questions (x7)      | 0–5 each    | Based on semantic similarity percentiles |
| Grammar Errors      | 0–5         | Fewer errors = higher score              |


Total score is a sum of all these components.

---

## 📦 Output CSV

```
📄 data/letters_with_total_scores.csv
```

After all steps, the final CSV includes:

- `letter_id`
- `program`
- `average_score`
- `mentions_average`
- `word_count`
- `text` and `normalized_text`
- `question_1` to `question_7`
- `grammar_errors`
- `grammar_errors_description` *(use json.loads())
- `total_score`

---

## 📌 Notes

- Ensure `src/features/grammar.py` is run after `process_letters.py`
- Ensure `src/assessment/motivation_letters_assessor.py` is run after `src/features/grammar.py`
- Notebooks can be used for interactive analysis and visualization

---

## 📄 License

This project is licensed under the MIT License – see the [LICENSE](./LICENSE) file for details.