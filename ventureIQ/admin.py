from django.contrib import admin
from .models import StartupIdea, ViabilityData, SWOTAnalysis, MarketSize, Competitor, AIInsight, BusinessBrief

admin.site.register(StartupIdea)
admin.site.register(ViabilityData)
admin.site.register(SWOTAnalysis)
admin.site.register(MarketSize)
admin.site.register(Competitor)
admin.site.register(AIInsight)
admin.site.register(BusinessBrief)