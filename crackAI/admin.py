from django.contrib import admin
from .models import (
    InterviewSession,
    InterviewQuestion,
    SessionResult,
    ImprovementPlan,
    QuestionCache,
)


class InterviewQuestionInline(admin.TabularInline):

    model = InterviewQuestion
    extra = 0
    readonly_fields = ('order', 'question_text', 'user_answer', 'overall_score', 'ai_feedback')
    fields = ('order', 'question_text', 'user_answer', 'overall_score', 'is_skipped', 'ai_feedback')

class ImprovementPlanInline(admin.TabularInline):
    model = ImprovementPlan
    extra = 0

class SessionResultInline(admin.StackedInline):
    model = SessionResult
    extra = 0
    inlines = [ImprovementPlanInline]

@admin.register(InterviewSession)
class InterviewSessionAdmin(admin.ModelAdmin):
    list_display  = ('id', 'user', 'role', 'interview_type', 'difficulty', 'overall_score', 'status', 'created_at')
    list_filter   = ('role', 'interview_type', 'difficulty', 'status')
    search_fields = ('user__username', 'role')
    readonly_fields = ('id', 'created_at', 'updated_at')
    inlines = [InterviewQuestionInline, SessionResultInline]

@admin.register(InterviewQuestion)
class InterviewQuestionAdmin(admin.ModelAdmin):
    list_display  = ('session', 'order', 'is_answered', 'is_skipped', 'overall_score')
    list_filter   = ('is_answered', 'is_skipped')
    search_fields = ('question_text',)

@admin.register(SessionResult)
class SessionResultAdmin(admin.ModelAdmin):
    list_display = ('session', 'grade_label', 'overall_score_display', 'created_at')
    inlines = [ImprovementPlanInline]

    def overall_score_display(self, obj):
        return obj.session.overall_score
    overall_score_display.short_description = 'Overall Score'

@admin.register(QuestionCache)
class QuestionCacheAdmin(admin.ModelAdmin):
    list_display  = ('role', 'interview_type', 'difficulty', 'created_at')
    list_filter   = ('role', 'interview_type', 'difficulty')
    search_fields = ('question_text',)