"""Gemini calls with structured JSON output and item-specific context."""
import json
import time
from pathlib import Path

PROMPTS = json.loads((Path(__file__).parent / "prompts" / "feedback_prompts.json").read_text())
MODEL = "gemini-2.5-flash"


def _request(api_key, system, context):
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=api_key)
    started = time.monotonic()
    response = client.models.generate_content(
        model=MODEL,
        contents=system + "\\nITEM CONTEXT:\\n" + json.dumps(context, ensure_ascii=False),
        config=types.GenerateContentConfig(
            temperature=0.2,
            response_mime_type="application/json",
            response_schema={
                "type": "OBJECT",
                "properties": {"message": {"type": "STRING"}, "focus": {"type": "STRING"}},
                "required": ["message", "focus"],
            },
        ),
    )
    result = json.loads(response.text)
    if not isinstance(result.get("message"), str) or not result["message"].strip():
        raise ValueError("Invalid tutor response")
    result["model"] = MODEL
    result["latency_ms"] = round((time.monotonic() - started) * 1000)
    return result


def instructional_reply(api_key, item, learner_response):
    return _request(api_key, PROMPTS["common"] + "\\n" + PROMPTS["instruction_reply"], {
        "question": item["question"], "expected_answer": item["expected_answer"],
        "guidance": item["guidance"], "learner_response": learner_response,
        "stage": "instruction", "instruction_shared_across_conditions": True,
    })


def generate_feedback(api_key, item, normalized, correct, condition, reasoning=None):
    if condition not in (2, 3):
        raise ValueError("LLM feedback is for conditions 2 and 3")
    prompt = PROMPTS["condition_2" if condition == 2 else "condition_3_feedback"]
    result = _request(api_key, PROMPTS["common"] + "\\n" + prompt, {
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
