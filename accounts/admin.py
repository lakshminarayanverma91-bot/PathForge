from django.contrib import admin
from django.contrib.admin.sites import NotRegistered
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from .models import Profile


class ProfileInline(admin.StackedInline):
	model = Profile
	fk_name = "user_ptr"
	can_delete = False
	extra = 1
	max_num = 1
	verbose_name_plural = "Profile Details"
	fields = (
		"phone_no",
		"university",
		"role",
		"about",
		"github",
		"linkedin",
		"gender",
		"image",
		"cover_image",
	)


class CustomUserAdmin(UserAdmin):
	inlines = (ProfileInline,)


try:
	admin.site.unregister(User)
except NotRegistered:
	pass

admin.site.register(User, CustomUserAdmin)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
	list_display = ("username", "email", "phone_no", "role", "university")
	search_fields = ("username", "email", "phone_no", "role", "university")
	list_filter = ("gender",)


