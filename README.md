# LLM-Based Intelligent Tutoring System (ITS)

## Project Overview

This project develops an LLM-based Intelligent Tutoring System (ITS) that provides instruction, practice activities, and individualized feedback. My main research interest is how different feedback designs influence students' reasoning and learning.

The current prototype focuses on **Module 1: Finding the Central Message**.

## Learning Flow

1. **Instruction:** Students read instructional materials and answer questions with AI tutor support.
2. **Worked Example:** Students review an example.
3. **Practice:** Students complete 3 items and receive feedback.
4. **Knowledge Test:** Students complete 3 items without feedback.

## Feedback Conditions

- **Condition 1:** Simple, predefined feedback.
- **Condition 2:** LLM-generated feedback based on item-specific prompts.
- **Condition 3:** Students explain their reasoning before receiving LLM-generated feedback.

## Implementation

- **Python & Streamlit:** Web interface and application logic.
- **Groq API (`openai/gpt-oss-20b`):** LLM-generated feedback.
- **JSON:** Instructional materials and feedback prompts.
- **JSONL:** Interaction logging for prototype testing.

## Run Locally

```bash
pip install -r requirements.txt
streamlit run main.py
```

Add `GROQ_API_KEY` to `.streamlit/secrets.toml` before running.

## Next Steps

- Validate LLM-generated feedback.
- Improve the interface and interaction logging.
- Integrate actual instructional materials.
- Evaluate students' attention, reasoning, and learning outcomes.

*Note: This public repository uses demonstration materials, not the original research instructional materials.*

