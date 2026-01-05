from google import genai
from google.genai.errors import ClientError
from django.conf import settings
import random

client = genai.Client(api_key=settings.GOOGLE_API_KEY)

FALLBACK_QUESTIONS = [
    "Explain the difference between Django ORM and raw SQL.",
    "What is select_related vs prefetch_related in Django?",
    "How does Django handle database migrations?",
    "Explain Django middleware with an example.",
    "What are Django signals and when would you use them?"
]

def generate_question(interview):
    prompt = f"""
You are an AI interviewer.

Interview Role:
{interview.title}

Required Skills:
{interview.required_skills}

Ask ONE clear, technical interview question related to this role.
Do NOT ask generic questions like "Tell us about yourself".
"""

    try:
        response = client.models.generate_content(
            model="models/gemini-flash-lite-latest",
            contents=prompt
        )
        return response.text.strip()

    except ClientError:
        # 🔥 IMPORTANT: technical fallback, NOT generic
        return random.choice(FALLBACK_QUESTIONS)


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
