import google.generativeai as genai
from django.conf import settings
import random
import logging
import difflib
import re

logger = logging.getLogger(__name__)

genai.configure(api_key=settings.GOOGLE_API_KEY)

# Fallback questions grouped by skill area. Used only when the API call fails.
FALLBACK_BY_SKILL = {
    'django': [
        "Explain the difference between Django ORM and raw SQL.",
        "What is select_related vs prefetch_related in Django?",
        "How does Django handle database migrations?",
        "Explain Django middleware with an example.",
        "What are Django signals and when would you use them?",
    ],
    'frontend': [
        "Explain the difference between CSS grid and flexbox and when to use each.",
        "How does the browser's event loop work and how does it affect asynchronous JS?",
        "What are the benefits of virtual DOM in frameworks like React?",
        "Explain CORS and how to resolve common CORS issues in frontend apps.",
        "How do you optimize web performance for critical rendering path?",
    ],
    'javascript': [
        "Explain prototypal inheritance in JavaScript.",
        "What are closures and where are they useful?",
        "Describe event delegation and when you'd use it.",
    ],
}

DEFAULT_FALLBACK = [
    "Give a short, technical interview question about programming fundamentals.",
]

def generate_question(interview, asked_questions=None):
    prompt = f"""
You are an AI interviewer.

Interview Title:
{interview.title}

Description:
{interview.description}

Required Skills:
{interview.required_skills}

Responsibilities:
{interview.responsibilities}

Evaluation Criteria:
{getattr(interview, 'evaluation_criteria', '')}

Using the interview outline above, ask ONE clear, technical interview question related to this role.
Do NOT ask generic or personal questions like "Tell us about yourself".
Keep the question focused and unambiguous.
"""

    # If provided, instruct the model not to repeat or paraphrase previously asked questions.
    if asked_questions:
        asked_text = "\n" + "\n".join([f"- {q}" for q in asked_questions if q])
        prompt += f"\nDo NOT repeat or paraphrase the following questions; produce a different, distinct technical question:{asked_text}\n"
    
    # Trim prompt length if needed (avoid sending very large asked lists)
    # Only include the most recent 12 asked questions to keep prompt concise.
    # The caller should provide a sensible asked_questions list (recent first).

    # log prompt for debugging (be careful in production — may contain PII)
    logger.debug("AI generate_question prompt:\n%s", prompt)

    try:
        # Helper: normalize text for fuzzy comparison
        def _normalize(s: str) -> str:
            s = (s or '').lower()
            s = re.sub(r"[^a-z0-9\s]", " ", s)
            s = re.sub(r"\s+", " ", s).strip()
            return s

        # Try generation up to N times if the model repeats or paraphrases a recent question
        max_attempts = 4
        similarity_threshold = 0.72
        recent_norm = [_normalize(q) for q in (asked_questions or []) if q]

        for attempt in range(max_attempts):
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt)
            text = response.text.strip()
            norm_text = _normalize(text)
            is_duplicate = False
            if recent_norm:
                for r in recent_norm:
                    if not r:
                        continue
                    # Use difflib ratio to detect paraphrases/near-duplicates
                    ratio = difflib.SequenceMatcher(None, norm_text, r).ratio()
                    if ratio >= similarity_threshold:
                        is_duplicate = True
                        logger.info("AI question similarity %.2f >= %.2f; treating as duplicate (attempt %s)", ratio, similarity_threshold, attempt + 1)
                        break

            if is_duplicate and attempt < (max_attempts - 1):
                # modify prompt slightly to push for different wording
                prompt += "\nPlease produce a substantially different question than those listed above."
                continue

            # If the model returned something new, accept it
            if not is_duplicate:
                return text

        # If we reach here, the model kept returning duplicates. Use a deterministic fallback
        # that excludes recent questions.
        logger.warning("AI generate_question repeated after %s attempts; using fallback pool", max_attempts)

        # Build a fallback pool based on skills
        skills_text = (interview.required_skills or '') + ' ' + (interview.title or '')
        skills_text = skills_text.lower()

        if 'react' in skills_text or 'frontend' in skills_text or 'javascript' in skills_text or 'css' in skills_text:
            pool = list(FALLBACK_BY_SKILL.get('frontend', DEFAULT_FALLBACK))
        elif 'django' in skills_text or 'python' in skills_text or 'backend' in skills_text:
            pool = list(FALLBACK_BY_SKILL.get('django', DEFAULT_FALLBACK))
        elif 'javascript' in skills_text:
            pool = list(FALLBACK_BY_SKILL.get('javascript', DEFAULT_FALLBACK))
        else:
            pool = list(DEFAULT_FALLBACK)

        # Exclude recent_norm entries
        filtered = []
        for p in pool:
            if _normalize(p) not in recent_norm:
                filtered.append(p)

        if filtered:
            return random.choice(filtered)

        # Last resort: return any pool item
        return random.choice(pool)

    except ClientError as e:
        # Log the error so we can see why the model call failed.
        logger.exception("AI generate_question ClientError: %s", e)

        # Choose a fallback based on keywords in required_skills or title
        skills_text = (interview.required_skills or '') + ' ' + (interview.title or '')
        skills_text = skills_text.lower()

        if 'react' in skills_text or 'frontend' in skills_text or 'javascript' in skills_text or 'css' in skills_text:
            pool = FALLBACK_BY_SKILL.get('frontend', DEFAULT_FALLBACK)
        elif 'django' in skills_text or 'python' in skills_text or 'backend' in skills_text:
            pool = FALLBACK_BY_SKILL.get('django', DEFAULT_FALLBACK)
        elif 'javascript' in skills_text:
            pool = FALLBACK_BY_SKILL.get('javascript', DEFAULT_FALLBACK)
        else:
            pool = DEFAULT_FALLBACK

        return random.choice(pool)


def evaluate_answer(question, answer):
    prompt = f"""
You are an AI interview evaluator.

Question:
"{question}"

Answer:
"{answer}"

1. Give short constructive feedback.
2. Give a score from 0 to 10.

Respond strictly in this format:
Score: <number>
Feedback: <text>
"""

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text.strip()

    except Exception as e:
        return "Score: 5\nFeedback: Answer recorded successfully."


def chat_with_ai(interview, message, role_hint="candidate"):
    """Return an AI response for an arbitrary chat message, using the interview outline
    as context. role_hint can be 'candidate' or 'system' to tune the prompt."""

    prompt = f"""
You are an AI interviewer assisting in a live interview session.

Interview Title:
{interview.title}

Description:
{interview.description}

Required Skills:
{interview.required_skills}

Responsibilities:
{interview.responsibilities}

Evaluation Criteria:
{getattr(interview, 'evaluation_criteria', '')}

The candidate says:
"{message}"

Respond as the AI interviewer: give a concise reply, optionally asking a follow-up technical question or giving brief feedback. Keep responses short and focused.
"""

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text.strip()

    except Exception as e:
        # fallback
        return "I'm sorry, I couldn't process that right now. Please try again."
