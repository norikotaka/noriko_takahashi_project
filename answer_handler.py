"""Normalize UI selection into a frontend-independent sentence answer."""


def normalize_answer(item, sentence_id):
    matches = [s for s in item["sentences"] if s["id"] == sentence_id]
    if len(matches) != 1:
        raise ValueError("Invalid sentence selection")
    return {
        "item_id": item["id"],
        "selected_sentence_id": sentence_id,
        "selected_sentence_text": matches[0]["text"],
    }


def is_correct(item, normalized):
    return normalized["selected_sentence_id"] == item["correct_sentence_id"]
