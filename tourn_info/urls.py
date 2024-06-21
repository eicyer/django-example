from django.urls import path,re_path
from tourn_info import views
app_name = 'tourn_info'

urlpatterns = [
    path('<str:tournament_name>/team_list/',views.TeamListView.as_view(), name="teams"),
    path('<str:tournament_name>/participants/',views.ParticipantListView.as_view(), name="participants"),
    path('<str:tournament_name>/adjudicator_list/',views.AdjudicatorListView.as_view(), name="adjudicators"),
    path('<str:tournament_name>/speaker_standing/',views.ordered_speaker_view, name="spstandings"),
    path('<str:tournament_name>/ordered-teams/',views.ordered_team_view, name="teamstandings"),
    path('<str:tournament_name>/access_denied/',views.AccessDeniedView.as_view(), name="access_denied"),
    path('<str:tournament_name>/round_one/',views.r1_view, name="r1"),
    path('<str:tournament_name>/round_two/',views.r2_view, name="r2"),
    path('<str:tournament_name>/round_three/',views.r3_view, name="r3"),
    path('<str:tournament_name>/round_four/',views.r4_view, name="r4"),
    path('<str:tournament_name>/round_five/',views.r5_view, name="r5"),
    path('<str:tournament_name>/pre_quarter_finals/',views.r32_view, name="r32"),
    path('<str:tournament_name>/partial_quarter_finals/',views.r24_view, name="r24"),
    path('<str:tournament_name>/quarter_finals/',views.r16_view, name="r16"),
    path('<str:tournament_name>/partial_semi_finals/',views.r12_view, name="r12"),
    path('<str:tournament_name>/semi_finals/',views.r8_view, name="r8"),
    path('<str:tournament_name>/final/',views.final_view, name="final"),
]