from django.contrib import admin
from .models import (
    UserProfile, Roadmap, RoadmapWeek, WeekResource,
    WeekTask, UserSkill, SkillGap, SkillProgress,
    AIInsight, SkillGapPriority
)

class WeekResourceInline(admin.TabularInline):
    model  = WeekResource
    extra  = 0
    fields = ['emoji', 'name', 'url', 'order']

class WeekTaskInline(admin.TabularInline):
    model  = WeekTask
    extra  = 0
    fields = ['description', 'est_hours', 'task_type', 'is_done', 'order']

class RoadmapWeekInline(admin.TabularInline):
    model  = RoadmapWeek
    extra  = 0
    fields = ['week_number', 'week_end', 'title', 'status', 'order']

class SkillGapInline(admin.TabularInline):
    model  = SkillGap
    extra  = 0
    fields = ['skill_name', 'status', 'level', 'order']

class SkillProgressInline(admin.TabularInline):
    model  = SkillProgress
    extra  = 0
    fields = ['skill_name', 'percentage', 'order']

class AIInsightInline(admin.TabularInline):
    model  = AIInsight
    extra  = 0
    fields = ['icon', 'title', 'order']

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display  = ['user', 'github_username', 'github_connected', 'experience_level', 'github_repos']
    list_filter   = ['github_connected', 'experience_level']
    search_fields = ['user__username', 'github_username']


@admin.register(Roadmap)
class RoadmapAdmin(admin.ModelAdmin):
    list_display  = ['user', 'title', 'target_role', 'timeline_months', 'progress_pct', 'status', 'version', 'created_at']
    list_filter   = ['status', 'timeline_months']
    search_fields = ['user__username', 'target_role', 'title']
    readonly_fields = ['progress_pct', 'created_at', 'updated_at']
    inlines       = [RoadmapWeekInline, SkillGapInline, SkillProgressInline, AIInsightInline]


@admin.register(RoadmapWeek)
class RoadmapWeekAdmin(admin.ModelAdmin):
    list_display  = ['roadmap', 'week_number', 'week_end', 'title', 'status', 'order']
    list_filter   = ['status']
    search_fields = ['title', 'roadmap__user__username']
    inlines       = [WeekResourceInline, WeekTaskInline]


@admin.register(WeekResource)
class WeekResourceAdmin(admin.ModelAdmin):
    list_display  = ['week', 'emoji', 'name', 'url']
    search_fields = ['name']


@admin.register(WeekTask)
class WeekTaskAdmin(admin.ModelAdmin):
    list_display  = ['week', 'description', 'is_done', 'task_type', 'est_hours']
    list_filter   = ['is_done', 'task_type']
    search_fields = ['description']


@admin.register(UserSkill)
class UserSkillAdmin(admin.ModelAdmin):
    list_display  = ['roadmap', 'skill_name', 'level']
    search_fields = ['skill_name']


@admin.register(SkillGap)
class SkillGapAdmin(admin.ModelAdmin):
    list_display  = ['roadmap', 'skill_name', 'status', 'level']
    list_filter   = ['status']
    search_fields = ['skill_name']


@admin.register(SkillProgress)
class SkillProgressAdmin(admin.ModelAdmin):
    list_display  = ['roadmap', 'skill_name', 'target_percentage']
    search_fields = ['skill_name']


@admin.register(AIInsight)
class AIInsightAdmin(admin.ModelAdmin):
    list_display  = ['roadmap', 'icon', 'title']
    search_fields = ['title']


@admin.register(SkillGapPriority)
class SkillGapPriorityAdmin(admin.ModelAdmin):
    list_display  = ['roadmap', 'updated_at']
    search_fields = ['roadmap__target_role']