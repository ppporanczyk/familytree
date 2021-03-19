from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, reverse

from person import views
from person.view_check import relation_check
from person.view_history import PersonDetailView
from person.views import (PersonCreateView, PersonUpdateView,
                          PersonDeleteView, RelationCreateView, RelationListView,
                          RelationDeleteView)
from .view_stats import HomeView, ChartData, ChartDataAge, ChartDataName
from .views import (
    FamilyTreeAllListView,
    FamilyTreeDetailView,
    FamilyTreeCreateView,
    FamilyTreeUpdateView,
    FamilyTreeDeleteView,
)

urlpatterns = [
    # ===================tree
    path('all/', FamilyTreeAllListView.as_view(), name='tree-all'),
    path('new/', FamilyTreeCreateView.as_view(), name='tree-create'),
    path('<int:pk>/', FamilyTreeDetailView.as_view(), name='tree-detail'),
    path('<int:pk>/update/', FamilyTreeUpdateView.as_view(), name='tree-update'),
    path('<int:pk>/delete/', FamilyTreeDeleteView.as_view(), name='tree-delete'),
    # ======================stats
    path('<int:pk>/stats/', HomeView.as_view(), name='tree-stats'),
    path('<int:pk>/stats/chart/', ChartData.as_view(), name='stats-chart'),
    path('<int:pk>/stats/chart_age/', ChartDataAge.as_view(), name='stats-chart-age'),
    path('<int:pk>/stats/chart_name/', ChartDataName.as_view(), name='stats-chart-name'),
    # =======================relation
    path('<int:pk>/new_related/', RelationCreateView.as_view(), name='relation-create'),
    path('<int:pk>/check_rel/', relation_check, name='relation-check'),
    path('<int:pk>/list_rel/', RelationListView.as_view(), name='relation-list'),
    path('<int:pk>/list_rel/<int:pk_rel>/delete/', RelationDeleteView.as_view(), name='relation-delete'),
    # =========================person
    path('<int:pk>/new/', PersonCreateView.as_view(), name='person-create'),
    path('<int:pk>/<int:pk_per>/', PersonDetailView.as_view(), name='person-detail'),
    path('<int:pk>/<int:pk_per>/update/', PersonUpdateView.as_view(), name='person-update'),
    path('<int:pk>/<int:pk_per>/delete/', PersonDeleteView.as_view(), name='person-delete'),
    path('new_related/load_person', views.load_person, name='load_people'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
