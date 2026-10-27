"""Groq calls with JSON output and item-specific context."""
import json
import time
from pathlib import Path

PROMPTS = json.loads((Path(__file__).parent / "prompts" / "feedback_prompts.json").read_text())
MODEL = "openai/gpt-oss-20b"


def _request(api_key, system, context):
    from groq import Groq

    client = Groq(api_key=api_key, timeout=25.0, max_retries=1)
    started = time.monotonic()
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system + "\nReturn a JSON object with string fields message and focus."},
            {"role": "user", "content": "ITEM CONTEXT:\n" + json.dumps(context, ensure_ascii=False)},
        ],
        temperature=0.2,
        max_completion_tokens=350,
        response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content
    if not content:
        raise ValueError("Groq returned an empty response")
    result = json.loads(content)
    if not isinstance(result.get("message"), str) or not result["message"].strip():
        raise ValueError("Invalid tutor response: missing message")
    result.setdefault("focus", "central_message")
    result["model"] = MODEL
    result["latency_ms"] = round((time.monotonic() - started) * 1000)
    return result


def instructional_reply(api_key, item, learner_response):
    return _request(api_key, PROMPTS["common"] + "\n" + PROMPTS["instruction_reply"], {
        "question": item["question"], "expected_answer": item["expected_answer"],
        "guidance": item["guidance"], "learner_response": learner_response,
        "stage": "instruction", "instruction_shared_across_conditions": True,
    })


def generate_feedback(api_key, item, normalized, correct, condition, reasoning=None):
    if condition not in (2, 3):
        raise ValueError("LLM feedback is for conditions 2 and 3")
    prompt = PROMPTS["condition_2" if condition == 2 else "condition_3_feedback"]
    result = _request(api_key, PROMPTS["common"] + "\n" + prompt, {
        "item_id": item["id"], "question": item["question"],
        "sentences": item["sentences"], "correct_sentence_id": item["correct_sentence_id"],
        "expected_answer": item["expected_answer"], "item_specific_prompt": item["item_prompt"],
        "learner_selection": normalized, "is_correct_determined_by_python": correct,
        "learner_reasoning": reasoning, "condition": condition,
    })
    return {"item_id": item["id"], "condition": condition,
            "evaluation": {"is_correct": correct, "expected_answer": item["expected_answer"]},
            "feedback": {"message": result["message"], "focus": result["focus"]},
            "next_action": "continue", "model": result["model"],
            "latency_ms": result["latency_ms"]}
