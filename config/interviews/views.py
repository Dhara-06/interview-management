from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Interview, InterviewAnswer, InterviewResult, AskedQuestion
from .ai import generate_question, evaluate_answer
from .forms import InterviewForm
from django.contrib import messages
from accounts.models import Profile
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Avg, Max
from types import SimpleNamespace
from django.conf import settings
from django.contrib.auth.models import User
import json

@login_required
def interview_detail(request, interview_id):
    interview = get_object_or_404(Interview, id=interview_id)
    
    # Get user role
    user_role = None
    try:
        profile = Profile.objects.get(user=request.user)
        user_role = profile.role
    except Profile.DoesNotExist:
        pass
    
    # Check if user is the creator of this interview
    is_creator = interview.created_by == request.user
    
    return render(request, "interviews/interview_detail.html", {
        "interview": interview,
        "user_role": user_role,
        "is_creator": is_creator
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

        # Mark any AskedQuestion records for this interview/candidate/question as answered
        try:
            AskedQuestion.objects.filter(
                interview=interview,
                candidate=request.user,
                question_text=question,
                answered=False
            ).update(answered=True)
        except Exception:
            pass

        return redirect("interview_session", interview_id=interview.id)

    # 🟢 Generate NEXT question
    # Gather previously asked questions for this candidate & interview to avoid repeats
    prev_answers = InterviewAnswer.objects.filter(interview=interview, candidate=request.user).order_by('-question_number')
    asked_db = [a.question for a in prev_answers[:12]]

    # Also track displayed (not-yet-saved) questions in session to avoid repeats
    session_key = f"asked_{interview.id}_{request.user.id}"
    asked_session = request.session.get(session_key, [])

    # Combine DB + session (recent first)
    asked = asked_db + asked_session

    question = generate_question(interview, asked_questions=asked)

    # Remember displayed question in session so subsequent generations avoid it
    # Keep only the most recent 24 entries to limit session size
    asked_session = [question] + asked_session
    request.session[session_key] = asked_session[:24]
    request.session.modified = True

    # Persist displayed question so it's remembered across sessions
    try:
        if not AskedQuestion.objects.filter(interview=interview, candidate=request.user, question_text=question, answered=False).exists():
            AskedQuestion.objects.create(interview=interview, candidate=request.user, question_text=question)
    except Exception:
        # If DB unavailable or other error, ignore—session will still prevent immediate repeats
        logger = None

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
    # This view was removed; redirect to results.
    from django.shortcuts import redirect
    return redirect('hr_results')


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


@require_POST
def api_callback(request, interview_id):
    """Endpoint for external tool (e.g., Gemini tool use) to POST evaluation results.

    Expected JSON body example:
    {
      "token": "<callback-token>" ,
      "candidate_username": "user1",
      "overall_score": 78,
      "overall_feedback": "Good answers...",
      "answers": [
        {"question_number": 1, "question": "...", "answer": "...", "ai_score": 8, "ai_feedback":"..."},
        ...
      ]
    }
    """

    # Simple token auth (compare to settings.GEMINI_CALLBACK_TOKEN)
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({"ok": False, "error": "invalid_json"}, status=400)

    token = payload.get('token') or request.headers.get('X-Callback-Token')
    if not token or token != getattr(settings, 'GEMINI_CALLBACK_TOKEN', None):
        return JsonResponse({"ok": False, "error": "forbidden"}, status=403)

    candidate_username = payload.get('candidate_username')
    if not candidate_username:
        return JsonResponse({"ok": False, "error": "missing_candidate"}, status=400)

    try:
        candidate = User.objects.get(username=candidate_username)
    except User.DoesNotExist:
        return JsonResponse({"ok": False, "error": "candidate_not_found"}, status=404)

    interview = get_object_or_404(Interview, id=interview_id)

    # Store / update per-answer results
    answers = payload.get('answers', [])
    for a in answers:
        qnum = a.get('question_number')
        question = a.get('question', '')
        answer_text = a.get('answer', '')
        ai_score = a.get('ai_score')
        ai_feedback = a.get('ai_feedback', '')

        if qnum is None:
            continue

        InterviewAnswer.objects.update_or_create(
            interview=interview,
            candidate=candidate,
            question_number=qnum,
            defaults={
                'question': question,
                'answer': answer_text,
                'ai_score': ai_score,
                'ai_feedback': ai_feedback,
            }
        )

    # Store overall result
    overall_score = payload.get('overall_score')
    overall_feedback = payload.get('overall_feedback', '')

    result = InterviewResult.objects.create(
        interview=interview,
        candidate=candidate,
        overall_score=overall_score,
        overall_feedback=overall_feedback,
        raw_payload=payload,
    )

    return JsonResponse({"ok": True, "result_id": result.id})


@login_required
def hr_results(request):
    # Show only results for interviews created by this HR user
    try:
        profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        messages.error(request, "Profile not found. Access denied.")
        return redirect("hr_dashboard")
    
    if profile.role != "HR":
        messages.error(request, "Only HR users can view results.")
        return redirect("candidate_dashboard")
    
    # Filter results to show only interviews created by this HR user
    persisted = list(InterviewResult.objects.filter(
        interview__created_by=request.user
    ).select_related('candidate', 'interview').order_by('-created_at'))

    # Build a list of result objects. Start with persisted InterviewResult records.
    results_list = []
    existing_pairs = set()
    for r in persisted:
        results_list.append(r)
        existing_pairs.add((r.interview_id, r.candidate_id))

    # For any interview/candidate pairs that have answers but no InterviewResult yet,
    # compute an aggregated score and include them as transient results.
    # Filter to show only interviews created by this HR user
    agg = InterviewAnswer.objects.filter(
        interview__created_by=request.user
    ).values('interview_id', 'candidate_id').annotate(
        avg_score=Avg('ai_score'), last_seen=Max('created_at')
    )

    from django.contrib.auth import get_user_model
    User = get_user_model()

    for a in agg:
        pair = (a['interview_id'], a['candidate_id'])
        if pair in existing_pairs:
            continue
        try:
            interview = Interview.objects.get(id=a['interview_id'])
            candidate = User.objects.get(id=a['candidate_id'])
        except (Interview.DoesNotExist, User.DoesNotExist):
            continue

        pseudo = SimpleNamespace(
            id=None,
            interview=interview,
            candidate=candidate,
            overall_score=round(a['avg_score'] or 0, 1),
            overall_feedback='(auto-aggregated from answers)',
            created_at=a['last_seen']
        )
        results_list.append(pseudo)

    # Sort by created_at desc
    results_list.sort(key=lambda x: x.created_at or 0, reverse=True)

    return render(request, "interviews/hr_results.html", {"results": results_list})


@login_required
def hr_view_result(request, result_id):
    result = get_object_or_404(InterviewResult, id=result_id)
    # Gather per-question answers for this interview & candidate
    answers = InterviewAnswer.objects.filter(interview=result.interview, candidate=result.candidate).order_by('question_number')
    return render(request, "interviews/hr_result_detail.html", {"result": result, "answers": answers})


@login_required
def hr_view_result_by_candidate(request, interview_id, candidate_id):
    interview = get_object_or_404(Interview, id=interview_id)
    from django.contrib.auth import get_user_model
    User = get_user_model()
    candidate = get_object_or_404(User, id=candidate_id)

    answers = InterviewAnswer.objects.filter(interview=interview, candidate=candidate).order_by('question_number')
    avg = answers.aggregate(avg_score=Avg('ai_score'))['avg_score']

    pseudo = SimpleNamespace(
        id=None,
        interview=interview,
        candidate=candidate,
        overall_score=round(avg or 0, 1),
        overall_feedback='(auto-aggregated from answers)',
        created_at=None,
    )

    return render(request, "interviews/hr_result_detail.html", {"result": pseudo, "answers": answers})

@login_required
@login_required
@require_POST
def delete_answer(request, answer_id):
    answer = get_object_or_404(InterviewAnswer, id=answer_id)

    # Permission check: only HR users may delete candidate answers
    try:
        profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        messages.error(request, "Profile not found. Access denied.")
        return redirect("hr_results")

    if profile.role != "HR":
        messages.error(request, "Only HR users can delete answers.")
        return redirect("hr_results")

    interview = answer.interview
    candidate = answer.candidate

    answer.delete()
    messages.success(request, "Answer deleted.")

    # Prefer redirecting back to the page that submitted the delete (safe check)
    next_url = request.POST.get('next') or request.GET.get('next')
    if next_url and next_url.startswith('/'):
        return redirect(next_url)

    # If no next provided, prefer to show the result detail (persisted result if exists,
    # otherwise the candidate-by-interview view)
    try:
        result = InterviewResult.objects.get(interview=interview, candidate=candidate)
        return redirect('hr_view_result', result_id=result.id)
    except InterviewResult.DoesNotExist:
        return redirect('hr_view_result_by_candidate', interview_id=interview.id, candidate_id=candidate.id)


@login_required
@require_POST
def hr_delete_result(request, result_id):
    """Allow HR users to delete a persisted InterviewResult record."""
    from django.shortcuts import redirect

    # Permission check: ensure user is HR
    try:
        profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        messages.error(request, "Profile not found. Access denied.")
        return redirect("hr_results")

    if profile.role != "HR":
        messages.error(request, "Only HR users can delete results.")
        return redirect("hr_results")

    result = get_object_or_404(InterviewResult, id=result_id)

    # Delete only the aggregated/persisted InterviewResult record.
    result.delete()
    messages.success(request, "Result deleted successfully.")
    return redirect("hr_results")