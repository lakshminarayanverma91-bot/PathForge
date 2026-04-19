import json
import google.generativeai as genai
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
from django.conf import settings
from accounts.models import Profile
from .models import (
    StartupIdea,
    ViabilityData,
    SWOTAnalysis,
    MarketSize,
    Competitor,
    AIInsight,
    BusinessBrief,
)

genai.configure(api_key=settings.GEMINI_API_KEY)


# ── Helper (same pattern as dashboard) ──────────────────────
def _ventureiq_context(request, extra=None):
    context = {
        "user"       : request.user,
        "profile"    : Profile.objects.filter(pk=request.user.pk).first(),
        "saved_ideas": StartupIdea.objects.filter(
                            user=request.user,
                            is_saved=True
                       ).select_related('viability'),
        "total_count": StartupIdea.objects.filter(user=request.user).count(),
    }
    if extra:
        context.update(extra)
    return context


# ── Home Page ────────────────────────────────────────────────
@login_required
@ensure_csrf_cookie
def ventureIQ(request):
    return render(request, "dashboard/ventureIQ.html", _ventureiq_context(request))


# ── Analyze Idea ─────────────────────────────────────────────
@login_required
@require_POST
def ventureiq_analyze(request):

    # Step 1: Data padhna
    data     = json.loads(request.body)
    idea     = data.get('idea_text', '').strip()
    industry = data.get('industry', '')
    market   = data.get('market', '')
    stage    = data.get('stage', '')

    # Step 2: Validation
    if not idea:
        return JsonResponse({'error': 'Please describe your startup idea.'}, status=400)

    if len(idea) < 50:
        return JsonResponse({'error': 'Please describe your idea in more detail (minimum 50 characters).'}, status=400)

    # Step 3: Gemini Prompt
    prompt = f"""
You are a world-class startup analyst. Analyze the following startup idea and return ONLY valid JSON with no markdown, no extra text, no code blocks.

Startup Idea: {idea}
Industry: {industry}
Target Market: {market}
Stage: {stage}

Return this exact JSON structure:
{{
  "idea_name": "Short catchy startup name (max 5 words)",

  "viability": {{
    "score": 7.5,
    "verdict": "strong",
    "market_pct": 75,
    "competitive_pct": 60,
    "scalability_pct": 80,
    "revenue_pct": 70,
    "geography": "India · Global",
    "business_type": "B2B + B2C"
  }},

  "swot": {{
    "strengths":     ["point 1", "point 2", "point 3", "point 4"],
    "weaknesses":    ["point 1", "point 2", "point 3"],
    "opportunities": ["point 1", "point 2", "point 3", "point 4"],
    "threats":       ["point 1", "point 2", "point 3"]
  }},

  "market": {{
    "tam": "₹2,400Cr",
    "sam": "₹1,320Cr",
    "som": "₹430Cr",
    "cagr": "24%",
    "description": "2-3 sentence market overview with key stats"
  }},

  "competitors": [
    {{"name": "Competitor 1", "description": "One line about them", "threat_level": "high"}},
    {{"name": "Competitor 2", "description": "One line about them", "threat_level": "medium"}},
    {{"name": "Competitor 3", "description": "One line about them", "threat_level": "low"}}
  ],

  "ai_edge_insight": "One paragraph about the unique AI advantage this startup has over all listed competitors",

  "insights": [
    {{"type": "advantage",    "content": "2-3 sentences about the biggest competitive advantage"}},
    {{"type": "risk",         "content": "2-3 sentences about the biggest risk and how to mitigate it"}},
    {{"type": "monetization", "content": "2-3 sentences about monetization path with specific numbers"}}
  ],

  "brief": {{
    "problem_solution":   "3-4 sentences describing the problem and solution clearly",
    "problem_highlight":  "Short highlight line e.g. Core: GitHub → AI → Jobs",
    "business_model":     "3-4 sentences about revenue streams and unit economics",
    "business_highlight": "Short highlight line e.g. LTV:CAC — 1:2.4 (solid)",
    "gtm_strategy":       "3-4 sentences about go-to-market phases and targets",
    "gtm_highlight":      "Short highlight line e.g. Rev target: ₹1.2Cr by month 18"
  }}
}}

Important rules:
- verdict must be exactly one of: strong, moderate, weak, risky
- threat_level must be exactly one of: high, medium, low
- Return ONLY the JSON, nothing else
"""

    # Step 4: Gemini API Call
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        result = json.loads(response.text.strip())

    except json.JSONDecodeError:
        return JsonResponse(
            {'error': 'AI returned an invalid response. Please try again.'},
            status=500
        )
    except Exception as e:
        return JsonResponse(
            {'error': f'AI analysis failed: {str(e)}'},
            status=500
        )

    # Step 5: Database mein save karna
    try:
        # 1. Parent - StartupIdea
        idea_obj = StartupIdea.objects.create(
            user            = request.user,
            idea_text       = idea,
            idea_name       = result['idea_name'],
            industry        = industry,
            market          = market,
            stage           = stage,
            ai_edge_insight = result['ai_edge_insight'],
            is_saved        = True,
        )

        # 2. Viability Card
        v = result['viability']
        ViabilityData.objects.create(
            analysis        = idea_obj,
            score           = v['score'],
            verdict         = v['verdict'],
            market_pct      = v['market_pct'],
            competitive_pct = v['competitive_pct'],
            scalability_pct = v['scalability_pct'],
            revenue_pct     = v['revenue_pct'],
            geography       = v['geography'],
            business_type   = v['business_type'],
        )

        # 3. SWOT Card
        s = result['swot']
        SWOTAnalysis.objects.create(
            analysis      = idea_obj,
            strengths     = s['strengths'],
            weaknesses    = s['weaknesses'],
            opportunities = s['opportunities'],
            threats       = s['threats'],
        )

        # 4. Market Size Card
        m = result['market']
        MarketSize.objects.create(
            analysis    = idea_obj,
            tam         = m['tam'],
            sam         = m['sam'],
            som         = m['som'],
            cagr        = m['cagr'],
            description = m['description'],
        )

        # 5. Competitors Card (3 alag rows)
        for i, comp in enumerate(result['competitors']):
            Competitor.objects.create(
                analysis     = idea_obj,
                name         = comp['name'],
                description  = comp['description'],
                threat_level = comp['threat_level'],
                order        = i,
            )

        # 6. AI Insights Card (3 alag rows)
        for insight in result['insights']:
            AIInsight.objects.create(
                analysis     = idea_obj,
                insight_type = insight['type'],
                content      = insight['content'],
            )

        # 7. Business Brief Card
        b = result['brief']
        BusinessBrief.objects.create(
            analysis           = idea_obj,
            problem_solution   = b['problem_solution'],
            problem_highlight  = b['problem_highlight'],
            business_model     = b['business_model'],
            business_highlight = b['business_highlight'],
            gtm_strategy       = b['gtm_strategy'],
            gtm_highlight      = b['gtm_highlight'],
        )

    except Exception as e:
        return JsonResponse(
            {'error': f'Failed to save analysis: {str(e)}'},
            status=500
        )

    # Step 6: Frontend ko response bhejo
    return JsonResponse({
        'success'    : True,
        'analysis_id': str(idea_obj.id),
        'data'       : result,
    })


# ── Saved Idea Load Karna ────────────────────────────────────
@login_required
def ventureiq_load(request, pk):

    # Sirf us user ki analysis milegi, dusre ki nahi
    idea = get_object_or_404(
        StartupIdea.objects.select_related(
            'viability',
            'swot',
            'market_size',
            'brief',
        ).prefetch_related(
            'competitors',
            'insights',
        ),
        pk   = pk,
        user = request.user,
    )

    data = {
        'idea_name': idea.idea_name,
        'industry' : idea.industry,
        'stage'    : idea.stage,

        'viability': {
            'score'          : str(idea.viability.score),
            'verdict'        : idea.viability.verdict,
            'market_pct'     : idea.viability.market_pct,
            'competitive_pct': idea.viability.competitive_pct,
            'scalability_pct': idea.viability.scalability_pct,
            'revenue_pct'    : idea.viability.revenue_pct,
            'geography'      : idea.viability.geography,
            'business_type'  : idea.viability.business_type,
        },

        'swot': {
            'strengths'    : idea.swot.strengths,
            'weaknesses'   : idea.swot.weaknesses,
            'opportunities': idea.swot.opportunities,
            'threats'      : idea.swot.threats,
        },

        'market': {
            'tam'        : idea.market_size.tam,
            'sam'        : idea.market_size.sam,
            'som'        : idea.market_size.som,
            'cagr'       : idea.market_size.cagr,
            'description': idea.market_size.description,
        },

        'competitors': [
            {
                'name'        : c.name,
                'description' : c.description,
                'threat_level': c.threat_level,
            }
            for c in idea.competitors.all()
        ],

        'ai_edge_insight': idea.ai_edge_insight,

        'insights': [
            {
                'type'   : i.insight_type,
                'content': i.content,
            }
            for i in idea.insights.all()
        ],

        'brief': {
            'problem_solution'  : idea.brief.problem_solution,
            'problem_highlight' : idea.brief.problem_highlight,
            'business_model'    : idea.brief.business_model,
            'business_highlight': idea.brief.business_highlight,
            'gtm_strategy'      : idea.brief.gtm_strategy,
            'gtm_highlight'     : idea.brief.gtm_highlight,
        },
    }

    return JsonResponse({'success': True, 'data': data})


# ── Analysis Delete Karna ────────────────────────────────────
@login_required
@require_POST
def ventureiq_delete(request, pk):
    idea = get_object_or_404(StartupIdea, pk=pk, user=request.user)
    idea.delete()  # CASCADE se sab related rows bhi delete ho jayenge
    return JsonResponse({'success': True})


# ── Save / Unsave Toggle ─────────────────────────────────────
@login_required
@require_POST
def ventureiq_toggle_save(request, pk):
    idea          = get_object_or_404(StartupIdea, pk=pk, user=request.user)
    idea.is_saved = not idea.is_saved
    idea.save()
    return JsonResponse({'success': True, 'is_saved': idea.is_saved})