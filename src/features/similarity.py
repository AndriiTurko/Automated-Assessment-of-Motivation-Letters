from sentence_transformers import SentenceTransformer, util


model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")


def compute_similarity(letter_text, criteria_list):
    letter_embedding = model.encode(letter_text, convert_to_tensor=True)
    scores = []

    for question in criteria_list:
        question_embedding = model.encode(question, convert_to_tensor=True)
        similarity = float(util.cos_sim(letter_embedding, question_embedding)[0])
        scores.append(similarity)

    return scores
