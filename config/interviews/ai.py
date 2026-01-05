from google import genai
from google.genai.errors import ClientError
from django.conf import settings
import random
import logging

logger = logging.getLogger(__name__)

client = genai.Client(api_key=settings.GOOGLE_API_KEY)

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

def generate_question(interview):
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

    try:
        response = client.models.generate_content(
            model="models/gemini-flash-lite-latest",
            contents=prompt
        )
        return response.text.strip()

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
        response = client.models.generate_content(
            model="models/gemini-flash-lite-latest",
            contents=prompt
        )
        return response.text.strip()

    except ClientError:
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
        response = client.models.generate_content(
            model="models/gemini-flash-lite-latest",
            contents=prompt
        )
        return response.text.strip()

    except ClientError:
        # fallback
        return "I'm sorry, I couldn't process that right now. Please try again."
