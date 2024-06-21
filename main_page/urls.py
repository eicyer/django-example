from django.urls import path,re_path
from main_page import views
urlpatterns = [
    path('detail/<str:tournament_name>/',views.tourn_info_view, name="detail"),
    path('',views.tourn_list_view, name="tournament_list"),
    path('hosting/',views.host_view, name="hosting")
]