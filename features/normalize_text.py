import spacy

nlp = spacy.load('uk_core_news_sm')


def normalize_text(text):
    doc = nlp(text)
    normalized_text = " ".join([token.lemma_ for token in doc if not token.is_stop])
    return normalized_text