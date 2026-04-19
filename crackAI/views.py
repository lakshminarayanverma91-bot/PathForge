import json
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import (
    InterviewSession,
    InterviewQuestion,
    SessionResult,
    ImprovementPlan,
    QuestionCache,
)
from .gemini_service import (
    generate_questions,
    evaluate_answer,
    generate_session_report,
)

def _body(request) -> dict:
    try:
        return json.loads(request.body)
    except Exception:
        return {}

@login_required
def crackai_home(request):
    recent_sessions = InterviewSession.objects.filter(
        user=request.user,
        status='completed'
    ).select_related('result').order_by('-created_at')[:10]

    context = {
        'recent_sessions': recent_sessions,
    }
    return render(request, 'dashboard/crackAI.html', context)

@login_required
@require_POST
def start_session(request):

    data = _body(request)
    role            = data.get('role', 'Frontend Developer')
    interview_type  = data.get('interview_type', 'Technical')
    difficulty      = data.get('difficulty', 'Medium')
    question_count  = int(data.get('question_count', 8))
    time_per_q      = data.get('time_per_question', '5min')

    session = InterviewSession.objects.create(
        user=request.user,
        role=role,
        interview_type=interview_type,
        difficulty=difficulty,
        question_count=question_count,
        time_per_question=time_per_q,
        status='in_progress',
    )

    cached = QuestionCache.objects.filter(
        role=role,
        interview_type=interview_type,
        difficulty=difficulty,
    ).order_by('?')[:question_count]

    if cached.count() >= question_count:
        questions_data = [
            {
                "question_text": q.question_text,
                "tags": q.tags,
                "hint": q.hint,
            }
            for q in cached
        ]
    else:
        questions_data = generate_questions(role, interview_type, difficulty, question_count)
        for q in questions_data:
            QuestionCache.objects.get_or_create(
                role=role,
                interview_type=interview_type,
                difficulty=difficulty,
                question_text=q.get('question_text', ''),
                defaults={
                    'tags': q.get('tags', []),
                    'hint': q.get('hint', ''),
                }
            )

    question_objects = []
    for i, q in enumerate(questions_data, 1):
        obj = InterviewQuestion.objects.create(
            session=session,
            order=i,
            question_text=q.get('question_text', ''),
            tags=q.get('tags', []),
            hint=q.get('hint', ''),
        )
        question_objects.append({
            "id": str(obj.id),
            "order": obj.order,
            "question_text": obj.question_text,
            "tags": obj.tags,
            "hint": obj.hint,
        })

    return JsonResponse({
        "success": True,
        "session_id": str(session.id),
        "questions": question_objects,
    })

@login_required
@require_POST
def submit_answer(request, question_id):

    question = get_object_or_404(
        InterviewQuestion,
        id=question_id,
        session__user=request.user
    )
    data = _body(request)

    answer = data.get('answer', '').strip()
    time_taken = int(data.get('time_taken_seconds', 0))

    is_skipped = (not answer or answer == '[SKIPPED]')

    evaluation = evaluate_answer(
        question=question.question_text,
        answer=answer or '[SKIPPED]',
        role=question.session.role,
        difficulty=question.session.difficulty,
    )

    question.user_answer        = answer
    question.is_answered        = not is_skipped
    question.is_skipped         = is_skipped
    question.time_taken_seconds = time_taken
    question.communication_score = evaluation.get('communication_score')
    question.technical_score    = evaluation.get('technical_score')
    question.confidence_score   = evaluation.get('confidence_score')
    question.overall_score      = evaluation.get('overall_score')
    question.clarity_score      = evaluation.get('clarity_score')
    question.examples_score     = evaluation.get('examples_score')
    question.depth_score        = evaluation.get('depth_score')
    question.length_score       = evaluation.get('length_score')
    question.ai_feedback        = evaluation.get('ai_feedback', '')
    question.save()

    return JsonResponse({
        "success": True,
        "question_id": str(question.id),
        "communication_score": evaluation.get('communication_score'),
        "technical_score":     evaluation.get('technical_score'),
        "confidence_score":    evaluation.get('confidence_score'),
        "overall_score":       evaluation.get('overall_score'),
        "clarity_score":       evaluation.get('clarity_score'),
        "examples_score":      evaluation.get('examples_score'),
        "depth_score":         evaluation.get('depth_score'),
        "length_score":        evaluation.get('length_score'),
        "ai_feedback":         evaluation.get('ai_feedback', ''),
        "tip":                 evaluation.get('tip', ''),
    })

@login_required
@require_POST
def end_session(request, session_id):

    session = get_object_or_404(InterviewSession, id=session_id, user=request.user)
    data = _body(request)

    duration = int(data.get('duration_seconds', 0))
    session.duration_seconds = duration
    session.status = 'completed'

    questions = session.questions.all()
    qa_list = []
    scores = []

    for q in questions:
        qa_list.append({
            "question": q.question_text,
            "answer": q.user_answer or '[SKIPPED]',
            "score": q.overall_score or 0,
        })
        if q.overall_score is not None:
            scores.append(q.overall_score)

    overall = round(sum(scores) / len(scores), 1) if scores else 0
    comm    = round(sum(q.communication_score or 0 for q in questions) / max(len(questions), 1), 1)
    tech    = round(sum(q.technical_score or 0 for q in questions) / max(len(questions), 1), 1)
    conf    = round(sum(q.confidence_score or 0 for q in questions) / max(len(questions), 1), 1)

    session.overall_score       = overall
    session.communication_score = comm
    session.technical_score     = tech
    session.confidence_score    = conf
    session.save()

    report = generate_session_report(
        role=session.role,
        interview_type=session.interview_type,
        difficulty=session.difficulty,
        questions_and_answers=qa_list,
        overall_score=overall,
    )

    result = SessionResult.objects.create(
        session=session,
        grade_label=report.get('grade_label', 'GOOD EFFORT'),
        grade_title=report.get('grade_title', 'Keep Practising'),
        grade_message=report.get('grade_message', ''),
        communication_score=report.get('communication_score', comm),
        technical_score=report.get('technical_score', tech),
        confidence_score=report.get('confidence_score', conf),
        examples_score=report.get('examples_score', 0),
        structure_score=report.get('structure_score', 0),
        strengths=report.get('strengths', []),
        weaknesses=report.get('weaknesses', []),
        ai_feedback=report.get('ai_feedback', ''),
    )

    for i, imp in enumerate(report.get('improvements', [])):
        ImprovementPlan.objects.create(
            result=result,
            icon=imp.get('icon', '💡'),
            title=imp.get('title', ''),
            description=imp.get('description', ''),
            tag_label=imp.get('tag_label', 'HIGH IMPACT'),
            tag_color=imp.get('tag_color', 'coral'),
            order=i,
        )

    improvements = [
        {
            "icon": imp.icon,
            "title": imp.title,
            "description": imp.description,
            "tag_label": imp.tag_label,
            "tag_color": imp.tag_color,
        }
        for imp in result.improvements.all()
    ]

    return JsonResponse({
        "success": True,
        "session_id": str(session.id),
        "result": {
            "overall_score":       overall,
            "communication_score": result.communication_score,
            "technical_score":     result.technical_score,
            "confidence_score":    result.confidence_score,
            "examples_score":      result.examples_score,
            "structure_score":     result.structure_score,
            "grade_label":         result.grade_label,
            "grade_title":         result.grade_title,
            "grade_message":       result.grade_message,
            "strengths":           result.strengths,
            "weaknesses":          result.weaknesses,
            "ai_feedback":         result.ai_feedback,
            "improvements":        improvements,
            "duration_seconds":    duration,
            "questions_answered":  session.questions_answered(),
            "total_questions":     session.total_questions(),
            "role":                session.role,
        }
    })

@login_required
def session_history(request):

    sessions = InterviewSession.objects.filter(
        user=request.user,
        status='completed'
    ).select_related('result').order_by('-created_at')

    data = []
    for s in sessions:
        data.append({
            "session_id":   str(s.id),
            "role":         s.role,
            "interview_type": s.interview_type,
            "difficulty":   s.difficulty,
            "overall_score": s.overall_score or 0,
            "grade_label":  s.result.grade_label if hasattr(s, 'result') else '',
            "questions_answered": s.questions_answered(),
            "total_questions": s.total_questions(),
            "duration_seconds": s.duration_seconds,
            "created_at":   s.created_at.strftime('%d %b %Y, %I:%M %p'),
        })

    return JsonResponse({"success": True, "sessions": data})

@login_required
def session_detail(request, session_id):

    session = get_object_or_404(InterviewSession, id=session_id, user=request.user)

    questions = []
    for q in session.questions.all():
        questions.append({
            "order":         q.order,
            "question_text": q.question_text,
            "tags":          q.tags,
            "hint":          q.hint,
            "user_answer":   q.user_answer,
            "is_skipped":    q.is_skipped,
            "overall_score": q.overall_score,
            "ai_feedback":   q.ai_feedback,
            "scores": {
                "communication": q.communication_score,
                "technical":     q.technical_score,
                "confidence":    q.confidence_score,
                "clarity":       q.clarity_score,
                "examples":      q.examples_score,
                "depth":         q.depth_score,
                "length":        q.length_score,
            }
        })

    result_data = {}
    if hasattr(session, 'result'):
        r = session.result
        result_data = {
            "grade_label":         r.grade_label,
            "grade_title":         r.grade_title,
            "grade_message":       r.grade_message,
            "communication_score": r.communication_score,
            "technical_score":     r.technical_score,
            "confidence_score":    r.confidence_score,
            "examples_score":      r.examples_score,
            "structure_score":     r.structure_score,
            "strengths":           r.strengths,
            "weaknesses":          r.weaknesses,
            "ai_feedback":         r.ai_feedback,
            "improvements": [
                {
                    "icon":        imp.icon,
                    "title":       imp.title,
                    "description": imp.description,
                    "tag_label":   imp.tag_label,
                    "tag_color":   imp.tag_color,
                }
                for imp in r.improvements.all()
            ]
        }

    return JsonResponse({
        "success": True,
        "session": {
            "id":               str(session.id),
            "role":             session.role,
            "interview_type":   session.interview_type,
            "difficulty":       session.difficulty,
            "status":           session.status,
            "overall_score":    session.overall_score,
            "duration_seconds": session.duration_seconds,
            "created_at":       session.created_at.strftime('%d %b %Y, %I:%M %p'),
            "questions":        questions,
            "result":           result_data,
        }
    })

@login_required
@require_POST
def abandon_session(request, session_id):

    session = get_object_or_404(InterviewSession, id=session_id, user=request.user)
    session.status = 'abandoned'
    session.save()
    return JsonResponse({"success": True})