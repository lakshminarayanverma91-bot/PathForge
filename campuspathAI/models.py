from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):

    EXPERIENCE_CHOICES = [
        ('beginner',     'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced',     'Advanced'),
    ]

    user             = models.OneToOneField(User, on_delete=models.CASCADE, related_name='campuspath_profile')
    github_url       = models.URLField(blank=True, null=True, help_text="e.g. https://github.com/username")
    github_username  = models.CharField(max_length=100, blank=True)
    github_connected = models.BooleanField(default=False)
    github_repos     = models.IntegerField(default=0,  help_text="Number of public repos")
    github_contribs  = models.IntegerField(default=0,  help_text="Total GitHub contributions")
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_CHOICES, default='intermediate')
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} — {self.experience_level}"

class Roadmap(models.Model):

    TIMELINE_CHOICES = [
        (3,  '3 Months'),
        (6,  '6 Months'),
        (12, '12 Months'),
    ]

    STATUS_CHOICES = [
        ('active',   'Active'),
        ('archived', 'Archived'),
        ('draft',    'Draft'),
    ]

    user            = models.ForeignKey(User, on_delete=models.CASCADE, related_name='roadmaps')
    title           = models.CharField(max_length=200, help_text="e.g. Frontend Engineer @ Startup — 6-Month Blueprint")
    target_role     = models.CharField(max_length=200, help_text="e.g. Frontend Engineer at a Startup")
    timeline_months = models.IntegerField(choices=TIMELINE_CHOICES, default=6)
    interests       = models.JSONField(default=list, help_text="List of selected interest areas")
    additional_ctx  = models.TextField(blank=True, help_text="Extra context the user provided")

    total_weeks     = models.IntegerField(default=24)
    completed_weeks = models.IntegerField(default=0)
    current_week    = models.IntegerField(default=1)
    progress_pct    = models.FloatField(default=0.0, help_text="0 to 100")

    ai_summary      = models.TextField(blank=True, help_text="Gemini's overall summary message")

    status          = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    version         = models.IntegerField(default=1, help_text="Increments each time roadmap is regenerated")
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} — {self.title} (v{self.version})"

    def recalculate_progress(self):
        """Auto-update progress percentage from completed weeks."""
        self.completed_weeks = self.weeks.filter(status='completed').count()
        if self.total_weeks > 0:
            self.progress_pct = round((self.completed_weeks / self.total_weeks) * 100, 1)
        self.save(update_fields=['completed_weeks', 'progress_pct'])

class RoadmapWeek(models.Model):

    STATUS_CHOICES = [
        ('upcoming',   'Upcoming'),
        ('active',     'Active'),
        ('completed',  'Completed'),
    ]

    roadmap       = models.ForeignKey(Roadmap, on_delete=models.CASCADE, related_name='weeks')
    week_number   = models.IntegerField(help_text="Start week number, e.g. 1")
    week_end      = models.IntegerField(help_text="End week number, e.g. 4 (same as week_number if single week)")
    title         = models.CharField(max_length=200, help_text="e.g. HTML, CSS & JavaScript Deep Dive")
    description   = models.TextField(help_text="What the student will learn this week")
    mini_project  = models.CharField(max_length=300, blank=True, help_text="e.g. Personal Portfolio Site")
    key_skills    = models.CharField(max_length=300, blank=True, help_text="e.g. HTML5, CSS Grid, ES6+")
    status        = models.CharField(max_length=20, choices=STATUS_CHOICES, default='upcoming')
    order         = models.IntegerField(default=0, help_text="Display order in the timeline")
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Week {self.week_number}–{self.week_end}: {self.title}"

    @property
    def week_label(self):
        """Returns display label like 'Weeks 1–4' or 'Week 16'"""
        if self.week_number == self.week_end:
            return f"Week {self.week_number}"
        return f"Weeks {self.week_number}–{self.week_end}"

class WeekResource(models.Model):

    week    = models.ForeignKey(RoadmapWeek, on_delete=models.CASCADE, related_name='resources')
    name    = models.CharField(max_length=100, help_text="e.g. MDN Web Docs")
    url     = models.URLField(blank=True, help_text="Direct link to resource")
    emoji   = models.CharField(max_length=10, default='📖', help_text="Emoji icon for the resource")
    order   = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.emoji} {self.name}"

class WeekTask(models.Model):

    week        = models.ForeignKey(RoadmapWeek, on_delete=models.CASCADE, related_name='tasks')
    description = models.CharField(max_length=300, help_text="Task description shown as checkbox label")
    is_done     = models.BooleanField(default=False)
    est_hours   = models.CharField(max_length=30, blank=True, help_text="e.g. '4–6 hrs'")
    task_type   = models.CharField(max_length=30, default='Core', help_text="e.g. Core, Polish, CI/CD")
    order       = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        status = "✓" if self.is_done else "○"
        return f"{status} {self.description}"

class UserSkill(models.Model):

    LEVEL_CHOICES = [
        ('beginner',   'Beginner'),
        ('learning',   'Learning'),
        ('developing', 'Developing'),
        ('proficient', 'Proficient'),
        ('expert',     'Expert'),
    ]

    roadmap    = models.ForeignKey(Roadmap, on_delete=models.CASCADE, related_name='user_skills')
    skill_name = models.CharField(max_length=100, help_text="e.g. React, TypeScript")
    level      = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='proficient')

    def __str__(self):
        return f"{self.skill_name} ({self.level})"

class SkillGap(models.Model):

    STATUS_CHOICES = [
        ('have',    'Have'),
        ('partial', 'Partial'),
        ('missing', 'Missing'),
    ]

    LEVEL_DISPLAY = [
        ('Expert',      'Expert'),
        ('Proficient',  'Proficient'),
        ('Developing',  'Developing'),
        ('Learning',    'Learning'),
        ('Beginner',    'Beginner'),
        ('In progress', 'In progress'),
        ('Basic',       'Basic'),
        ('Missing',     'Missing'),
    ]

    roadmap    = models.ForeignKey(Roadmap, on_delete=models.CASCADE, related_name='skill_gaps')
    skill_name = models.CharField(max_length=100)
    status     = models.CharField(max_length=10, choices=STATUS_CHOICES)
    level      = models.CharField(max_length=20, choices=LEVEL_DISPLAY, default='Missing')
    order      = models.IntegerField(default=0)

    class Meta:
        ordering = ['status', 'order']

    def __str__(self):
        return f"{self.skill_name} — {self.status} ({self.level})"

class SkillProgress(models.Model):

    roadmap      = models.ForeignKey(Roadmap, on_delete=models.CASCADE, related_name='skill_progress')
    skill_name   = models.CharField(max_length=100, help_text="e.g. React / Frontend")
    target_percentage = models.IntegerField(default=0, help_text="Gemini's estimate once roadmap is fully completed")
    color_start  = models.CharField(max_length=30, default='var(--sky)',    help_text="CSS gradient start color")
    color_end    = models.CharField(max_length=30, default='#8b5cf6',       help_text="CSS gradient end color")
    order        = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    @property
    def current_percentage(self):
        return round(self.target_percentage * (self.roadmap.progress_pct / 100))
    
    def __str__(self):
        return f"{self.skill_name}: {self.current_percentage}% (target {self.target_percentage}%)"

class AIInsight(models.Model):

    roadmap    = models.ForeignKey(Roadmap, on_delete=models.CASCADE, related_name='insights')
    icon       = models.CharField(max_length=10, default='💡', help_text="Emoji icon for the card")
    title      = models.CharField(max_length=100, help_text="e.g. Pace Recommendation")
    body       = models.TextField(help_text="The insight text shown in the card")
    order      = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.icon} {self.title}"

class SkillGapPriority(models.Model):

    roadmap         = models.OneToOneField(Roadmap, on_delete=models.CASCADE, related_name='gap_priority')
    priority_text   = models.TextField(help_text="Gemini's priority order recommendation")
    updated_at      = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Priority for {self.roadmap.title}"