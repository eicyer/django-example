from django.shortcuts import render,redirect, get_object_or_404
from django.db.models import F, Sum, Case, When, IntegerField
from main_page.models import Tournament
from tourn_info.models import Adjudicator,Participant,Team,Lobby, TeamAssignment
from django.views.generic import ListView, TemplateView,DetailView
# Create your views here.

class ParticipantListView(ListView):
    model = Participant
    context_object_name = "participants_inturn"
    template_name = "tourn_info/participant_list.html"

    def get_queryset(self):
        # Retrieve the tournament_name from URL parameters
        tournament_name = self.kwargs.get('tournament_name')
        
        # Get the tournament object or 404 if not found
        tournament = get_object_or_404(Tournament, name=tournament_name)
        if not tournament.participant_view_accessible:
            return redirect('AccessDeniedView') 
        
        # Filter participants by the retrieved tournament
        return Participant.objects.filter(tournament=tournament)


class TeamListView(ListView):
    model = Team
    context_object_name = "teams_inturn"
    template_name = "tourn_info/team_list.html"
    def get_queryset(self):
        tournament_name = self.kwargs.get('tournament_name')
        
        tournament = get_object_or_404(Tournament, name=tournament_name)
        if not tournament.team_view_accessible:
            return redirect('AccessDeniedView') 
        
        return Team.objects.filter(tournament=tournament)


class AdjudicatorListView(ListView):
    model = Adjudicator
    context_object_name = "adjudicators_inturn"
    template_name = "tourn_info/adjudicator_list.html"
    def get_queryset(self):
        tournament_name = self.kwargs.get('tournament_name')
        
        tournament = get_object_or_404(Tournament, name=tournament_name)
        if not tournament.adjudicator_view_accessible:
            return redirect('AccessDeniedView') 
        
        return Adjudicator.objects.filter(tournament=tournament)
    
def ordered_speaker_view(request, tournament_name):
    tourn = get_object_or_404(Tournament, name=tournament_name)
    if not tourn.ordered_speaker_view_accessible:
        return redirect('tourn_info:access_denied', tournament_name=tournament_name)


    participants = Participant.objects.filter(tournament=tourn).order_by('-total_speaker_points')
    context = {
        'participants': participants,
        'tournament': tourn,
    }
    return render(request, 'tourn_info/speaker_order.html', context)

def ordered_team_view(request, tournament_name):
    tourn = get_object_or_404(Tournament, name=tournament_name)
    teams = Team.objects.filter(tournament_id=tourn)
    team_count = teams.count()
    if not tourn.ordered_team_view_accessible:
        return redirect('tourn_info:access_denied', tournament_name=tournament_name)
    if tourn.outround:
        teams = Team.objects.filter(tournament=tourn)
        sorted_teams = sorted(teams, key=lambda team: (-team.total_team_points(), -team.teams_total_speaker_points()))
    else:
        if tourn.round == 1:
            sorted_teams = Team.objects.filter(tournament=tourn).order_by("name")
        else:
            teams = Team.objects.filter(tournament=tourn)
            sorted_teams = sorted(teams, key=lambda team: team.total_team_points(), reverse=True)

    context = {'teams': sorted_teams, 'tournament': tourn, 'team_range': range(1, team_count + 1)}
    return render(request, 'tourn_info/team_order.html', context)



class AccessDeniedView(TemplateView):
    template_name = "tourn_info/access_denied.html"
    context_object_name = "access_denied"

def r1_view(request, tournament_name):
    tourn = get_object_or_404(Tournament, name=tournament_name)
    if not tourn.r1_view_accessible:
        return redirect('tourn_info:access_denied', tournament_name=tournament_name)
    
    lobbies = Lobby.objects.filter(tournament=tourn, round=1).prefetch_related('teams', 'adjudicators')
    
    lobby_assignments = {}
    for lobby in lobbies:
        team_positions = {ta.position: ta.team for ta in TeamAssignment.objects.filter(lobby=lobby)}
        adjudicator_names = ', '.join(adj.name for adj in lobby.adjudicators.all())
        lobby_assignments[lobby] = {**team_positions, 'adjudicators': adjudicator_names}

    context = {
        'lobby_assignments': lobby_assignments
    }

    return render(request, 'tourn_info/round_one.html', context)


def r2_view(request, tournament_name):
    tourn = get_object_or_404(Tournament, name=tournament_name)
    if not tourn.r2_view_accessible:
        return redirect('tourn_info:access_denied', tournament_name=tournament_name)
    
    lobbies = Lobby.objects.filter(tournament=tourn, round=2).prefetch_related('teams', 'adjudicators')
    
    lobby_assignments = {}
    for lobby in lobbies:
        team_positions = {ta.position: ta.team for ta in TeamAssignment.objects.filter(lobby=lobby)}
        adjudicator_names = ', '.join(adj.name for adj in lobby.adjudicators.all())
        lobby_assignments[lobby] = {**team_positions, 'adjudicators': adjudicator_names}

    context = {
        'lobby_assignments': lobby_assignments
    }

    return render(request, 'tourn_info/round_two.html', context)

def r3_view(request, tournament_name):
    tourn = get_object_or_404(Tournament, name=tournament_name)
    if not tourn.r3_view_accessible:
        return redirect('tourn_info:access_denied', tournament_name=tournament_name)
    
    lobbies = Lobby.objects.filter(tournament=tourn, round=3).prefetch_related('teams', 'adjudicators')
    
    lobby_assignments = {}
    for lobby in lobbies:
        team_positions = {ta.position: ta.team for ta in TeamAssignment.objects.filter(lobby=lobby)}
        adjudicator_names = ', '.join(adj.name for adj in lobby.adjudicators.all())
        lobby_assignments[lobby] = {**team_positions, 'adjudicators': adjudicator_names}

    context = {
        'lobby_assignments': lobby_assignments
    }

    return render(request, 'tourn_info/round_three.html', context)

def r4_view(request, tournament_name):
    tourn = get_object_or_404(Tournament, name=tournament_name)
    if not tourn.r4_view_accessible:
        return redirect('tourn_info:access_denied', tournament_name=tournament_name)
    
    lobbies = Lobby.objects.filter(tournament=tourn, round=4).prefetch_related('teams', 'adjudicators')
    
    lobby_assignments = {}
    for lobby in lobbies:
        team_positions = {ta.position: ta.team for ta in TeamAssignment.objects.filter(lobby=lobby)}
        adjudicator_names = ', '.join(adj.name for adj in lobby.adjudicators.all())
        lobby_assignments[lobby] = {**team_positions, 'adjudicators': adjudicator_names}

    context = {
        'lobby_assignments': lobby_assignments
    }

    return render(request, 'tourn_info/round_four.html', context)

def r5_view(request, tournament_name):
    tourn = get_object_or_404(Tournament, name=tournament_name)
    if not tourn.r5_view_accessible:
        return redirect('tourn_info:access_denied', tournament_name=tournament_name)
    
    lobbies = Lobby.objects.filter(tournament=tourn, round=5).prefetch_related('teams', 'adjudicators')
    
    lobby_assignments = {}
    for lobby in lobbies:
        team_positions = {ta.position: ta.team for ta in TeamAssignment.objects.filter(lobby=lobby)}
        adjudicator_names = ', '.join(adj.name for adj in lobby.adjudicators.all())
        lobby_assignments[lobby] = {**team_positions, 'adjudicators': adjudicator_names}

    context = {
        'lobby_assignments': lobby_assignments
    }

    return render(request, 'tourn_info/round_five.html', context)

def r32_view(request, tournament_name):
    tourn = get_object_or_404(Tournament, name=tournament_name)
    if not tourn.otuziki_view_accessible:
        return redirect('tourn_info:access_denied', tournament_name=tournament_name)
    
    lobbies = Lobby.objects.filter(tournament=tourn, round=32).prefetch_related('teams', 'adjudicators')
    
    lobby_assignments = {}
    for lobby in lobbies:
        team_positions = {ta.position: ta.team for ta in TeamAssignment.objects.filter(lobby=lobby)}
        adjudicator_names = ', '.join(adj.name for adj in lobby.adjudicators.all())
        lobby_assignments[lobby] = {**team_positions, 'adjudicators': adjudicator_names}

    context = {
        'lobby_assignments': lobby_assignments
    }

    return render(request, 'tourn_info/pre_qf.html', context)

def r24_view(request, tournament_name):
    tourn = get_object_or_404(Tournament, name=tournament_name)
    if not tourn.yirmidort_view_accessible:
        return redirect('tourn_info:access_denied', tournament_name=tournament_name)
    
    lobbies = Lobby.objects.filter(tournament=tourn, round=24).prefetch_related('teams', 'adjudicators')
    
    lobby_assignments = {}
    for lobby in lobbies:
        team_positions = {ta.position: ta.team for ta in TeamAssignment.objects.filter(lobby=lobby)}
        adjudicator_names = ', '.join(adj.name for adj in lobby.adjudicators.all())
        lobby_assignments[lobby] = {**team_positions, 'adjudicators': adjudicator_names}

    context = {
        'lobby_assignments': lobby_assignments
    }

    return render(request, 'tourn_info/partial_qf.html', context)

def r16_view(request, tournament_name):
    tourn = get_object_or_404(Tournament, name=tournament_name)
    if not tourn.onalti_view_accessible:
        return redirect('tourn_info:access_denied', tournament_name=tournament_name)
    
    lobbies = Lobby.objects.filter(tournament=tourn, round=16).prefetch_related('teams', 'adjudicators')
    
    lobby_assignments = {}
    for lobby in lobbies:
        team_positions = {ta.position: ta.team for ta in TeamAssignment.objects.filter(lobby=lobby)}
        adjudicator_names = ', '.join(adj.name for adj in lobby.adjudicators.all())
        lobby_assignments[lobby] = {**team_positions, 'adjudicators': adjudicator_names}

    context = {
        'lobby_assignments': lobby_assignments
    }

    return render(request, 'tourn_info/quarter_finals.html', context)

def r12_view(request, tournament_name):
    tourn = get_object_or_404(Tournament, name=tournament_name)
    if not tourn.oniki_view_accessible:
        return redirect('tourn_info:access_denied', tournament_name=tournament_name)
    
    lobbies = Lobby.objects.filter(tournament=tourn, round=12).prefetch_related('teams', 'adjudicators')
    
    lobby_assignments = {}
    for lobby in lobbies:
        team_positions = {ta.position: ta.team for ta in TeamAssignment.objects.filter(lobby=lobby)}
        adjudicator_names = ', '.join(adj.name for adj in lobby.adjudicators.all())
        lobby_assignments[lobby] = {**team_positions, 'adjudicators': adjudicator_names}

    context = {
        'lobby_assignments': lobby_assignments
    }

    return render(request, 'tourn_info/partial_sf.html', context)

def r8_view(request, tournament_name):
    tourn = get_object_or_404(Tournament, name=tournament_name)
    if not tourn.sekiz_view_accessible:
        return redirect('tourn_info:access_denied', tournament_name=tournament_name)
    
    lobbies = Lobby.objects.filter(tournament=tourn, round=8).prefetch_related('teams', 'adjudicators')
    
    lobby_assignments = {}
    for lobby in lobbies:
        team_positions = {ta.position: ta.team for ta in TeamAssignment.objects.filter(lobby=lobby)}
        adjudicator_names = ', '.join(adj.name for adj in lobby.adjudicators.all())
        lobby_assignments[lobby] = {**team_positions, 'adjudicators': adjudicator_names}

    context = {
        'lobby_assignments': lobby_assignments
    }

    return render(request, 'tourn_info/semifinals.html', context)

def final_view(request, tournament_name):
    tourn = get_object_or_404(Tournament, name=tournament_name)
    if not tourn.final_view_accessible:
        return redirect('tourn_info:access_denied', tournament_name=tournament_name)
    
    lobbies = Lobby.objects.filter(tournament=tourn, round=10).prefetch_related('teams', 'adjudicators')
    
    lobby_assignments = {}
    for lobby in lobbies:
        team_positions = {ta.position: ta.team for ta in TeamAssignment.objects.filter(lobby=lobby)}
        adjudicator_names = ', '.join(adj.name for adj in lobby.adjudicators.all())
        lobby_assignments[lobby] = {**team_positions, 'adjudicators': adjudicator_names}

    context = {
        'lobby_assignments': lobby_assignments
    }

    return render(request, 'tourn_info/final.html', context)





