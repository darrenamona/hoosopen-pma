from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.contrib import messages
from django.db.models import Avg, Count, F, Q
from django.contrib.auth.models import User
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import PermissionDenied, BadRequest
from .forms import ProjectJoinRequestForm, TagForm, FileUploadForm, LinkForm, RatingForm
from .models import UserProfile, Tag, Project, Skill, UserSkill, Message, ProjectJoinRequest, FileTag, ProjectFile, LOCATION_CHOICES, Rating
import json

# Home
def home(request):
    return render(request, 'home.html')

from django.db.models import Q

def projects(request):
    search_query = request.GET.get('search', '').strip()  
    projects = Project.objects.all()

    project_list = []
    for project in projects:
        # Calculate overall rating for each project
        overall_rating = Rating.objects.filter(project=project).aggregate(Avg('stars'))['stars__avg']

        project_data = {
            'title': project.title,
            'owner': project.creator.user.username,
            'description': project.description,
            'tags': [tag.name for tag in project.tags.all()],
            'skills': [skill.name for skill in project.skills.all()],
            'location': project.location.lower(),
            'start_date': project.creation_date.strftime('%Y-%m-%d'),
            'added_date': project.creation_date.strftime('%Y-%m-%d'),
            'pk': project.pk,
            'overall_rating': overall_rating,
        }
        project_list.append(project_data)

    projects_json = json.dumps(project_list)
    context = {
        "tags": Tag.objects.all(),
        "skills": Skill.objects.all(),
        "projects_json": projects_json,
        "search_query": search_query,  # Include search query in context for pre-filling the search input
    }
    return render(request, 'projects.html', context=context)


# Profile
def profile(request):
    if request.user.is_anonymous:
        return redirect('account_login')
    else:
        context = {"user": request.user,
                   "userprofile": request.user.userprofile}
    return render(request, 'profile.html', context=context)


def profile(request):
    if request.user.is_anonymous:
        return redirect('account_login')
    else:
        user_profile = request.user.userprofile

        #https://books.agiliq.com/projects/django-orm-cookbook/en/latest/query_relatedtool.html
        joined_projects = Project.objects.filter(
            Q(creator=user_profile) | Q(members=user_profile)
        ).distinct().select_related('creator__user').prefetch_related('tags')

        context = {
            "user": request.user,
            "userprofile": user_profile,
            "joined_projects": joined_projects,
        }
    return render(request, 'profile.html', context=context)


def visit_profile(request, username):
    if request.user.is_anonymous:
        return redirect('account_login')
    try:
        other_user = get_object_or_404(User, username=username)
        other_user_profile = get_object_or_404(UserProfile, user=other_user)
    except Http404:  
        return render(request, '404.html')
    
    joined_projects = Project.objects.filter(
        Q(creator=other_user_profile) | Q(members=other_user_profile)
    ).distinct().select_related('creator__user').prefetch_related('tags')
    context = {"user": other_user,
                "userprofile": other_user_profile,
                "joined_projects": joined_projects
        }
    if request.user == other_user:
        return render(request, 'profile.html', context=context)
    return render(request, 'visit-profile.html', context=context)

def profile_edit(request):
    if request.user.is_anonymous:
        return redirect('account_login')
    else:
        context = {
            "user": request.user,
            "userprofile": request.user.userprofile,
            "tags": get_tags(),
            "skills": get_skills(),
            "user_interests": request.user.userprofile.interests.all(),
            "user_skills": [user_skill.skill.name for user_skill in request.user.userprofile.skills.all()],
        }
    return render(request, 'profile_edit.html', context=context)

def get_tags():
    with open('hoosopen/fixtures/initial.json', 'r') as file:
        data = json.load(file)
        for entry in data:
            if entry['model'] == 'hoosopen.tag':                
                tag_name = entry['fields']['name']
                Tag.objects.get_or_create(name=tag_name)

    return Tag.objects.all()
                
def get_skills():
    with open('hoosopen/fixtures/initial.json', 'r') as file:
        data = json.load(file)
        for entry in data:
            if entry['model'] == 'hoosopen.skill':                
                skill_name = entry['fields']['name']
                Skill.objects.get_or_create(name=skill_name)

    return Skill.objects.all()
            
def profile_finish_editing(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        bio = request.POST.get('bio')
        graduation_year = request.POST.get('graduation_year')

        # User
        user = get_object_or_404(User, id=request.user.id)
        
        full_name = full_name.split(" ")
        
        # update first_name
        if full_name[0] != '':
            user.first_name = full_name[0]    
        
        if len(full_name) > 1 and full_name[1] != '':
                user.last_name = full_name[1]
        else:
            user.last_name = ''

        user.save() 

        # UserProfile
        user_profile = get_object_or_404(UserProfile, user=request.user)

        # update bio
        if len(bio) > 0 and bio.strip():
            user_profile.bio = bio

        # update graduation_year
        if graduation_year != '' and graduation_year != 'None':
            try:     
                graduation_year = int(graduation_year)
                if graduation_year < 1900:
                    raise ValueError
            except (ValueError, TypeError):
                graduation_year = -1
        else:
            graduation_year = -1
        user_profile.graduation_year = graduation_year

        # interests
        selected_interests = request.POST.getlist('interests')
        for tag_id in selected_interests:
            tag = Tag.objects.get(id=tag_id)
            user_profile.interests.add(tag)
        
        for tag in Tag.objects.all():
            if str(tag.id) not in selected_interests:     
                user_profile.interests.remove(tag)

        # skills
        selected_skills = request.POST.getlist('skills')
        for skill_id in selected_skills:
            skill = Skill.objects.get(id=skill_id)  
            if not user_profile.skills.filter(skill=skill).exists():
                UserSkill.objects.create(user_profile=user_profile, skill=skill)

        for user_skill in user_profile.skills.all():
            if str(user_skill.skill.id) not in selected_skills:     
                user_profile.skills.remove(user_skill)

        user_profile.save()
        
        return redirect('profile')
    

# Settings
def settings(request):
    if request.user.is_anonymous:
        return redirect('account_login')
    return render(request, 'settings.html')  # Create this view and template if needed

# Projects
def project_messages(request, project_id):
    if request.user.is_anonymous:
        return redirect('account_login')
    userprofile = request.user.userprofile
    # project = Project.objects.get(pk=project_id)
    project = get_object_or_404(Project, pk=project_id)
    members = project.members.all()
    creator = project.creator
    if userprofile not in members and userprofile != creator and not userprofile.is_admin:
        raise PermissionDenied('You must be a project member or admin to project messages')
    if request.method == 'POST':
        try:
            dictionary = request.POST.dict()
            action = dictionary.get('action')
            if action == 'create':
                text = dictionary.get('text').strip()
                if len(text) > 500:
                    messages.error(request, "Failed to post message, messages must be 500 characters or less")
                elif text != "":
                    Message.objects.create(user_profile=userprofile, project=project, message=text)
                    messages.success(request, "Message posted successfully")
            elif action == 'delete':
                if userprofile.is_admin:
                    messagepk = dictionary.get('messagepk').strip()
                    messageobj = get_object_or_404(Message, pk=messagepk)
                    messageobj.delete()
                    messages.success(request, "Message deleted successfully")
                else:
                    raise PermissionDenied('You must be an admin to delete messages')
            else:
                raise BadRequest()
        except PermissionDenied as e:
                raise e
        except:
            raise BadRequest('A bad request was made')

    project_messages = sorted(project.message_set.all(), key=lambda x: x.post_date, reverse=True)
    return render(request, 'messages.html', context={'project': project, 'project_messages': project_messages})

def join_project(request, project_id):
    if request.user.is_anonymous:
        return redirect('account_login')
    userprofile = request.user.userprofile
    if userprofile.is_admin:
        raise PermissionDenied('Admins cannot join projects!')
    
    project = get_object_or_404(Project, pk=project_id)
    members = project.members
    if userprofile == project.creator or userprofile in members.all():
        return redirect(reverse('project', args=[project_id]))

    if not project.application_required:
        members.add(userprofile)
        messages.success(request, 'Joined project!')
        return redirect(reverse('project', args=[project_id]))
    else:
        # TO DO fix this bc it should be grayed
        if len(ProjectJoinRequest.objects.filter(userprofile=userprofile, project=project_id)) > 0 and ProjectJoinRequest.objects.filter(userprofile=userprofile, project=project_id).last().status != "Declined":
            raise PermissionDenied('You have already applied to this project')
        return redirect(reverse('project_application', args=[project_id]))

def project_application(request, project_id):
    if request.user.is_anonymous:
        return redirect('account_login')
    userprofile = request.user.userprofile
    if userprofile.is_admin:
        raise PermissionDenied('Admins cannot join projects!')
    
    project = get_object_or_404(Project, pk=project_id)
    members = project.members
    if userprofile == project.creator or userprofile in members.all():
        return redirect(reverse('project', args=[project_id]))

    if request.method == "POST":
        form = ProjectJoinRequestForm(request.POST)
        if form.is_valid():
            application = ProjectJoinRequest(userprofile=userprofile, project=project, comment=form.cleaned_data['comments'])
            application.save()
            messages.success(request, "Project application submitted!")
            return redirect(reverse('project', args=[project_id]))
    else:
        form = ProjectJoinRequestForm()
        return render(request, "project_application.html", {"form": form, 'project': project})
    
def project_join_requests(request, project_id):
    # Placeholder projects (same as in the 'projects' view)
    project = get_object_or_404(Project, id=project_id)
    if request.user.is_anonymous:
        return redirect('account_login')
    else:
        is_admin = request.user.userprofile.is_admin
        is_creator = request.user.userprofile == project.creator
    context = {
        "is_admin": is_admin,
        "is_creator": is_creator,
        "user": request.user,
        "userprofile": request.user.userprofile,
        "project": project,
        "project_join_requests": project.project_join_requests.all().order_by('-id'),
    }
    return render(request, 'project-join-requests.html', context=context)

def project_approve_join_request(request, project_id, project_join_request_id, user_id):
    project = get_object_or_404(Project, pk=project_id)

    user = get_object_or_404(User, pk=user_id)
    userprofile = user.userprofile

    members = project.members
    members.add(userprofile)

    project_join_request = get_object_or_404(ProjectJoinRequest, pk=project_join_request_id, project=project)
    project_join_request.status = "Approved"
    project_join_request.save()
    
    return redirect('project_join_requests', project_id=project.id)

def project_decline_join_request(request, project_id, project_join_request_id, user_id):
    project = get_object_or_404(Project, pk=project_id)

    project_join_request = get_object_or_404(ProjectJoinRequest, pk=project_join_request_id, project=project)
    project_join_request.status = "Declined"
    project_join_request.save()
    
    return redirect('project_join_requests', project_id=project.id)

def project_leave(request, project_id):
    if request.user.is_anonymous:
        return redirect('account_login')
    userprofile = request.user.userprofile
    if userprofile.is_admin:
        raise PermissionDenied('Admins cannot leave projects!')
    project = get_object_or_404(Project, pk=project_id)
    members = project.members
    if userprofile == project.creator:
        raise PermissionDenied('Project creators cannot leave a project! They can only delete them from the project\'s info page')
    if not (userprofile in members.all()):
        raise PermissionDenied('Only project members can leave a project!')
    else:
        members.remove(userprofile)
        if len(project.project_join_requests.all()) > 0:
            last = project.project_join_requests.filter(userprofile=request.user.userprofile).last()
            last.status = "Declined"
            last.save()
        # https://stackoverflow.com/questions/8931040/django-redirect-with-kwarg
        messages.success(request, 'Left project successfully!')
        return redirect(reverse('project', args=[project_id]))

def create_page(request):

    if request.user.is_anonymous:
        return redirect('account_login')
    if request.user.userprofile.is_admin:
        raise PermissionDenied('Only common users can create projects!')
    return render(request, 'create.html', context={"tags": get_tags(), "skills": get_skills()})

def create(request):
    if request.user.is_anonymous:
        return redirect('account_login')
    if request.user.userprofile.is_admin:
        raise PermissionDenied('Only common users can create projects!')
    current_user = request.user.userprofile
    selected_tags = request.POST.getlist('tags')
    selected_skills = request.POST.getlist('skills')
    selected_location = request.POST.get('location')
    app_required = request.POST.get('app_required')
    #f.save()

    try:
        if request.POST.get('title_text').strip() == '' or request.POST.get('description_text').strip() == '' or selected_location == None:
            raise Exception()
        f = Project(creator=current_user, title=request.POST['title_text'], creation_date=timezone.datetime.now(), 
                    description=request.POST['description_text'])
        f.save()
        
        f.location = selected_location

        if(app_required == 'yes'):
            f.application_required = True

        for tag_id in selected_tags:
            tag = Tag.objects.get(id=tag_id)
            f.tags.add(tag)

        
        for skill_id in selected_skills:
            skill = Skill.objects.get(id=skill_id)
            f.skills.add(skill)

        f.save()
        return redirect(reverse('project', args=[f.pk]))
    except:
        # Catch malformed requests
        request.session['error'] = 'There was an issue making your project. Make sure your project title, description, and location are not empty.'
        return redirect(reverse('create_page'))

def project_details(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    members = project.members.all()
    skills = project.skills.all()
    tags = project.tags.all()

    # Determine user roles and permissions
    if request.user.is_anonymous:
        is_admin = False
        is_creator = False
        is_member = False
        project_membership = "None"
        has_rated = False
        project_membership = "None"
    else:
        is_admin = request.user.userprofile.is_admin
        is_creator = request.user.userprofile == project.creator
        is_member = request.user.userprofile in members
        has_rated = Rating.objects.filter(project=project, user=request.user).exists()
        
        project_membership = (
            project.project_join_requests.filter(userprofile=request.user.userprofile).last().status
            if project.project_join_requests.filter(userprofile=request.user.userprofile).exists()
            else "None"
        )

    # Calculate overall rating and prepare rating breakdown data
    overall_rating = Rating.objects.filter(project=project).aggregate(Avg('stars'))['stars__avg'] or 0
    total_reviews = Rating.objects.filter(project=project).count()
    
    # Aggregate rating counts for each star level
    rating_counts = Rating.objects.filter(project=project).values('stars').annotate(count=Count('stars')).order_by('-stars')
    rating_percentages = {i: 0 for i in range(1, 6)}
    for rating in rating_counts:
        rating_percentages[rating['stars']] = (rating['count'] / total_reviews) * 100

    # Prepare star ratings data for template
    star_data = []
    for i in range(5):
        star_data.append({
            'star_count': 5 - i,  # 5-star, 4-star, etc.
            'percentage': rating_percentages[5 - i]
        })

    # Context for rendering the template
    context = {
        'project': project,
        'members': members,
        'is_admin': is_admin,
        'is_creator': is_creator,
        'is_member': is_member, "tags": tags,
        'skills': skills,
        'project_membership': project_membership,
        'has_rated': has_rated,
        'overall_rating': overall_rating,
        'total_reviews': total_reviews,
        'star_data': star_data,
    }
    return render(request, 'project-details.html', context)


def project_details_edit(request, project_id): 
    if request.user.is_anonymous:
        return redirect('account_login')
    else:
        project = get_object_or_404(Project, id=project_id)
        
        members = project.members.all()
        
        is_admin = request.user.userprofile.is_admin
        is_creator = request.user.userprofile == project.creator

        skills = get_skills()
        tags = get_tags()
        locations = LOCATION_CHOICES

        project_skills = project.skills.all()
        project_tags = project.tags.all()
        project_location = project.location

        return render(request, 'project-details-edit.html', {'project': project, "members": members, "is_admin": is_admin, "is_creator": is_creator, "skills": skills, "tags": tags, "locations": locations,"project_skills": project_skills, "project_tags": project_tags, "project_location": project_location})

def project_details_finish_editing(request, project_id):
    if request.method == 'POST':
        # Project
        project = get_object_or_404(Project, id=project_id)
        
        # update project title
        project.title = request.POST.get('title')

        # update project description
        description = request.POST.get('description')
        if len(description) > 0 and description.strip():
            project.description = description

        # tags
        selected_tags = request.POST.getlist('tags')
        for tag_id in selected_tags:
            tag = Tag.objects.get(id=tag_id)
            project.tags.add(tag)
        
        for tag in Tag.objects.all():
            if str(tag.id) not in selected_tags:     
                project.tags.remove(tag)

        # skills
        selected_skills = request.POST.getlist('skills')
        for skill_id in selected_skills:
            skill = Skill.objects.get(id=skill_id)
            project.skills.add(skill)
        
        for skill in Skill.objects.all():
            if str(skill.id) not in selected_skills:     
                project.skills.remove(skill)

        # location
        if request.POST.get('location') != None:
            project.location = request.POST.get('location')

        # application required
        application_required = request.POST.get('application')
        print(application_required)
        if application_required == "Yes":
            project.application_required = True
        else:
            project.application_required = False

        project.save()
        
        return redirect('project', project_id=project.id)

def upload_file(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    userprofile = request.user.userprofile

    # Ensure the user is part of the project
    if userprofile not in project.members.all() and userprofile != project.creator:
        raise PermissionDenied('You must be a project member to upload files.')

    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file_instance = form.save(commit=False)
            file_instance.project = project
            file_instance.userprofile = userprofile
            tags_str = form.cleaned_data.get('tags', '')
            tags_names = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
            file_instance.save()
            for tag_name in tags_names:
                tag, created = FileTag.objects.get_or_create(name=tag_name)
                file_instance.tags.add(tag)
            return redirect('view_files', project_id=project.id)
    else:
        form = FileUploadForm()

    return render(request, 'upload_file.html', {'form': form, 'project': project})

def view_file(request, project_id, file_id):
    project = get_object_or_404(Project, pk=project_id)
    userprofile = request.user.userprofile

    # Ensure the user is part of the project
    if userprofile not in project.members.all() and userprofile != project.creator and not userprofile.is_admin:
        raise PermissionDenied('You must be a project member to view files.')
    file = get_object_or_404(ProjectFile, pk=file_id, project=project)
    file_data = {
        'pk': file.pk,
        'title': file.title,
        'description': file.description,
        'tags': [tag.name for tag in file.tags.all()],
        'uploaded_by': file.userprofile.user.username,
        'uploaded_at': file.uploaded_at.isoformat(), #https://www.geeksforgeeks.org/isoformat-method-of-datetime-class-in-python/
        'file_url': file.file.url,
        'file_name': file.file.name,
        'deletable': userprofile.is_admin or file.userprofile == userprofile,
    }
    file_json = json.dumps(file_data)
    context = {
        'project': project,
        'file_json': file_json,
    }
    return render(request, 'view_file.html', context)

def view_files(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    userprofile = request.user.userprofile

    # Ensure the user is part of the project
    if userprofile not in project.members.all() and userprofile != project.creator and not userprofile.is_admin:
        raise PermissionDenied('You must be a project member to view files.')

    files = project.files.all()
    file_list = []
    for file in files:
        file_data = {
            'pk': file.pk,
            'title': file.title,
            'description': file.description,
            'tags': [tag.name for tag in file.tags.all()],
            'uploaded_by': file.userprofile.user.username,
            'uploaded_at': file.uploaded_at.isoformat(), #https://www.geeksforgeeks.org/isoformat-method-of-datetime-class-in-python/
            'file_url': file.file.url,
            'file_name': file.file.name,
            'deletable': userprofile.is_admin or file.userprofile == userprofile,
        }
        file_list.append(file_data)

    files_json = json.dumps(file_list)

    context = {
        'project': project,
        'files_json': files_json,
        'tags': Tag.objects.all()
    }
    
    return render(request, 'view_files.html', context)

def delete_file(request, project_id, file_id):
    if request.user.is_anonymous:
        return redirect('account_login')
    project = get_object_or_404(Project, pk=project_id)
    userprofile = request.user.userprofile
    if userprofile not in project.members.all() and userprofile != project.creator and not userprofile.is_admin:
        raise PermissionDenied('Be a member of a project to interact with its files')
    projectfile = get_object_or_404(ProjectFile, pk=file_id, project=project)
    if projectfile.userprofile != userprofile and not userprofile.is_admin:
        raise PermissionDenied('You must be the uploader of a file to delete it')
    else:
        projectfile.file.delete(save=False)
        projectfile.delete()
        messages.success(request, "File deleted!")
        return redirect(reverse('view_files', args=[project_id]))
        
def project_delete(request, project_id):
    if request.user.is_anonymous:
        return redirect('account_login')
    project = get_object_or_404(Project, id=project_id)
    userprofile = request.user.userprofile
    if project.creator != userprofile and not userprofile.is_admin:
        raise PermissionDenied('Only project creators and admins can delete projects')
    
    if request.method == 'POST':
        project.delete()
        messages.success(request, "Project deleted successfully!")
        return redirect(reverse('projects'))

    return render(request, 'delete_project.html', {'project': project})

def add_link(request, project_id):
    if request.user.is_anonymous:
        return redirect('account_login')
    project = get_object_or_404(Project, pk=project_id)
    userprofile = request.user.userprofile
    if project.creator != userprofile:
        raise PermissionDenied('Only project creators can add links to a project')
    if request.method == 'POST':
        form = LinkForm(request.POST)
        if form.is_valid():
            link = form.save(commit=False)
            link.project = project 
            link.save()
            messages.success(request, "Link added successfully!")
            return redirect('view_links', project_id=project.id)
    else:
        form = LinkForm()
    context = {'form': form, 'project': project}
    return render(request, 'add_link.html', context=context)

def view_links(request, project_id):
    if request.user.is_anonymous:
        return redirect('account_login')
    project = get_object_or_404(Project, pk=project_id)
    userprofile = request.user.userprofile
    if userprofile not in project.members.all() and userprofile != project.creator and not userprofile.is_admin:
        raise PermissionDenied('Be a member of a project to view it\'s links')
    context = {'project': project, 'links': project.link_set.all()}
    return render(request, 'view_links.html', context=context)


# Error Handling
def error_403(request):
    return render(request, '403.html', status=403)


def error_404(request):
    return render(request, '404.html', status=404)




def ratings(request, project_id):
    if request.user.is_anonymous:
        return redirect('account_login')
    project = get_object_or_404(Project, id=project_id)
    ratings = project.ratings.all()
    total_reviews = ratings.count()
    overall_rating = ratings.aggregate(Avg('stars'))['stars__avg'] or 0
    rating_counts = ratings.values('stars').annotate(count=Count('stars')).order_by('-stars')

    # Calculate rating percentages
    rating_percentages = {i: 0 for i in range(1, 6)}
    if total_reviews > 0:
        for rating in rating_counts:
            rating_percentages[rating['stars']] = (rating['count'] / total_reviews) * 100

    # Prepare star ratings data for template
    star_data = []
    for i in range(5):
        star_data.append({
            'star_count': 5 - i,  # 5-star, 4-star, etc.
            'percentage': rating_percentages[5 - i]
        })

    # Get individual review details
    review_details = ratings.select_related('user').values('user__username', 'comment', 'stars')

    # Determine if the user has rated the project
    has_rated = ratings.filter(user=request.user).exists() if request.user.is_authenticated else False

    # Check if the user is a project member or the creator
    is_member_or_creator = request.user.is_authenticated and (
        request.user.userprofile in project.members.all() or request.user.userprofile == project.creator
    )

    context = {
        'project': project,
        'overall_rating': overall_rating,
        'total_reviews': total_reviews,
        'star_data': star_data,
        'review_details': review_details,
        'has_rated': has_rated,
        'is_member_or_creator': is_member_or_creator,
    }
    return render(request, 'ratings.html', context)


# Add Rating View
def add_rating(request, project_id):
    if request.user.is_anonymous:
        return redirect('account_login')
    project = get_object_or_404(Project, id=project_id)
    userprofile = request.user.userprofile

    # Check if the user is a member of the project
    if userprofile not in project.members.all() and userprofile != project.creator:
        raise PermissionDenied("You must be a member of this project to rate it.")

    # Check if the user has already submitted a rating for this project
    existing_rating = Rating.objects.filter(project=project, user=request.user).first()
    if existing_rating:
        messages.info(request, "You have already rated this project.")
        return redirect('edit_rating', project_id=project.id)

    if request.method == 'POST':
        form = RatingForm(request.POST)
        if form.is_valid():
            rating = form.save(commit=False)
            rating.project = project
            rating.user = request.user
            rating.save()
            messages.success(request, "Rating added successfully!")
            return redirect('project_ratings', project_id=project.id)
    else:
        form = RatingForm()

    return render(request, 'add_rating.html', {'project': project, 'form': form})

# Edit Rating View
def edit_rating(request, project_id):
    if request.user.is_anonymous:
        return redirect('account_login')
    project = get_object_or_404(Project, id=project_id)
    rating = get_object_or_404(Rating, project=project, user=request.user)

    if request.method == 'POST':
        form = RatingForm(request.POST, instance=rating)
        if form.is_valid():
            form.save()
            messages.success(request, "Rating updated successfully!")
            return redirect('project_ratings', project_id=project.id)
    else:
        form = RatingForm(instance=rating)

    return render(request, 'edit_rating.html', {'project': project, 'form': form})

# Delete Rating View
def delete_rating(request, project_id):
    if request.user.is_anonymous:
        return redirect('account_login')
    project = get_object_or_404(Project, id=project_id)
    rating = get_object_or_404(Rating, project=project, user=request.user)

    if request.method == 'POST':
        rating.delete()
        messages.success(request, "Rating deleted successfully!")
        return redirect('project_ratings', project_id=project.id)

    return render(request, 'delete_rating.html', {'project': project})

def home(request):
    projects = Project.objects.annotate(overall_rating=Avg('ratings__stars'))

    projects_with_ratings = projects.exclude(overall_rating__isnull=True).exclude(overall_rating=0)

    recent_projects = projects.order_by('-creation_date')[:5]

    popular_projects = projects_with_ratings.order_by('-overall_rating')[:5]

    recent_project_list = [
        {
            'title': project.title,
            'owner': project.creator.user.username,
            'description': project.description,
            'tags': [tag.name for tag in project.tags.all()],
            'creation_date': project.creation_date,
            'overall_rating': project.overall_rating,
            'pk': project.pk,
        }
        for project in recent_projects
    ]

    popular_project_list = [
        {
            'title': project.title,
            'owner': project.creator.user.username,
            'description': project.description,
            'tags': [tag.name for tag in project.tags.all()],
            'creation_date': project.creation_date,
            'overall_rating': project.overall_rating,
            'pk': project.pk,
        }
        for project in popular_projects
    ]

    context = {
        'recent_projects': recent_project_list,
        'popular_projects': popular_project_list,
    }
    return render(request, 'home.html', context)
