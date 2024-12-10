"""
URL configuration for mysite project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from hoosopen import views

# SHERRIFF: added the '' path to handle the root url
urlpatterns = [
    # path('', include('mysite.urls')),
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),

    # Home
    path('', views.home, name='home'),

    # Projects Details
    path('projects/', views.projects, name='projects'),
    path('projects/<int:project_id>/', views.project_details, name='project'),
    path('projects/<int:project_id>/edit', views.project_details_edit, name='project_details_edit'),
    path('projects/<int:project_id>/finish-editing', views.project_details_finish_editing, name='project_details_finish_editing'),


    path('projects/<int:project_id>/messages', views.project_messages, name='messages'),
    path('projects/<int:project_id>/join', views.join_project, name='join_project'),
    path('projects/<int:project_id>/apply', views.project_application, name='project_application'),
    path('projects/<int:project_id>/leave', views.project_leave, name='project_leave'),
    path('projects/<int:project_id>/delete', views.project_delete, name='project_delete'),
    path('projects/<int:project_id>/ratings/', views.ratings, name='project_ratings'),
    path('projects/<int:project_id>/add_rating/', views.add_rating, name='add_rating'),
    path('projects/<int:project_id>/edit_rating/', views.edit_rating, name='edit_rating'),
    path('projects/<int:project_id>/delete_rating/', views.delete_rating, name='delete_rating'),


    # Project Join Request
    path('projects/<int:project_id>/view-join-requests', views.project_join_requests, name='project_join_requests'),
    path('projects/<int:project_id>/approve-join-request/<int:project_join_request_id>/<int:user_id>', views.project_approve_join_request, name='project_approve_join_request'),
    path('projects/<int:project_id>/decline-join-request/<int:project_join_request_id>/<int:user_id>', views.project_decline_join_request, name='project_decline_join_request'),


    # Create Project
    path('create_page/', views.create_page, name='create_page'),

    path('create/', views.create, name='create'),
    path('projects/<int:project_id>/upload/', views.upload_file, name='upload_file'),
    path('projects/<int:project_id>/files/', views.view_files, name='view_files'),
    path('projects/<int:project_id>/files/<int:file_id>', views.view_file, name='view_file'),
    path('projects/<int:project_id>/files/<int:file_id>/delete', views.delete_file, name='delete_file'),
    path('projects/<int:project_id>/add_link/', views.add_link, name='add_link'),
    path('projects/<int:project_id>/links/', views.view_links, name='view_links'),

    # Author: PrettyPrinted
    # Date: 1/17/2024
    # URL: https://www.youtube.com/watch?v=mIlgzn2zuFE&ab_channel=PrettyPrinted
    # Used this to help configure default account page that displays account name
    # Profile
    path('accounts/profile/', views.profile, name='profile'),
    path('accounts/profile/edit', views.profile_edit, name='profile_edit'),
    path('accounts/profile/edit/finish-editing', views.profile_finish_editing, name='profile_finish_editing'),

    path('accounts/profile/<str:username>', views.visit_profile, name='visit_profile'),

    # Settings (optional, create view if needed)
    path('settings/', views.settings, name='settings'),

    # Error handling
    path('403', views.error_403, name='403'),
    path('404', views.error_404, name='404'),
]
