from django.db import models
from django.contrib.auth.models import User
import uuid

class InterviewSession(models.Model):

    ROLE_CHOICES = [
        ('Frontend Developer', 'Frontend Developer'),
        ('Backend Developer', 'Backend Developer'),
        ('Full Stack', 'Full Stack'),
        ('Data Analyst', 'Data Analyst'),
        ('Product Manager', 'Product Manager'),
        ('UX Designer', 'UX Designer'),
        ('ML Engineer', 'ML Engineer'),
        ('DevOps Engineer', 'DevOps Engineer'),
    ]

    TYPE_CHOICES = [
        ('Technical', 'Technical'),
        ('Behavioural', 'Behavioural'),
        ('HR Round', 'HR Round'),
        ('Mixed', 'Mixed'),
    ]

    DIFFICULTY_CHOICES = [
        ('Easy', 'Easy'),
        ('Medium', 'Medium'),
        ('Hard', 'Hard'),
    ]

    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('abandoned', 'Abandoned'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='interview_sessions')
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    interview_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='Technical')
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='Medium')
    question_count = models.IntegerField(default=8)
    time_per_question = models.CharField(max_length=20, default='5min')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    duration_seconds = models.IntegerField(default=0)
    overall_score = models.FloatField(null=True, blank=True)
    communication_score = models.FloatField(null=True, blank=True)
    technical_score = models.FloatField(null=True, blank=True)
    confidence_score = models.FloatField(null=True, blank=True)
    ai_feedback = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} — {self.role} ({self.interview_type}) [{self.status}]"

    def questions_answered(self):
        return self.questions.filter(is_answered=True).count()

    def total_questions(self):
        return self.questions.count()

class InterviewQuestion(models.Model):

    session = models.ForeignKey(InterviewSession, on_delete=models.CASCADE, related_name='questions')
    order = models.IntegerField()
    question_text = models.TextField()
    tags = models.JSONField(default=list)
    hint = models.TextField(blank=True, default='')
    user_answer = models.TextField(blank=True, default='')
    is_answered = models.BooleanField(default=False)
    is_skipped = models.BooleanField(default=False)
    time_taken_seconds = models.IntegerField(default=0)
    communication_score = models.FloatField(null=True, blank=True)
    technical_score = models.FloatField(null=True, blank=True)
    confidence_score = models.FloatField(null=True, blank=True)
    overall_score = models.FloatField(null=True, blank=True)
    ai_feedback = models.TextField(blank=True, default='')
    clarity_score = models.FloatField(null=True, blank=True)
    examples_score = models.FloatField(null=True, blank=True)
    depth_score = models.FloatField(null=True, blank=True)
    length_score = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Q{self.order} — Session {self.session.id}"

class SessionResult(models.Model):
    
    session = models.OneToOneField(InterviewSession, on_delete=models.CASCADE, related_name='result')
    grade_label = models.CharField(max_length=50, default='')
    grade_title = models.CharField(max_length=100, default='')
    grade_message = models.TextField(default='')
    communication_score = models.FloatField(default=0)
    technical_score = models.FloatField(default=0)
    confidence_score = models.FloatField(default=0)
    examples_score = models.FloatField(default=0)
    structure_score = models.FloatField(default=0)
    strengths = models.JSONField(default=list)
    weaknesses = models.JSONField(default=list)
    ai_feedback = models.TextField(default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Result — {self.session}"

class ImprovementPlan(models.Model):

    result = models.ForeignKey(SessionResult, on_delete=models.CASCADE, related_name='improvements')
    icon = models.CharField(max_length=10, default='💡')
    title = models.CharField(max_length=100)
    description = models.TextField()
    tag_label = models.CharField(max_length=50, default='HIGH IMPACT')
    tag_color = models.CharField(max_length=20, default='coral')
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.title} — {self.result.session}"

class QuestionCache(models.Model):

    role          = models.CharField(max_length=50)
    interview_type = models.CharField(max_length=20)
    difficulty    = models.CharField(max_length=10)
    question_text = models.TextField()
    tags          = models.JSONField(default=list)
    hint          = models.TextField(blank=True, default='')
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.role} | {self.interview_type} | {self.difficulty}"