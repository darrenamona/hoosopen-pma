from django import forms
from .models import Tag, UserProfile, ProjectFile, Link, Rating


# Author:
# Date: 
# URL: https://blog.jcharistech.com/2023/07/09/multiple-select-with-django-forms/
# Used this to 
class TagForm(forms.ModelForm):
    interests = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        widget=forms.SelectMultiple,
        required=False
    )

    class Meta:
        model = UserProfile
        fields = ['interests']

    def __init__(self, *args, **kwargs):
        super(TagForm, self).__init__(*args, **kwargs)

class ProjectJoinRequestForm(forms.Form):
    comments = forms.CharField(
        label="Comments",
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={'placeholder': 'Leave your comments here!'})
    )

class LinkForm(forms.ModelForm):
    class Meta:
        model = Link
        fields = ['website', 'url']
        widgets = {
            'url': forms.TextInput(attrs={'placeholder': 'http://'}),
        }

class FileUploadForm(forms.ModelForm):
    tags = forms.CharField(
        max_length=255,
        required=False,
        help_text="Enter comma-separated keywords."
    )
    title = forms.CharField(max_length=255)
    description = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = ProjectFile
        fields = ['file', 'title', 'description', 'tags']

    def save(self, commit=True, project=None, userprofile=None):
        instance = super(FileUploadForm, self).save(commit=False)
        if project:
            instance.project = project
        if userprofile:
            instance.userprofile = userprofile
        if commit:
            instance.save()
            tags_str = self.cleaned_data.get('tags', '')
            tags_names = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
            for tag_name in tags_names:
                tag, created = Tag.objects.get_or_create(name=tag_name)
                instance.tags.add(tag)
        return instance

class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ['stars', 'comment']
        widgets = {
            'stars': forms.Select(choices=[(i, str(i)) for i in range(1, 6)]),
            'comment': forms.Textarea(attrs={'rows': 3}),
        }
