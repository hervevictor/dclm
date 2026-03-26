from django.urls import path
from .views import *



urlpatterns = [
    path('add_projects', AddProjects.as_view(), name='add_projects'),
    path('projects_list', ProjectsList.as_view(), name='projects_list'),
    path('projects/<int:id>', ProjectsDetail, name='projects_detail'),
    path('projects/<int:pk>/edit', EditProjects.as_view(), name='edit_projects'),
    path('Projects/<int:pk>/delete', DeleteProjects.as_view(), name='delete_projects'),
    path('projects_groups/<str:group>', FilterProjectsGroups, name='projects_groups'),
    path('projects_region/<str:regs>', FilterProjectsRegion, name='projects_region'),
    path('projects_district/<str:dist>', FilterProjectsDistricts, name='projects_district'),
    
    
    path('add_difficultes', AddDifficultes.as_view(), name='add_difficultes'),
    path('difficultes_list', DifficultesList.as_view(), name='difficultes_list'),
    path('difficultes/<int:id>', DifficultesDetail, name='difficultes_detail'),
    path('difficultes/<int:pk>/edit', EditDifficultes.as_view(), name='edit_difficultes'),
    path('difficultes/<int:pk>/delete', DeleteDifficultes.as_view(), name='delete_difficultes'),
    path('difficultes_groups/<str:group>', FilterDifficultesGroups, name='difficultes_groups'),
    path('difficultes_region/<str:regs>', FilterDifficultesRegion, name='difficultes_region'),
    path('difficultes_district/<str:dist>', FilterDifficultesDistricts, name='difficultes_district'),

]


