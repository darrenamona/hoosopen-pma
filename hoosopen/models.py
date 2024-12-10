from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date

GRADUATION_YEAR_CHOICES = [(x, x) for x in range(2020, 2030)]
GRADUATION_SEMESTER_CHOICES = [(1, "Spring"), (2, "Fall")]
LOCATION_CHOICES = [("inperson", "In-Person"), ("online", "Online"), ("hybrid", "Hybrid")]
WEBSITE_CHOICES = [("github", "GitHub"), ("discord", "Discord"), ("slack", "Slack"), ("googledrive","Google Drive"), ("other", "Other")]
PROFICIENCY_CHOICES = [("novice", "Novice - No prior experience or knowledge."), ("beginner", "Beginner - Basic understanding but limited practical experience."), ("intermediate", "Intermediate - Working knowledge with some practical experience."), ("advanced","Advanced - Proficient with substantial practical experience."), ("expert", "Expert - Deep expertise and can mentor others.")]

class Tag(models.Model):
    name = models.CharField(max_length=100, blank=False)
    def __str__(self):
        return self.name

class FileTag(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Skill(models.Model):
    name = models.CharField(max_length=100, blank=False)
    def __str__(self):
        return self.name

# Author: Adi Ramadhan
# Date: 9/20/2020
# URL: https://adiramadhan17.medium.com/django-extend-user-model-with-one-to-one-field-92ced0303d84
# Used this to help extend the default Django User with my own custom attributes
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    join_date = models.DateField(default=date.today)
    bio = models.CharField(null=True, blank=True, max_length=5000, default="Show your personality by adding a fun bio!")
    github_username = models.CharField(null=True, blank=True, max_length=39)
    graduation_year = models.IntegerField(null=True, blank=True, choices=GRADUATION_YEAR_CHOICES)
    graduation_semester = models.CharField(null=True, blank=True, max_length=10, choices=GRADUATION_SEMESTER_CHOICES)
    is_admin = models.BooleanField(default=False)
    interests = models.ManyToManyField(Tag, blank=True)
    REQUIRED_FIELDS = ('user')
    def __str__(self):
        return self.user.username
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

class Project(models.Model):
    creator = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='creator')
    title = models.CharField(max_length=100, blank=False)
    creation_date = models.DateTimeField(default=timezone.datetime.now)
    description = models.CharField(max_length=5000)
    members = models.ManyToManyField(UserProfile, related_name='members', blank=True)
    tags = models.ManyToManyField(Tag, blank=True)
    application_required = models.BooleanField(default=False)
    location = models.CharField(max_length=100, choices=LOCATION_CHOICES, default=LOCATION_CHOICES[0])
    skills = models.ManyToManyField(Skill, blank=True)
    def __str__(self):
        return self.title


class Link(models.Model):
    website = models.CharField(max_length=100, choices=WEBSITE_CHOICES)
    url = models.CharField(max_length=100, blank=False)
    project = models.ForeignKey(Project, blank=True, on_delete=models.CASCADE)
    def __str__(self):
        return self.url

class UserSkill(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, null=True, blank=True, related_name="skills")
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    proficiency = models.CharField(max_length=100, default=PROFICIENCY_CHOICES[0], choices=PROFICIENCY_CHOICES)
    def __str__(self):
        return self.skill.name + ': ' + self.proficiency

class Message(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    post_date = models.DateTimeField(auto_now_add=True)
    message = models.CharField(max_length=500)
    
class ProjectJoinRequest(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="project_join_requests")
    userprofile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    request_date = models.DateTimeField(default=timezone.datetime.now)
    comment = models.CharField(max_length=500, blank=True)
    status = models.CharField(max_length=10, default='Pending')

def upload_to(instance, filename):
    return f"uploads/{instance.project.pk}/{filename}"

class ProjectFile(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='files')
    userprofile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='uploaded_files', null=True)
    file = models.FileField(upload_to=upload_to)
    title = models.CharField(max_length=255, default='Untitled', null=True, blank=True)
    description = models.TextField(default='', null=True, blank=True)
    tags = models.ManyToManyField(FileTag, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.title}'

class Rating(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='ratings')  # Link to Project
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    stars = models.IntegerField()  # e.g., 1 to 5
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.stars} Stars"
