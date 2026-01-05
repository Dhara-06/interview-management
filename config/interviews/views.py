from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Interview, InterviewAnswer
from .ai import generate_question, evaluate_answer
from .forms import InterviewForm
from django.contrib import messages
from accounts.models import Profile
from django.http import JsonResponse
from django.views.decorators.http import require_POST

@login_required
def interview_detail(request, interview_id):
    interview = get_object_or_404(Interview, id=interview_id)
    return render(request, "interviews/interview_detail.html", {
        "interview": interview
    })

@login_required
def interview_session(request, interview_id):
    interview = get_object_or_404(Interview, id=interview_id)

    # How many questions already answered
    answered_count = InterviewAnswer.objects.filter(
        interview=interview,
        candidate=request.user
    ).count()

    total_questions = interview.number_of_questions

    # 🔴 INTERVIEW FINISHED → show final result
    if answered_count >= total_questions:
        answers = InterviewAnswer.objects.filter(
            interview=interview,
            candidate=request.user
        )

        scores = [a.ai_score for a in answers if a.ai_score is not None]
        average_score = sum(scores) / len(scores) if scores else 0

        return render(request, "interviews/final_result.html", {
            "total_questions": total_questions,
            "average_score": round(average_score, 1)
        })

    # 🟢 Handle submitted answer
    if request.method == "POST":
        question = request.POST.get("question")
        answer = request.POST.get("answer")

        result = evaluate_answer(question, answer)

        score = None
        feedback = result
        if "Score:" in result:
            try:
                score = int(result.split("Score:")[1].split("\n")[0].strip())
                feedback = result.split("Feedback:")[1].strip()
            except:
                pass

        InterviewAnswer.objects.create(
            interview=interview,
            candidate=request.user,
            question_number=answered_count + 1,
            question=question,
            answer=answer,
            ai_feedback=feedback,
            ai_score=score
        )

        return redirect("interview_session", interview_id=interview.id)

    # 🟢 Generate NEXT question
    question = generate_question(interview)

    progress = int((answered_count / total_questions) * 100)

    return render(request, "interviews/interview_session.html", {
        "interview": interview,
        "question": question,
        "current_question": answered_count + 1,
        "total_questions": total_questions,
        "progress": progress
    })


@login_required
def hr_view_answers(request):
    answers = InterviewAnswer.objects.select_related("interview", "candidate")
    return render(request, "interviews/hr_answers.html", {
        "answers": answers
    })


@login_required
def hr_create_interview(request):
    # Ensure user is HR
    try:
        profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        messages.error(request, "Profile not found. Access denied.")
        return redirect("hr_dashboard")

    if profile.role != "HR":
        messages.error(request, "Only HR users can create interviews.")
        return redirect("hr_dashboard")

    if request.method == "POST":
        form = InterviewForm(request.POST)
        if form.is_valid():
            interview = form.save(commit=False)
            interview.created_by = request.user
            interview.save()
            messages.success(request, "Interview created successfully.")
            return redirect("hr_dashboard")
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = InterviewForm()

    return render(request, "interviews/hr_create.html", {"form": form})


@login_required
def hr_edit_interview(request, interview_id):
    interview = get_object_or_404(Interview, id=interview_id)

    # Only the creator (HR) may edit
    if interview.created_by != request.user:
        messages.error(request, "You do not have permission to edit this interview.")
        return redirect("hr_dashboard")

    if request.method == "POST":
        form = InterviewForm(request.POST, instance=interview)
        if form.is_valid():
            form.save()
            messages.success(request, "Interview updated successfully.")
            return redirect("hr_dashboard")
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = InterviewForm(instance=interview)

    return render(request, "interviews/hr_edit.html", {"form": form, "interview": interview})


@login_required
@require_POST
def ai_chat(request, interview_id):
    """Simple endpoint to handle chat messages from the candidate and return AI responses."""
    interview = get_object_or_404(Interview, id=interview_id)

    message = request.POST.get("message", "").strip()
    if not message:
        return JsonResponse({"ok": False, "error": "empty message"}, status=400)

    # Lazy import to avoid circular issues
    from .ai import chat_with_ai

    ai_response = chat_with_ai(interview, message)

    return JsonResponse({"ok": True, "response": ai_response})

@login_required
def delete_answer(request, answer_id):
    answer = get_object_or_404(InterviewAnswer, id=answer_id)
    answer.delete()
    return redirect("hr_view_answers")