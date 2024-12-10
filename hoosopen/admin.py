from django.contrib import admin
from .models import UserProfile, Project, Tag, Skill, Link, FileTag, UserSkill, Message, ProjectJoinRequest, ProjectFile, Rating
# Register your models here.

admin.site.register(UserProfile)
admin.site.register(Project)
admin.site.register(Tag)
admin.site.register(FileTag)
admin.site.register(Skill)
admin.site.register(Link)
admin.site.register(UserSkill)
admin.site.register(Message)
admin.site.register(ProjectJoinRequest)
admin.site.register(ProjectFile)
admin.site.register(Rating)

