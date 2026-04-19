import json
import requests
import google.generativeai as genai
from django.conf              import settings
from django.shortcuts         import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http              import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

from .models import (
    UserProfile, Roadmap, RoadmapWeek, WeekResource,
    WeekTask, UserSkill, SkillGap, SkillProgress,
    AIInsight, SkillGapPriority
)

genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

def build_gemini_prompt(target_role, skills, interests, experience, timeline, github_data, additional_ctx):
    skills_str    = ", ".join(skills) if skills else "Not specified"
    interests_str = ", ".join(interests) if interests else "Not specified"
    github_str    = (
        f"GitHub: {github_data['username']} | "
        f"{github_data['repos']} repos | "
        f"{github_data['contributions']} contributions | "
        f"Top languages: {', '.join(github_data.get('languages', []))}"
        if github_data else "GitHub not connected"
    )

    prompt = f"""
You are CampusPath AI — a personalised career roadmap generator for students.

Generate a complete {timeline}-month career roadmap for a student with these details:
- Target Role: {target_role}
- Experience Level: {experience}
- Current Skills: {skills_str}
- Interests: {interests_str}
- {github_str}
- Additional Context: {additional_ctx or 'None'}

Return ONLY a valid JSON object (no markdown, no explanation) with this exact structure:

{{
  "title": "Short roadmap title like 'Frontend Engineer @ Startup — 6-Month Blueprint'",
  "ai_summary": "2-3 paragraph personalized message from Gemini explaining what you found, what you changed, and key market signals. Be specific, mention the student's skills.",
  "total_weeks": 24,
  "weeks": [
    {{
      "week_number": 1,
      "week_end": 4,
      "title": "Week group title",
      "description": "What the student will learn. Be specific and practical.",
      "mini_project": "Project name",
      "key_skills": "Skill1, Skill2, Skill3",
      "status": "upcoming",
      "resources": [
        {{"name": "Resource Name", "url": "https://example.com", "emoji": "📖"}}
      ],
      "tasks": [
        {{"description": "Specific task to complete", "est_hours": "2-3 hrs", "task_type": "Core"}}
      ]
    }}
  ],
  "skill_gaps": [
    {{"skill_name": "React.js", "status": "have", "level": "Expert"}},
    {{"skill_name": "System Design", "status": "missing", "level": "Missing"}},
    {{"skill_name": "Testing", "status": "partial", "level": "Developing"}}
  ],
  "gap_priority": "Gemini's priority order text explaining which gaps to fill first and why.",
  "skill_progress": [
    {{"skill_name": "React / Frontend", "percentage": 85, "color_start": "var(--sky)", "color_end": "#8b5cf6"}},
    {{"skill_name": "System Design", "percentage": 10, "color_start": "var(--coral)", "color_end": "rgba(255,107,53,0.5)"}}
  ],
  "insights": [
    {{"icon": "📈", "title": "Pace Recommendation", "body": "Detailed insight text here."}},
    {{"icon": "🏗", "title": "Project Strategy", "body": "Detailed insight text here."}},
    {{"icon": "🎯", "title": "Interview Readiness", "body": "Detailed insight text here."}},
    {{"icon": "⚡", "title": "Quick Win This Week", "body": "Detailed insight text here."}},
    {{"icon": "🌐", "title": "Market Intelligence", "body": "Detailed insight text here."}},
    {{"icon": "🔄", "title": "Adaptive Adjustment", "body": "Detailed insight text here."}}
  ]
}}

Rules:
- Generate {timeline * 4} weeks total (4 weeks per month)
- The first week's status should be "active", rest "upcoming"
- Include 3-5 resources per week with real URLs
- Include 3-4 tasks per week
- Include 6-10 skill gaps (mix of have/partial/missing)
- Include exactly 6 insight cards
- Include 4-6 skill progress bars
- Be highly specific to the student's target role and current skills
- JSON must be valid — no trailing commas, no comments
"""
    return prompt

def save_roadmap_to_db(user, data, skills, interests, experience, timeline, additional_ctx, github_data):

    # Archive old active roadmaps
    Roadmap.objects.filter(user=user, status='active').update(status='archived')

    # Get or create roadmap version
    last_version = Roadmap.objects.filter(user=user).order_by('-version').first()
    new_version  = (last_version.version + 1) if last_version else 1

    # Create Roadmap
    roadmap = Roadmap.objects.create(
        user            = user,
        title           = data.get('title', f'{data.get("target_role", "Career")} Blueprint'),
        target_role     = data.get('target_role', ''),
        timeline_months = timeline,
        interests       = interests,
        additional_ctx  = additional_ctx,
        total_weeks     = data.get('total_weeks', timeline * 4),
        completed_weeks = 0,
        current_week    = 1,
        progress_pct    = 0.0,
        ai_summary      = data.get('ai_summary', ''),
        status          = 'active',
        version         = new_version,
    )

    # Save user's current skills
    for skill_name in skills:
        UserSkill.objects.create(roadmap=roadmap, skill_name=skill_name.strip())

    # Save weeks, resources, tasks
    for idx, week_data in enumerate(data.get('weeks', [])):
        week = RoadmapWeek.objects.create(
            roadmap      = roadmap,
            week_number  = week_data.get('week_number', idx + 1),
            week_end     = week_data.get('week_end', idx + 1),
            title        = week_data.get('title', ''),
            description  = week_data.get('description', ''),
            mini_project = week_data.get('mini_project', ''),
            key_skills   = week_data.get('key_skills', ''),
            status       = week_data.get('status', 'upcoming'),
            order        = idx,
        )

        # Resources
        for r_idx, res in enumerate(week_data.get('resources', [])):
            WeekResource.objects.create(
                week  = week,
                name  = res.get('name', ''),
                url   = res.get('url', ''),
                emoji = res.get('emoji', '📖'),
                order = r_idx,
            )

        # Tasks
        for t_idx, task in enumerate(week_data.get('tasks', [])):
            WeekTask.objects.create(
                week        = week,
                description = task.get('description', ''),
                est_hours   = task.get('est_hours', ''),
                task_type   = task.get('task_type', 'Core'),
                order       = t_idx,
            )

    # Save skill gaps
    for idx, gap in enumerate(data.get('skill_gaps', [])):
        SkillGap.objects.create(
            roadmap    = roadmap,
            skill_name = gap.get('skill_name', ''),
            status     = gap.get('status', 'missing'),
            level      = gap.get('level', 'Missing'),
            order      = idx,
        )

    # Save gap priority
    if data.get('gap_priority'):
        SkillGapPriority.objects.create(
            roadmap       = roadmap,
            priority_text = data['gap_priority'],
        )

    # Save skill progress bars
    for idx, sp in enumerate(data.get('skill_progress', [])):
        SkillProgress.objects.create(
            roadmap     = roadmap,
            skill_name  = sp.get('skill_name', ''),
            percentage  = sp.get('percentage', 0),
            color_start = sp.get('color_start', 'var(--sky)'),
            color_end   = sp.get('color_end', '#8b5cf6'),
            order       = idx,
        )

    # Save AI insights
    for idx, insight in enumerate(data.get('insights', [])):
        AIInsight.objects.create(
            roadmap = roadmap,
            icon    = insight.get('icon', '💡'),
            title   = insight.get('title', ''),
            body    = insight.get('body', ''),
            order   = idx,
        )

    # Update UserProfile with GitHub data
    profile, _ = UserProfile.objects.get_or_create(user=user)
    if github_data:
        profile.github_url       = github_data.get('url', '')
        profile.github_username  = github_data.get('username', '')
        profile.github_connected = True
        profile.github_repos     = github_data.get('repos', 0)
        profile.github_contribs  = github_data.get('contributions', 0)
    profile.experience_level = experience
    profile.save()

    return roadmap

@login_required
def campuspath_home(request):

    active_roadmap = Roadmap.objects.filter(
        user=request.user, status='active'
    ).prefetch_related(
        'weeks__resources',
        'weeks__tasks',
        'skill_gaps',
        'skill_progress',
        'insights',
        'user_skills',
    ).first()

    # All roadmaps for history panel
    all_roadmaps = Roadmap.objects.filter(user=request.user).order_by('-created_at')[:5]

    # User's GitHub profile info
    profile = UserProfile.objects.filter(user=request.user).first()

    context = {
        'roadmap':      active_roadmap,
        'all_roadmaps': all_roadmaps,
        'profile':      profile,
    }
    return render(request, 'dashboard/campuspathAI.html', context)

@login_required
@require_POST
def generate_roadmap(request):

    try:
        body = json.loads(request.body)

        target_role    = body.get('target_role', '').strip()
        skills         = body.get('skills', [])        # list of strings
        interests      = body.get('interests', [])     # list of strings
        experience     = body.get('experience', 'intermediate')
        timeline       = int(body.get('timeline', 6))
        additional_ctx = body.get('additional_ctx', '').strip()
        github_data    = body.get('github_data', None) # dict or None

        if not target_role:
            return JsonResponse({'error': 'Target role is required.'}, status=400)

        # Build prompt and call Gemini
        prompt   = build_gemini_prompt(
            target_role, skills, interests, experience,
            timeline, github_data, additional_ctx
        )
        response = model.generate_content(prompt)
        raw_text = response.text.strip()

        # Clean response (remove markdown fences if present)
        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
        raw_text = raw_text.strip()

        # ── Parse JSON ───────────────────────────────────────
        data = json.loads(raw_text)

        # Attach target_role so save_roadmap_to_db can use it
        data['target_role'] = target_role

        # ── Save everything to database ──────────────────────
        roadmap = save_roadmap_to_db(
            user           = request.user,
            data           = data,
            skills         = skills,
            interests      = interests,
            experience     = experience,
            timeline       = timeline,
            additional_ctx = additional_ctx,
            github_data    = github_data,
        )

        return JsonResponse({
            'success':    True,
            'roadmap_id': roadmap.id,
            'message':    'Roadmap generated successfully!',
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Gemini returned invalid JSON. Please try again.'}, status=500)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def roadmap_detail(request, roadmap_id):
    roadmap = get_object_or_404(Roadmap, id=roadmap_id, user=request.user)
    profile = UserProfile.objects.filter(user=request.user).first()

    context = {
        'roadmap': roadmap,
        'profile': profile,
    }
    return render(request, 'dashboard/campuspathAI.html', context)

@login_required
@require_POST
def connect_github(request):
    """
    Takes a GitHub URL, fetches public profile data via GitHub REST API.
    Returns repos count, contribution estimate, and top languages.
    """
    try:
        body     = json.loads(request.body)
        gh_url   = body.get('github_url', '').strip()

        if not gh_url:
            return JsonResponse({'error': 'GitHub URL is required.'}, status=400)

        username = gh_url.rstrip('/').split('/')[-1]

        # Fetch from GitHub REST API
        headers = {'Accept': 'application/vnd.github.v3+json'}
        if hasattr(settings, 'GITHUB_TOKEN') and settings.GITHUB_TOKEN:
            headers['Authorization'] = f"token {settings.GITHUB_TOKEN}"

        # User profile
        user_resp = requests.get(
            f'https://api.github.com/users/{username}',
            headers=headers,
            timeout=10
        )
        if user_resp.status_code != 200:
            return JsonResponse({'error': f'GitHub user "{username}" not found.'}, status=404)

        user_data = user_resp.json()
        repos     = user_data.get('public_repos', 0)

        # Top languages from repos
        repos_resp = requests.get(
            f'https://api.github.com/users/{username}/repos?per_page=10&sort=updated',
            headers=headers,
            timeout=10
        )
        languages = []
        if repos_resp.status_code == 200:
            lang_count = {}
            for repo in repos_resp.json():
                lang = repo.get('language')
                if lang:
                    lang_count[lang] = lang_count.get(lang, 0) + 1
            
            languages = sorted(lang_count, key=lang_count.get, reverse=True)[:3]

        github_data = {
            'url':           gh_url,
            'username':      username,
            'repos':         repos,
            'contributions': user_data.get('public_gists', 0) + repos * 10,  # estimate
            'languages':     languages,
            'avatar_url':    user_data.get('avatar_url', ''),
            'name':          user_data.get('name', username),
            'bio':           user_data.get('bio', ''),
        }

        return JsonResponse({'success': True, 'github_data': github_data})

    except requests.exceptions.Timeout:
        return JsonResponse({'error': 'GitHub API timed out. Please try again.'}, status=408)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_POST
def toggle_week_complete(request, week_id):
    """
    Toggles a RoadmapWeek between 'completed' and 'active'/'upcoming'.
    Updates the roadmap's progress percentage.
    """
    try:
        week = get_object_or_404(RoadmapWeek, id=week_id, roadmap__user=request.user)

        if week.status == 'completed':
            # Unmark complete
            week.status = 'upcoming'
            week.save()
            week.roadmap.completed_weeks = max(0, week.roadmap.completed_weeks - 1)
        else:
            # Mark complete
            week.status = 'completed'
            week.save()
            week.roadmap.completed_weeks += 1

        week.roadmap.recalculate_progress()

        return JsonResponse({
            'success':     True,
            'new_status':  week.status,
            'progress':    week.roadmap.progress_pct,
            'completed':   week.roadmap.completed_weeks,
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_POST
def toggle_task_done(request, task_id):
    """
    Toggles a WeekTask's is_done between True and False.
    """
    try:
        task         = get_object_or_404(WeekTask, id=task_id, week__roadmap__user=request.user)
        task.is_done = not task.is_done
        task.save()

        return JsonResponse({'success': True, 'is_done': task.is_done})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============================================================
# VIEW 7: Get Roadmap JSON — returns full roadmap as JSON
#         (used by frontend to render the roadmap dynamically)
# ============================================================
@login_required
def get_roadmap_json(request, roadmap_id):
    """
    Returns the full roadmap as JSON so the frontend can
    render it dynamically without a page reload.
    """
    roadmap = get_object_or_404(Roadmap, id=roadmap_id, user=request.user)

    # Build weeks data
    weeks_data = []
    for week in roadmap.weeks.all():
        weeks_data.append({
            'id':           week.id,
            'week_label':   week.week_label,
            'title':        week.title,
            'description':  week.description,
            'mini_project': week.mini_project,
            'key_skills':   week.key_skills,
            'status':       week.status,
            'resources': [
                {'name': r.name, 'url': r.url, 'emoji': r.emoji}
                for r in week.resources.all()
            ],
            'tasks': [
                {
                    'id':          t.id,
                    'description': t.description,
                    'is_done':     t.is_done,
                    'est_hours':   t.est_hours,
                    'task_type':   t.task_type,
                }
                for t in week.tasks.all()
            ],
        })

    # Build skill gaps data
    skill_gaps = {
        'have':    [],
        'partial': [],
        'missing': [],
    }
    for gap in roadmap.skill_gaps.all():
        skill_gaps[gap.status].append({
            'skill_name': gap.skill_name,
            'level':      gap.level,
        })

    # Build full response
    data = {
        'id':             roadmap.id,
        'title':          roadmap.title,
        'target_role':    roadmap.target_role,
        'timeline':       roadmap.timeline_months,
        'total_weeks':    roadmap.total_weeks,
        'completed_weeks':roadmap.completed_weeks,
        'current_week':   roadmap.current_week,
        'progress_pct':   roadmap.progress_pct,
        'ai_summary':     roadmap.ai_summary,
        'status':         roadmap.status,
        'version':        roadmap.version,
        'created_at':     roadmap.created_at.strftime('%d %b %Y'),
        'weeks':          weeks_data,
        'skill_gaps':     skill_gaps,
        'gap_priority':   roadmap.gap_priority.priority_text if hasattr(roadmap, 'gap_priority') else '',
        'skill_progress': [
            {
                'skill_name':  sp.skill_name,
                'percentage':  sp.percentage,
                'color_start': sp.color_start,
                'color_end':   sp.color_end,
            }
            for sp in roadmap.skill_progress.all()
        ],
        'insights': [
            {'icon': ins.icon, 'title': ins.title, 'body': ins.body}
            for ins in roadmap.insights.all()
        ],
        'user_skills': [s.skill_name for s in roadmap.user_skills.all()],
    }

    return JsonResponse(data)


# ============================================================
# VIEW 8: Update Roadmap — re-run Gemini to refresh roadmap
# ============================================================
@login_required
@require_POST
def update_roadmap(request, roadmap_id):
    """
    Re-generates the roadmap using updated market data.
    Keeps the user's original inputs but calls Gemini again.
    """
    try:
        roadmap = get_object_or_404(Roadmap, id=roadmap_id, user=request.user)
        profile = UserProfile.objects.filter(user=request.user).first()

        skills     = [s.skill_name for s in roadmap.user_skills.all()]
        interests  = roadmap.interests
        experience = profile.experience_level if profile else 'intermediate'

        github_data = None
        if profile and profile.github_connected:
            github_data = {
                'url':           profile.github_url,
                'username':      profile.github_username,
                'repos':         profile.github_repos,
                'contributions': profile.github_contribs,
                'languages':     [],
            }

        prompt   = build_gemini_prompt(
            roadmap.target_role, skills, interests, experience,
            roadmap.timeline_months, github_data, roadmap.additional_ctx
        )
        response = model.generate_content(prompt)
        raw_text = response.text.strip()

        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
        raw_text = raw_text.strip()

        data = json.loads(raw_text)
        data['target_role'] = roadmap.target_role

        # Delete old roadmap data and recreate
        roadmap.delete()

        new_roadmap = save_roadmap_to_db(
            user           = request.user,
            data           = data,
            skills         = skills,
            interests      = interests,
            experience     = experience,
            timeline       = roadmap.timeline_months,
            additional_ctx = roadmap.additional_ctx,
            github_data    = github_data,
        )

        return JsonResponse({
            'success':    True,
            'roadmap_id': new_roadmap.id,
            'message':    'Roadmap updated with latest market data!',
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============================================================
# VIEW 9: Save Progress — manual save trigger from frontend
# ============================================================
@login_required
@require_POST
def save_progress(request):
    """
    Manual save endpoint. The database auto-saves on every toggle,
    but this gives the user a confirmation. Returns latest stats.
    """
    try:
        body       = json.loads(request.body)
        roadmap_id = body.get('roadmap_id')

        roadmap = get_object_or_404(Roadmap, id=roadmap_id, user=request.user)

        return JsonResponse({
            'success':       True,
            'progress_pct':  roadmap.progress_pct,
            'completed':     roadmap.completed_weeks,
            'total':         roadmap.total_weeks,
            'message':       'Progress saved!',
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)