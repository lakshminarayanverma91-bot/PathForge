from django.db import models
from django.contrib.auth.models import User
import uuid

class StartupIdea(models.Model):

    INDUSTRY_CHOICES = (
        ('edtech', 'EdTech'),
        ('fintech', 'FinTech'),
        ('healthtech', 'HealthTech'),
        ('saas', 'SaaS / B2B'),
        ('e-commerce', 'E-Commerce'),
        ('devtools', 'Developer Tools'),
        ('climate-tech', 'Climate Tech'),
        ('deep-tech', 'Deep Tech / AI')
    )

    MARKET_CHOICES = (
        ('students', 'Students / College'),
        ('businesses', 'Small Businesses'),
        ('enterprise', 'Enterprise'),
        ('consumers', 'Consumers (B2C)'),
        ('devs', 'Developers'),
        ('healthcare', 'Healthcare Providers'),
        ('government', 'Government / Public Sector')
    )

    STAGE_CHOICES = (
        ('idea', 'Idea Stage'),
        ('mvp', 'Prototype / MVP'),
        ('revenue', 'Early Revenue'),
        ('growth', 'Growth Stage')
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    idea_text = models.TextField()
    idea_name = models.CharField(max_length=200, blank=True)
    industry = models.CharField(max_length=20, choices=INDUSTRY_CHOICES)
    market = models.CharField(max_length=20, choices=MARKET_CHOICES)
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES)
    ai_edge_insight = models.TextField(blank=True)
    is_saved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.idea_name}"

class ViabilityData(models.Model):

    VERDICT_CHOICES = (
        ('strong',   'Strong Market Potential'),
        ('moderate', 'Moderate Market Potential'),
        ('weak',     'Weak Market Potential'),
        ('risky',    'High Risk — Proceed Carefully')
    )

    analysis = models.OneToOneField(StartupIdea, on_delete=models.CASCADE, related_name='viability')
    score = models.DecimalField(max_digits=3, decimal_places=1)
    verdict         = models.CharField(max_length=10, choices=VERDICT_CHOICES)
    market_pct      = models.IntegerField()
    competitive_pct = models.IntegerField()
    scalability_pct = models.IntegerField()
    revenue_pct     = models.IntegerField()
    geography       = models.CharField(max_length=100)
    business_type = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.analysis.idea_name} — {self.score}/10"

class SWOTAnalysis(models.Model):

    analysis = models.OneToOneField(StartupIdea, on_delete=models.CASCADE, related_name='swot')
    strengths = models.JSONField(default=list)
    weaknesses = models.JSONField(default=list)
    opportunities = models.JSONField(default=list)
    threats = models.JSONField(default=list)

    def __str__(self):
        return f"{self.analysis.idea_name} — SWOT"

class MarketSize(models.Model):

    analysis = models.OneToOneField(StartupIdea, on_delete=models.CASCADE, related_name='market_size')
    description = models.TextField()
    tam = models.CharField(max_length=100)
    sam = models.CharField(max_length=100)
    som = models.CharField(max_length=100)
    cagr = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.analysis.idea_name} — TAM: {self.tam}"

class Competitor(models.Model):

    THREAT_CHOICES = (
        ('high',   'High'),
        ('medium', 'Medium'),
        ('low',    'Low')
    )

    analysis = models.ForeignKey(StartupIdea, on_delete=models.CASCADE, related_name='competitors')
    name         = models.CharField(max_length=200)
    description  = models.TextField()
    threat_level = models.CharField(max_length=10, choices=THREAT_CHOICES)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.name} ({self.threat_level})"

class AIInsight(models.Model):

    INSIGHT_TYPES = (
        ('advantage',    'Biggest Advantage'),
        ('risk',         'Biggest Risk'),
        ('monetization', 'Monetization Path')
    )

    analysis = models.ForeignKey(StartupIdea, on_delete=models.CASCADE, related_name='insights')
    insight_type = models.CharField(max_length=20, choices=INSIGHT_TYPES)
    content = models.TextField()

    def __str__(self):
        return f"{self.analysis.idea_name} — {self.insight_type}"

class BusinessBrief(models.Model):

    analysis = models.OneToOneField(StartupIdea, on_delete=models.CASCADE, related_name='brief')
    problem_solution = models.TextField()
    problem_highlight = models.CharField(max_length=200, blank=True)
    business_model = models.TextField()
    business_highlight = models.CharField(max_length=200, blank=True)
    gtm_strategy = models.TextField()
    gtm_highlight = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.analysis.idea_name} — Brief"
