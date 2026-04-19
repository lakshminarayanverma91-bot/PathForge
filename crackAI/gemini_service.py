"""
gemini_service.py
─────────────────
All Gemini API calls for CrackAI live here.
Uses: gemini-2.0-flash
"""

import json
import google.generativeai as genai
from django.conf import settings

# ── Configure Gemini ──────────────────────────────────────────
genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')


def _call_gemini(prompt: str) -> str:
    """Helper: call Gemini and return raw text."""
    response = model.generate_content(prompt)
    return response.text.strip()


def _parse_json(text: str) -> dict | list:
    """Strip markdown code fences and parse JSON."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())


# ──────────────────────────────────────────────────────────────
# 1. Generate Questions
#    Returns a list of question dicts
# ──────────────────────────────────────────────────────────────
def generate_questions(role: str, interview_type: str, difficulty: str, count: int) -> list:
    """
    Ask Gemini to generate `count` interview questions
    for the given role, type, and difficulty.
    """
    prompt = f"""
You are an expert interviewer at a top tech company.

Generate exactly {count} interview questions for:
- Role: {role}
- Type: {interview_type} (Technical / Behavioural / HR Round / Mixed)
- Difficulty: {difficulty}

Return ONLY a valid JSON array. Each item must have:
- "question_text": the full question (string)
- "tags": list of 2-3 short tags like ["React", "Hooks", "Medium"]
- "hint": a one-line hint to help the candidate (string)

Rules:
- Questions must be specific to the role
- Difficulty {difficulty}: {"simple concepts" if difficulty == "Easy" else "moderate depth, some edge cases" if difficulty == "Medium" else "deep system design and trade-offs"}
- No numbering, no extra text — only the JSON array

Example format:
[
  {{
    "question_text": "Explain the difference between useMemo and useCallback in React.",
    "tags": ["React", "Hooks", "Medium"],
    "hint": "Think about memoisation and referential equality."
  }}
]
"""
    try:
        raw = _call_gemini(prompt)
        questions = _parse_json(raw)
        # Ensure it's a list
        if not isinstance(questions, list):
            raise ValueError("Expected a list of questions")
        return questions[:count]  # safety limit
    except Exception as e:
        print(f"[CrackAI] generate_questions error: {e}")
        # Fallback: return a generic question
        return [
            {
                "question_text": f"Tell me about your experience as a {role}. Walk me through a recent challenging project.",
                "tags": [role, interview_type, difficulty],
                "hint": "Use the STAR method: Situation, Task, Action, Result."
            }
        ] * count


# ──────────────────────────────────────────────────────────────
# 2. Evaluate a Single Answer
#    Returns scores + feedback for one question
# ──────────────────────────────────────────────────────────────
def evaluate_answer(question: str, answer: str, role: str, difficulty: str) -> dict:
    """
    Evaluate a candidate's answer to a single question.
    Returns dict with scores and AI feedback.
    """
    if not answer or answer.strip() == '[SKIPPED]':
        return {
            "communication_score": 0,
            "technical_score": 0,
            "confidence_score": 0,
            "overall_score": 0,
            "clarity_score": 0,
            "examples_score": 0,
            "depth_score": 0,
            "length_score": 0,
            "ai_feedback": "Question was skipped.",
            "tip": "Try to attempt every question — even a partial answer is better than skipping."
        }

    word_count = len(answer.split())

    prompt = f"""
You are an expert interviewer evaluating a candidate's answer.

Role: {role}
Difficulty: {difficulty}

Question:
{question}

Candidate's Answer:
{answer}

Evaluate and return ONLY a valid JSON object with these exact keys:
- "communication_score": 0-100 (clarity, fluency, structure)
- "technical_score": 0-100 (accuracy, depth, correct terminology)
- "confidence_score": 0-100 (assertiveness, directness, certainty)
- "overall_score": 0-100 (weighted average)
- "clarity_score": 0-100 (how clear and well-structured the answer is)
- "examples_score": 0-100 (did they use concrete real-world examples?)
- "depth_score": 0-100 (depth of knowledge shown)
- "length_score": 0-100 (appropriate answer length — not too short, not too long)
- "ai_feedback": a 2-3 sentence specific feedback string (what was good, what to improve)
- "tip": a single actionable tip for next time (1 sentence)

Be strict but fair. A {difficulty} question expects {"basic understanding" if difficulty == "Easy" else "solid applied knowledge" if difficulty == "Medium" else "expert-level depth and trade-offs"}.
"""
    try:
        raw = _call_gemini(prompt)
        result = _parse_json(raw)
        # Sanitise: ensure all fields exist
        defaults = {
            "communication_score": 50, "technical_score": 50, "confidence_score": 50,
            "overall_score": 50, "clarity_score": 50, "examples_score": 50,
            "depth_score": 50, "length_score": 50,
            "ai_feedback": "Good attempt. Keep practising.",
            "tip": "Try adding a real project example to strengthen your answer."
        }
        for k, v in defaults.items():
            result.setdefault(k, v)
        return result
    except Exception as e:
        print(f"[CrackAI] evaluate_answer error: {e}")
        return {
            "communication_score": 65, "technical_score": 62, "confidence_score": 60,
            "overall_score": 62, "clarity_score": 65, "examples_score": 50,
            "depth_score": 58, "length_score": max(0, min(100, word_count // 2)),
            "ai_feedback": "Your answer showed a basic understanding of the topic. Try adding concrete examples from past projects.",
            "tip": "Use the STAR format to structure answers more clearly."
        }


# ──────────────────────────────────────────────────────────────
# 3. Generate Final Session Report
#    Runs after all questions are answered
# ──────────────────────────────────────────────────────────────
def generate_session_report(role: str, interview_type: str, difficulty: str,
                             questions_and_answers: list, overall_score: float) -> dict:
    """
    Generate the full end-of-session report.
    questions_and_answers: list of dicts with 'question', 'answer', 'score'
    """
    qa_text = ""
    for i, qa in enumerate(questions_and_answers, 1):
        qa_text += f"\nQ{i}: {qa.get('question', '')}\nA{i}: {qa.get('answer', '[SKIPPED]')}\nScore: {qa.get('score', 0)}/100\n"

    prompt = f"""
You are an expert career coach reviewing a mock interview session.

Candidate applied for: {role}
Interview Type: {interview_type}
Difficulty: {difficulty}
Overall Score: {overall_score:.1f}/100

Questions and Answers:
{qa_text}

Generate a comprehensive session report. Return ONLY a valid JSON object with:

- "grade_label": short all-caps label like "GOOD PERFORMANCE" or "EXCELLENT" (max 3 words)
- "grade_title": encouraging headline like "Strong Foundation — Keep Practising" (max 8 words)
- "grade_message": 2-sentence message about overall performance
- "communication_score": 0-100 float
- "technical_score": 0-100 float
- "confidence_score": 0-100 float
- "examples_score": 0-100 float (how often they used real examples)
- "structure_score": 0-100 float (quality of answer structure)
- "strengths": list of exactly 3 strings, each starting with bold text like "**Strong vocabulary** — ..."
- "weaknesses": list of exactly 2 strings, each starting with bold text like "**Lack of examples** — ..."
- "ai_feedback": 4 paragraphs of detailed, personalised, constructive feedback (as a single string with \\n\\n between paragraphs)
- "improvements": list of exactly 3 improvement plans, each with:
    - "icon": an emoji
    - "title": short title (3-5 words)
    - "description": 2-sentence actionable improvement advice
    - "tag_label": one of "HIGH IMPACT" / "TECHNICAL" / "STORYTELLING" / "COMMUNICATION"
    - "tag_color": one of "coral" / "sky" / "emerald"
"""
    try:
        raw = _call_gemini(prompt)
        report = _parse_json(raw)
        return report
    except Exception as e:
        print(f"[CrackAI] generate_session_report error: {e}")
        # Fallback report
        grade = "EXCELLENT" if overall_score >= 90 else "GREAT JOB" if overall_score >= 80 else "GOOD EFFORT" if overall_score >= 65 else "KEEP GOING"
        return {
            "grade_label": grade,
            "grade_title": "Keep practising to reach your goal!",
            "grade_message": f"You scored {overall_score:.0f}/100 in this {role} interview. Keep practising to improve.",
            "communication_score": overall_score,
            "technical_score": overall_score,
            "confidence_score": overall_score,
            "examples_score": overall_score - 10,
            "structure_score": overall_score + 5,
            "strengths": [
                "**Technical understanding** — You demonstrated awareness of core concepts.",
                "**Consistency** — You attempted all questions without giving up.",
                "**Communication** — Your answers were generally clear and easy to follow."
            ],
            "weaknesses": [
                "**Real examples** — Add specific project references to make answers memorable.",
                "**Depth** — Push further into trade-offs and edge cases to show expert thinking."
            ],
            "ai_feedback": "You showed a solid foundation in this session.\n\nFocus on adding concrete examples from real projects.\n\nPractise system design and architecture questions.\n\nKeep up the daily practice sessions!",
            "improvements": [
                {"icon": "💡", "title": "STAR Method Practice", "description": "Write 10 STAR stories from past projects this week.", "tag_label": "HIGH IMPACT", "tag_color": "coral"},
                {"icon": "🏗️", "title": "System Design Basics", "description": "Study architecture patterns and practice designing common systems.", "tag_label": "TECHNICAL", "tag_color": "sky"},
                {"icon": "📖", "title": "Project Story Bank", "description": "Document 5 projects with specific metrics and outcomes.", "tag_label": "STORYTELLING", "tag_color": "emerald"},
            ]
        }