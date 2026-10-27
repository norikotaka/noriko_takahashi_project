"""Single-column Streamlit ITS. Run: streamlit run main.py"""
import uuid
import streamlit as st
from answer_handler import normalize_answer, is_correct
from logger import log_event
from module_engine import load_module
from tutor import instructional_reply, generate_feedback

st.set_page_config(page_title="ITS Module 1 Demo", layout="centered")
st.title("Module 1 — Finding the Central Message")
st.caption("Original demo materials only · Single-column tutoring")
module = load_module()


def start(condition):
    st.session_state.update(
        pid=str(uuid.uuid4()), condition=condition, index=0, phase="show",
        messages=[], pending=None, started=True, selected_id=None
    )
    event("session_started", module_id=module["module_id"])


def event(name, **details):
    log_event(st.session_state.pid, st.session_state.condition, name, **details)


def show(role, content):
    st.session_state.messages.append({"role": role, "content": content})


def advance():
    st.session_state.index += 1
    st.session_state.phase = "show"
    st.session_state.selected_id = None
    st.rerun()


def api_key():
    key = st.secrets.get("GEMINI_API_KEY", "")
    if not key:
        st.error("GEMINI_API_KEY is missing from Streamlit secrets.")
        st.stop()
    return key


if not st.session_state.get("started"):
    condition = st.radio("Try a feedback condition", [1, 2, 3],
        format_func=lambda n: {1:"1 — Simple feedback", 2:"2 — Feedback with reasoning",
                               3:"3 — Ask for reasoning first"}[n])
    st.info("Prototype logging is local JSONL and not durable on Streamlit Cloud. Do not collect real participant data with this storage.")
    if st.button("Start module", type="primary"):
        start(condition)
        st.rerun()
    st.stop()

steps = module["steps"]
if st.session_state.index >= len(steps):
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    st.success("Module complete.")
    event_once = "completion_logged"
    if not st.session_state.get(event_once):
        event("module_completed")
        st.session_state[event_once] = True
    st.stop()

item = steps[st.session_state.index]
if st.session_state.phase == "show":
    kind = item["type"]
    if kind == "instruction":
        show("assistant", item["text"])
        st.session_state.phase = "continue"
    elif kind == "instruction_ask":
        show("assistant", item["question"])
        st.session_state.phase = "instruction_answer"
    elif kind == "worked_example":
        show("assistant", "**Worked example**\\n\\n" + item["passage"] +
             "\\n\\n**Question:** " + item["question"] +
             "\\n\\n**Answer:** " + item["expected_answer"] +
             "\\n\\n" + item["explanation"])
        st.session_state.phase = "continue"
    else:
        label = "Knowledge test" if kind == "knowledge_test" else "Practice"
        show("assistant", "**" + label + "**\\n\\n" +
             "\\n\\n".join(f"**{i+1}.** {s['text']}" for i,s in enumerate(item["sentences"])) +
             "\\n\\n**" + item["question"] + "**")
        st.session_state.phase = "select"
    event("item_displayed", item_id=item["id"], item_type=kind)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

phase = st.session_state.phase
if phase == "continue":
    if st.button("Continue", type="primary"):
        event("continue_clicked", item_id=item["id"])
        advance()
elif phase == "instruction_answer":
    answer = st.chat_input("Type your answer")
    if answer and answer.strip():
        show("user", answer)
        event("instruction_answer_submitted", item_id=item["id"], response=answer)
        st.session_state.pending = {"instruction_answer": answer}
        st.session_state.phase = "instruction_feedback"
        st.rerun()
elif phase == "instruction_feedback":
    try:
        with st.spinner("Tutor responding..."):
            reply = instructional_reply(api_key(), item, st.session_state.pending["instruction_answer"])
    except Exception as exc:
        st.error(f"Could not get instructional response ({type(exc).__name__}).")
        if st.button("Retry"): st.rerun()
        st.stop()
    show("assistant", reply["message"])
    event("instruction_feedback_displayed", item_id=item["id"], llm_response=reply)
    st.session_state.phase = "continue"
    st.rerun()
elif phase == "select":
    options = [s["id"] for s in item["sentences"]]
    selected = st.radio("Select the main sentence", options, index=None,
        format_func=lambda sid: next(s["text"] for s in item["sentences"] if s["id"] == sid),
        key=f"selection_{item['id']}")
    if st.button("Submit sentence", type="primary", disabled=selected is None):
        normalized = normalize_answer(item, selected)
        correct = is_correct(item, normalized)
        st.session_state.pending = {"selection": normalized, "correct": correct}
        show("user", normalized["selected_sentence_text"])
        event("answer_submitted", item_id=item["id"], answer=normalized, is_correct=correct)
        if item["type"] == "knowledge_test":
            show("assistant", "Your answer has been recorded.")
            st.session_state.phase = "continue"
        elif st.session_state.condition == 3:
            show("assistant", "Why did you choose that sentence as the central message?")
            event("reasoning_requested", item_id=item["id"])
            st.session_state.phase = "reasoning"
        else:
            st.session_state.phase = "feedback"
        st.rerun()
elif phase == "reasoning":
    answer = st.chat_input("Explain your choice")
    if answer and answer.strip():
        show("user", answer)
        st.session_state.pending["reasoning"] = answer
        event("reasoning_submitted", item_id=item["id"], response=answer)
        st.session_state.phase = "feedback"
        st.rerun()
elif phase == "feedback":
    pending = st.session_state.pending
    if st.session_state.condition == 1:
        message = item["simple_feedback"]["correct" if pending["correct"] else "incorrect"]
        result = {"item_id":item["id"], "condition":1,
            "evaluation":{"is_correct":pending["correct"],"expected_answer":item["expected_answer"]},
            "feedback":{"message":message,"focus":"central_message"},
            "next_action":"continue","model":None}
    else:
        try:
            with st.spinner("Generating feedback..."):
                result = generate_feedback(api_key(), item, pending["selection"],
                    pending["correct"], st.session_state.condition, pending.get("reasoning"))
        except Exception as exc:
            st.error(f"Feedback unavailable ({type(exc).__name__}).")
            if st.button("Retry"): st.rerun()
            st.stop()
    show("assistant", result["feedback"]["message"])
    event("feedback_displayed", item_id=item["id"], llm_response=result)
    st.session_state.phase = "continue"
    st.rerun()
