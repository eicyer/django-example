from django.contrib import admin
import random
from django import forms
from collections import defaultdict
import itertools
from django.db.models.expressions import RawSQL
from django.urls import resolve
from tourn_info.models import Participant,Team,Lobby,Adjudicator, Lobby, TeamAssignment, Conflict
from main_page.models import Tournament
from django.shortcuts import render,redirect, get_object_or_404
from guardian.admin import GuardedModelAdmin
from django.db import models

class ParticipantInline(admin.TabularInline):
    model = Participant
class ConflictInline(admin.TabularInline):
    model = Conflict
from django.forms import Select

from django_select2.forms import Select2MultipleWidget

class LobbyInline(admin.TabularInline):
    model = Lobby
    readonly_fields = ['teams_and_positions']

    def get_formset(self, request, obj=None, **kwargs):
        request._obj_ = obj
        return super().get_formset(request, obj, **kwargs)

    def teams_and_positions(self, obj):
        # Retrieve and format team assignments
        assignments = TeamAssignment.objects.filter(lobby=obj).select_related('team')
        sorted_assignments = sorted(assignments, key=lambda x: ['OG', 'OO', 'CG', 'CO'].index(x.position))
        return ', '.join([f"{assignment.team.name} ({assignment.position})" for assignment in sorted_assignments])
    teams_and_positions.short_description = 'Teams and Positions'

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "adjudicators":
            if request._obj_ is not None:
                kwargs["queryset"] = Adjudicator.objects.filter(tournament=request._obj_.name)
            else:
                kwargs["queryset"] = Adjudicator.objects.none()  # Empty queryset if no lobby is yet selected
            kwargs['widget'] = Select2MultipleWidget
        return super().formfield_for_manytomany(db_field, request, **kwargs)

class TeamInline(admin.TabularInline):
    model = Team
    fields = ['name', 'display_total_points',"display_total_speaker_points", 'institution',"r1_pt","r2_pt","r3_pt","r4_pt","r5_pt","eliminated",'og', 'oo', 'cg', 'co']  # Specify the fields you want to show
    readonly_fields = ['display_total_points',"display_total_speaker_points"]  # Make total points read-only if it's just for display
   #exclude = ('og', 'oo', 'cg', 'co')  # Exclude these fields from the inline form
    extra = 0  # Set how many extra forms for new records you want by default
    def display_total_points(self, obj):
        return obj.total_team_points()
    display_total_points.short_description = 'Total Points'
    def display_total_speaker_points(self, obj):
        return obj.teams_total_speaker_points()
    display_total_speaker_points.short_description = 'Total Speaker Points'
    def get_queryset(self, request):
        # Order by 'total_points' first, then 'total_speaker_points' in case of ties
        qs = super(TeamInline, self).get_queryset(request)
        return qs.order_by('-total_points', '-total_speaker_points')

class AdjudicatorInline(admin.TabularInline):
    model = Adjudicator

class TeamAssignmentForm(forms.ModelForm):
    eliminated = forms.BooleanField(required=False, label="Eliminated")

    class Meta:
        model = TeamAssignment
        fields = ['team', 'position', 'eliminated']

    def __init__(self, *args, **kwargs):
        super(TeamAssignmentForm, self).__init__(*args, **kwargs)
        # Check if instance and instance.team exist before accessing attributes
        if self.instance and hasattr(self.instance, 'team') and self.instance.team:
            self.fields['eliminated'].initial = self.instance.team.eliminated
        # Optionally, handle the case where there is no team yet
        else:
            self.fields['eliminated'].disabled = True  # Disable if no team is associated

    def save(self, commit=True):
        instance = super(TeamAssignmentForm, self).save(commit=False)
        # Ensure team is present before setting eliminated status
        if self.cleaned_data.get('eliminated') is not None and self.instance.team:
            self.instance.team.eliminated = self.cleaned_data['eliminated']
            self.instance.team.save()
        if commit:
            instance.save()
        return instance
    
class TeamAssignmentInline(admin.TabularInline):
    model = TeamAssignment
    form = TeamAssignmentForm
    fields = ['team', 'lobby', 'position', 'eliminated']
    extra = 0
    readonly_fields = ['get_round']

    def get_round(self, obj):
        return obj.lobby.round if obj.lobby else None
    get_round.short_description = 'Round'

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "lobby":
            kwargs["queryset"] = Lobby.objects.order_by('-round', 'name')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
from django.urls import path
from django.shortcuts import render
class TournamentAdmin(GuardedModelAdmin):
        # existing setup
    change_list_template = "admin/tournament_change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('manage_teams/', self.admin_site.admin_view(self.manage_teams), name='manage-teams'),
        ]
        return custom_urls + urls

    def manage_teams(self, request):
        context = {
            # Add context data here necessary for the view
        }
        return render(request, "tourn_admin/manage_teams.html", context)
    
@admin.register(Tournament)
class TournamentAdmin(GuardedModelAdmin):
    fieldsets = (
        (None, {
            'fields': ('name', 'host', 'date', 'round', 'outround', 'motions')
        }),
        ('View Accessible Fields', {
            'fields': (
                'adjudicator_view_accessible',
                'team_view_accessible',
                'participant_view_accessible',
                'ordered_speaker_view_accessible',
                'ordered_team_view_accessible',
                'r1_view_accessible',
                'r2_view_accessible',
                'r3_view_accessible',
                'r4_view_accessible',
                'r5_view_accessible',
                'otuziki_view_accessible',
                'yirmidort_view_accessible',
                'onalti_view_accessible',
                'oniki_view_accessible',
                'sekiz_view_accessible',
                'final_view_accessible',
            ),
            'classes': ('collapse',)
        }),
    )
    list_display = ['name','team_view_accessible','adjudicator_view_accessible','participant_view_accessible', 'ordered_speaker_view_accessible','ordered_team_view_accessible']
    inlines = [
        TeamInline,AdjudicatorInline,ParticipantInline,LobbyInline,TeamAssignmentInline,ConflictInline
    ]
    def clean_name(self):
        name = self.cleaned_data['name']
        if Tournament.objects.filter(name=name).exists():
            raise forms.ValidationError("A tournament with this name already exists.")
        return name

    actions = ["group_teams_and_create_lobbies"]
import random
from django.db.models import Q

def check_strict_conflict(adjudicator, teams):
    for team in teams:
        # Check if both participants have a conflict or a team-level conflict exists
        participants = team.participants.all()
        participant_conflicts = [Conflict.objects.filter(adjudicator=adjudicator, participant=participant, is_strict=True).exists() for participant in participants]
        if len(participant_conflicts) == 2 and all(participant_conflicts):
            return True
        if Conflict.objects.filter(adjudicator=adjudicator, team=team, is_strict=True).exists():
            return True
    return False

def check_soft_conflict(adjudicator, teams):
    for team in teams:
        participants = team.participants.all()
        if any(Conflict.objects.filter(adjudicator=adjudicator, participant=participant, is_strict=False).exists() for participant in participants):
            return True
    return False

def random_assignment(modeladmin, request, queryset):
    for tournament in queryset:
        teams = list(tournament.teams.all())
        random.shuffle(teams)
        
        num_teams = len(teams)
        teams_per_lobby = 4
        num_lobbies = (num_teams + teams_per_lobby - 1) // teams_per_lobby
        
        # Fetch all adjudicators for the tournament
        adjudicators = list(Adjudicator.objects.filter(tournament=tournament))
        random.shuffle(adjudicators)
        
        # Calculate the number of adjudicators per lobby if possible
        if len(adjudicators) < num_lobbies:
            print("Error: Not enough adjudicators for the number of lobbies.")
            return  # Or handle this situation appropriately
        adjudicators_per_lobby = len(adjudicators) // num_lobbies
        
        lobbies = []
        # Create lobbies and distribute teams
        for i in range(num_lobbies):
            lobby_teams = teams[i * teams_per_lobby:(i + 1) * teams_per_lobby]
            lobby = Lobby.objects.create(
                tournament=tournament,
                name=f"Round {tournament.round} Lobby {i + 1}",
                round=tournament.round
            )
            lobbies.append(lobby)

            positions = ['OG', 'OO', 'CG', 'CO']
            random.shuffle(positions)
            for team, position in zip(lobby_teams, positions):
                TeamAssignment.objects.create(
                    tournament=tournament,
                    lobby=lobby,
                    team=team,
                    position=position
                )
                
                setattr(team, position.lower(), getattr(team, position.lower()) + 1)
                team.save()
  # Assign adjudicators to lobbies ensuring even distribution
        remaining_adjudicators = adjudicators[:]
        round_number = 0  # To keep track of distribution rounds

        while remaining_adjudicators:
            assigned_in_round = False  # Track if we assigned any adjudicators this round
            for lobby in lobbies:
                if not remaining_adjudicators:
                    break  # No more adjudicators to assign

                for adjudicator in remaining_adjudicators[:]:
                    if check_strict_conflict(adjudicator, lobby.teams.all()):
                        continue  # Skip strict conflicts
                    elif check_soft_conflict(adjudicator, lobby.teams.all()):
                        continue  # Skip soft conflicts
                    if lobby.adjudicators.count() >= round_number:
                        # Only add adjudicator if the lobby does not already have more than the current round number of adjudicators
                        lobby.adjudicators.add(adjudicator)
                        remaining_adjudicators.remove(adjudicator)
                        assigned_in_round = True
                        break  # Break after assigning one adjudicator to prevent multiple assignments in one round

            if not assigned_in_round:
                # If no adjudicators were assigned in this full pass, stop the loop
                break
            round_number += 1  # Increase the round number after a full pass

        tournament.round += 1
        tournament.save()

admin.site.add_action(random_assignment, 'Randomly Group Teams and Create Lobbies')

import random
from collections import defaultdict, deque
import itertools

def group_teams_and_create_lobbies(modeladmin, request, queryset):
    for tournament in queryset:
        teams = list(tournament.teams.all().order_by('-total_points', '-r1_pt', '-r2_pt', '-r3_pt', '-r4_pt', '-r5_pt'))
        shuffle_iterations = 30
        best_overall_cost = float('inf')
        best_assignments = []  # Store the best assignment for each group

        teams_by_score = defaultdict(list)
        for team in teams:
            teams_by_score[team.total_team_points()].append(team)

        for _ in range(shuffle_iterations):
            for score_group in teams_by_score.values():
                random.shuffle(score_group)
            shuffled_teams = [team for score in sorted(teams_by_score.keys(), reverse=True) for team in teams_by_score[score]]

            current_assignments = []
            current_overall_cost = 0

            for i in range(0, len(shuffled_teams), 4):
                lobby_teams = shuffled_teams[i:i + 4]
                if len(lobby_teams) < 4:
                    continue

                current_best_cost = float('inf')
                current_best_assignment = None

                for permutation in itertools.permutations(['OG', 'OO', 'CG', 'CO']):
                    current_cost = sum({0: 0, 1: 0.2, 2: 10}.get(getattr(team, position.lower()), 20) for team, position in zip(lobby_teams, permutation))

                    if current_cost < current_best_cost:
                        current_best_cost = current_cost
                        current_best_assignment = (lobby_teams, permutation)

                current_assignments.append(current_best_assignment)
                current_overall_cost += current_best_cost

            if current_overall_cost < best_overall_cost:
                best_overall_cost = current_overall_cost
                best_assignments = current_assignments

        adjudicators = deque(sorted(Adjudicator.objects.filter(tournament=tournament).annotate(random_order=RawSQL("RANDOM()", [])).order_by('-points', 'random_order'), key=lambda x: x.points, reverse=True))
        
        lobbies_points = [(sum(team.total_points for team in lobby_teams[0]), i) for i, lobby_teams in enumerate(best_assignments)]
        lobbies_points.sort(reverse=True, key=lambda x: x[0])
        
        # First round of assigning adjudicators
        for points, i in lobbies_points:
            if adjudicators:
                lobby_teams, positions = best_assignments[i]
                adjudicator = adjudicators.popleft()
                lobby = Lobby.objects.create(
                    tournament=tournament, 
                    name=f"Round {tournament.round} Lobby {i + 1}", 
                    round=tournament.round
                )
                lobby.adjudicators.add(adjudicator)

                for team, position in zip(lobby_teams, positions):
                    TeamAssignment.objects.create(
                        tournament=tournament,
                        lobby=lobby,
                        team=team,
                        position=position
                    )
                    setattr(team, position.lower(), getattr(team, position.lower()) + 1)
                    team.save()

        # Second round of assigning remaining adjudicators (higher points to lower points lobbies)
            adjudicators_this_round = deque()  # Track adjudicators used in this round to avoid double assignment
            while adjudicators and lobby.adjudicators.count() < 1:
                adjudicator = adjudicators.popleft()
                if not check_strict_conflict(adjudicator, lobby_teams) and not check_soft_conflict(adjudicator, lobby_teams):
                    lobby.adjudicators.add(adjudicator)
                else:
                    # If the popped adjudicator has a conflict, they are put back at the end of the deque to be considered for another lobby
                    adjudicators_this_round.append(adjudicator)
            
            # Re-add adjudicators back to the main deque that were not used due to conflicts in other lobbies
            adjudicators.extend(adjudicators_this_round)
        tournament.round += 1
        tournament.save()
            
admin.site.add_action(group_teams_and_create_lobbies, 'Group Teams and Create Lobbies')
        
def assign_adjudicators_to_lobbies(lobbies, adjudicators):
    # Sort adjudicators by points for better distribution
    sorted_adjudicators = sorted(adjudicators, key=lambda x: x.points, reverse=True)
    adjudicator_queue = deque(sorted_adjudicators)

    # Tracking for initial assignment to ensure every lobby gets at least one adjudicator
    lobbies_needing_adjudicators = set(lobbies)

    # Track adjudicators and points to manage distribution
    lobby_points = {lobby: 0 for lobby in lobbies}
    adjudicator_assignments = {lobby: [] for lobby in lobbies}

    while adjudicator_queue and lobbies_needing_adjudicators:
        adjudicator = adjudicator_queue.popleft()

        # Try to assign this adjudicator to a suitable lobby from those needing an adjudicator
        for lobby in list(lobbies_needing_adjudicators):
            if not check_strict_conflict(adjudicator, lobby.teams.all()) and not check_soft_conflict(adjudicator, lobby.teams.all()):
                lobby.adjudicators.add(adjudicator)
                lobby_points[lobby] += adjudicator.points
                adjudicator_assignments[lobby].append(adjudicator)
                lobbies_needing_adjudicators.remove(lobby)
                break
        else:
            # If no suitable lobby was found, re-add adjudicator to the end of the queue
            if adjudicator_queue:  # Only re-add if there are still adjudicators to process
                adjudicator_queue.append(adjudicator)

    # Continue distributing remaining adjudicators once every lobby has at least one
    while adjudicator_queue:
        adjudicator = adjudicator_queue.popleft()

        # Find the lobby with the least points to try to balance adjudicator quality
        target_lobby = min(lobby_points, key=lobby_points.get)

        if not check_strict_conflict(adjudicator, target_lobby.teams.all()) and not check_soft_conflict(adjudicator, target_lobby.teams.all()):
            target_lobby.adjudicators.add(adjudicator)
            lobby_points[target_lobby] += adjudicator.points
            adjudicator_assignments[target_lobby].append(adjudicator)
        else:
            # If no suitable placement is found, do not attempt further for this adjudicator
            continue





from collections import deque
import random
from django.db.models import F

def folding32(modeladmin, request, queryset):
    for tournament in queryset:
        tournament.outround = True
        tournament.save()
        
        teams = list(tournament.teams.all().order_by('-total_points', '-total_speaker_points'))
        print([(team.name, team.total_points) for team in teams])
        print(teams[0])
        if len(teams) < 32:
            print("Error: Not enough teams for the lobbies.")
            continue  # Skip to next tournament if not enough teams

        top_teams = teams[:32]
        teams_to_update = teams[32:]
        for team in teams_to_update:
            team.eliminated = True
        Team.objects.bulk_update(teams_to_update, ['eliminated'])

        def get_lobby_indices(n):
            # Correct the indices based on the specified pattern
            # (1st, 16th, 17th, 32nd), (2nd, 15th, 18th, 31st), ..., (n-1, 16-n, 16+n-1, 32-n)
            return [n-1, 16-n, 16+n-1, 32-n]

        positions = ['OG', 'OO', 'CG', 'CO']
        adjudicators = list(Adjudicator.objects.filter(tournament=tournament).annotate(random_order=F('points')).order_by('-points', 'random_order'))
        random.shuffle(adjudicators)

        if len(adjudicators) < 8:
            print("Error: Not enough adjudicators for the number of lobbies.")
            continue

        lobbies = []
        for i in range(1, 9):
            indices = get_lobby_indices(i)
            lobby_teams = [top_teams[j] for j in indices]
            lobby_name = f"SQF Lobby {i}"
            lobby = Lobby.objects.create(
                tournament=tournament, name=lobby_name, outround=True, round=32
            )
            lobbies.append(lobby)

            random.shuffle(positions)
            for team, position in zip(lobby_teams, positions):
                TeamAssignment.objects.create(
                    tournament=tournament,
                    lobby=lobby,
                    team=team,
                    position=position
                )

        assign_adjudicators_to_lobbies(lobbies, adjudicators)

        tournament.round += 1
        tournament.save()

admin.site.add_action(folding32, 'Group Top 32 Teams and Create Lobbies')

def folding16(modeladmin, request, queryset):
    for tournament in queryset:
        tournament.outround = True
        tournament.save()
        teams = list(tournament.teams.all().order_by('-total_points', '-total_speaker_points'))

        if len(teams) < 16:
            print("Error: Not enough teams for the lobbies.")
            continue

        top_teams = teams[:16]
        teams_to_update = teams[16:]
        for team in teams_to_update:
            team.eliminated = True
        Team.objects.bulk_update(teams_to_update, ['eliminated'])

        def get_lobby_indices(n):
            return [n-1, 8-n, 8+n-1, 16-n]

        positions = ["OG", "OO", "CG", "CO"]
        adjudicators = list(Adjudicator.objects.filter(tournament=tournament).order_by('?'))
        if len(adjudicators) < 4:  # Checking if there are enough adjudicators to have 5 per lobby
            print("Error: Not enough adjudicators for the number of lobbies.")
            return

        lobbies = []
        for i in range(1, 5):
            indices = get_lobby_indices(i)
            lobby_teams = [top_teams[j] for j in indices]

            lobby_name = f"QF Lobby {i}"
            lobby = Lobby.objects.create(
                tournament=tournament, name=lobby_name, outround=True, round=16
            )
            lobbies.append(lobby)

            random.shuffle(positions)
            for team, position in zip(lobby_teams, positions):
                TeamAssignment.objects.create(
                    tournament=tournament,
                    lobby=lobby,
                    team=team,
                    position=position
                )

        # Assign up to 5 adjudicators to each lobby
        assign_adjudicators_to_lobbies(lobbies, adjudicators)
        tournament.round += 1
        tournament.save()

admin.site.add_action(folding16, 'Group Top 16 Teams and Create Lobbies')

def folding8(modeladmin, request, queryset):
    for tournament in queryset:
        tournament.outround = True
        tournament.save()

        teams = list(tournament.teams.all().order_by('-total_points', '-total_speaker_points'))
        if len(teams) < 8:
            print("Error: Not enough teams for the lobbies.")
            continue

        top_teams = teams[:8]
        teams_to_update = teams[8:]
        for team in teams_to_update:
            team.eliminated = True
        Team.objects.bulk_update(teams_to_update, ['eliminated'])

        adjudicators = list(Adjudicator.objects.filter(tournament=tournament).order_by('-points'))
        if len(adjudicators) < 2:  # Ensuring at least 10 adjudicators to potentially assign up to 5 per lobby
            print("Error: Not enough adjudicators for the number of lobbies.")
            return

        positions = ["OG", "OO", "CG", "CO"]
        lobby_indices = [[0, 3, 4, 7], [1, 2, 5, 6]]  # Example indices for two lobbies

        lobbies = []
        for i, indices in enumerate(lobby_indices, start=1):
            lobby_teams = [top_teams[j] for j in indices]
            lobby_name = f"SF Lobby {i}"
            lobby = Lobby.objects.create(
                tournament=tournament,
                name=lobby_name,
                outround=True,
                round=8
            )
            lobbies.append(lobby)

            random.shuffle(positions)
            for team, position in zip(lobby_teams, positions):
                TeamAssignment.objects.create(
                    tournament=tournament,
                    lobby=lobby,
                    team=team,
                    position=position
                )
        assign_adjudicators_to_lobbies(lobbies, adjudicators)
        # Assign up to 5 adjudicators to each lobby
        tournament.round += 1
        tournament.save()

admin.site.add_action(folding8, 'Group Top 8 Teams and Create Lobbies')

def continuing16(modeladmin, request, queryset):
    for tournament in queryset:
        sorted_lobbies = Lobby.objects.filter(tournament=tournament, round=32).order_by('name')
        lobby_pairs = [(sorted_lobbies[i], sorted_lobbies[7-i]) for i in range(4)]

        # Fetch all available adjudicators for the next round
        adjudicators = list(Adjudicator.objects.filter(tournament=tournament)
                             .annotate(random_order=RawSQL("RANDOM()", []))
                             .order_by('-points', 'random_order'))

        if len(adjudicators) < 4:
            print("Not enough adjudicators available to continue.")
            return

        lobbies = []
        for index, lobby_pair in enumerate(lobby_pairs):
            combined_teams = list(lobby_pair[0].teams.all()) + list(lobby_pair[1].teams.all())
            remaining_teams = [team for team in combined_teams if not team.eliminated]

            if len(remaining_teams) == 4:
                new_lobby_name = f"Quarter Final Lobby {index + 1}"
                new_lobby = Lobby.objects.create(
                    tournament=tournament,
                    name=new_lobby_name,
                    outround=True,
                    round=16
                )
                lobbies.append(new_lobby)

                positions = ['OG', 'OO', 'CG', 'CO']
                random.shuffle(positions)
                for i, position in enumerate(positions):
                    TeamAssignment.objects.create(
                        tournament=tournament,
                        lobby=new_lobby,
                        team=remaining_teams[i],
                        position=position
                    )
            else:
                print(f"Unexpected number of remaining teams in lobbies {lobby_pair[0].name} and {lobby_pair[1].name}")

        assign_adjudicators_to_lobbies(lobbies, adjudicators)

        tournament.round += 1
        tournament.save()
admin.site.add_action(continuing16, 'Continue to quarter final')

def continuing8(modeladmin, request, queryset):
    for tournament in queryset:
        sorted_lobbies = Lobby.objects.filter(tournament=tournament, outround=True, round=16)
        lobby_pairs = [(sorted_lobbies[i], sorted_lobbies[3-i]) for i in range(2)]

        # Retrieve and shuffle all available adjudicators, breaking ties randomly
        adjudicators = list(Adjudicator.objects.filter(tournament=tournament).order_by('-points', '?'))
        if len(adjudicators) <len(lobby_pairs):  # Ensure there are enough adjudicators to assign 5 to each lobby
            print("Not enough adjudicators available.")
            return

        lobbies = []
        for index, lobby_pair in enumerate(lobby_pairs):
            combined_teams = list(lobby_pair[0].teams.all()) + list(lobby_pair[1].teams.all())
            remaining_teams = [team for team in combined_teams if not team.eliminated]

            if len(remaining_teams) == 4:
                # Create a new lobby for the semi-final round
                new_lobby_name = f"Semi Final Lobby {index + 1}"
                new_lobby = Lobby.objects.create(
                    tournament=tournament,
                    name=new_lobby_name,
                    outround=True,
                    round=8
                )
                lobbies.append(new_lobby)

                positions = ['OG', 'OO', 'CG', 'CO']
                random.shuffle(positions)
                for i, position in enumerate(positions):
                    TeamAssignment.objects.create(
                        tournament=tournament,
                        lobby=new_lobby,
                        team=remaining_teams[i],
                        position=position
                    )
            else:
                print(f"Unexpected number of remaining teams in lobbies {lobby_pair[0].name} and {lobby_pair[1].name}")

        # Assign adjudicators to each lobby, with a maximum of 5 per lobby
        adjudicator_queue = deque(adjudicators)
        while adjudicator_queue:
            for lobby in lobbies:
                if len(lobby.adjudicators.all()) >= 5:
                    continue  # Skip to next lobby if this one already has 5 adjudicators
                if not adjudicator_queue:
                    break
                adjudicator = adjudicator_queue.popleft()
                lobby.adjudicators.add(adjudicator)

        tournament.round = 8
        tournament.save()

admin.site.add_action(continuing8, 'Continue to semi final')

def continuing4(modeladmin, request, queryset):
    for tournament in queryset:
        # Ensure there are exactly four non-eliminated teams
        teams = list(Team.objects.filter(tournament=tournament, eliminated=False))
        if len(teams) != 4:
            print("Error: There are not exactly four teams eligible for the final.")
            continue  # Skip if the precondition is not met

        new_lobby_name = "Final Lobby"

        # Fetch the top 5 adjudicators based on their points
        adjudicators = list(Adjudicator.objects.filter(tournament=tournament).order_by('-points')[:5])

        if len(adjudicators) < 5:
            print("Error: Not enough high-point adjudicators available for the final.")
            continue

        # Create a new lobby for the final
        new_lobby = Lobby.objects.create(
            tournament=tournament,
            name=new_lobby_name,
            outround=True,
            round=10
        )

        # Randomly assign positions to each team
        positions = ['OG', 'OO', 'CG', 'CO']
        random.shuffle(positions)
        for team, position in zip(teams, positions):
            TeamAssignment.objects.create(
                tournament=tournament,
                lobby=new_lobby,
                team=team,
                position=position
            )

        # Check for conflicts and assign adjudicators
        assigned_adjudicators = 0
        for adjudicator in adjudicators:
            if check_strict_conflict(adjudicator, teams) or check_soft_conflict(adjudicator, teams):
                continue  # Skip adjudicators who have conflicts with any of the teams
            
            # Attach the adjudicator to the lobby if no conflicts are found
            new_lobby.adjudicators.add(adjudicator)
            assigned_adjudicators += 1
            
            if assigned_adjudicators == 5:
                break  # Stop after assigning 5 adjudicators

        if assigned_adjudicators < 5:
            print(f"Only {assigned_adjudicators} adjudicators were assigned due to conflicts. Additional adjudicators may be needed.")

admin.site.register_action(continuing4, 'Continue to final')

def foldingpsf(modeladmin, request, queryset):
    for tournament in queryset:
        teams = list(Team.objects.filter(tournament=tournament))
        teams.sort(key=lambda team: (-team.total_team_points(), -team.teams_total_speaker_points()))

        # Specify the lobby configurations
        lobby_configs = [
            (teams[4], teams[7], teams[8], teams[11]),  # Teams for the first lobby
            (teams[5], teams[6], teams[9], teams[10])   # Teams for the second lobby
        ]

        # Fetch sufficient adjudicators for assignment, ensuring enough for up to 5 per lobby
        adjudicators = list(Adjudicator.objects.filter(tournament=tournament).order_by('-points'))
        if len(adjudicators) < 2:  # Expecting at least 5 adjudicators per lobby
            print("Error: Not enough adjudicators for the lobbies.")
            return
        
        # Shuffle the list of adjudicators to randomize their assignment to lobbies
        
        adjudicator_queue = deque(adjudicators)

        lobbies = []
        for index, team_group in enumerate(lobby_configs):
            lobby_name = f"PSF Lobby {index + 1}"
            lobby = Lobby.objects.create(
                tournament=tournament,
                name=lobby_name,
                outround=True,
                round=12
            )
            lobbies.append(lobby)
            
            # Assign positions randomly
            positions = ['OG', 'OO', 'CG', 'CO']
            random.shuffle(positions)
            for i, team in enumerate(team_group):
                TeamAssignment.objects.create(
                    tournament=tournament,
                    lobby=lobby,
                    team=team,
                    position=positions[i]
                )

        # Assign up to 5 adjudicators to each lobby
        for lobby in lobbies:
            while len(lobby.adjudicators.all()) < 5 and adjudicator_queue:
                adjudicator = adjudicator_queue.popleft()
                lobby.adjudicators.add(adjudicator)

        # Mark teams below the 12th place as eliminated
        for team in teams[12:]:
            team.eliminated = True
            team.save()

admin.site.add_action(foldingpsf, 'Folding Partial-Semi Final')


def foldingpqf(modeladmin, request, queryset):
    for tournament in queryset:
        # Retrieve and sort teams
        teams = list(Team.objects.filter(tournament=tournament))
        teams.sort(key=lambda team: (-team.total_team_points(), -team.teams_total_speaker_points()))

        # Define the match groups
        match_groups = [
            (teams[8], teams[23], teams[15], teams[16]),
            (teams[9], teams[22], teams[14], teams[17]),
            (teams[10], teams[21], teams[13], teams[18]),
            (teams[11], teams[20], teams[12], teams[19]),
        ]

        # Retrieve top adjudicators and prepare for assignment
        adjudicators = list(Adjudicator.objects.filter(tournament=tournament).order_by('-points'))
        if len(adjudicators) < 4:  # Fetch enough adjudicators to rotate through up to 5 per lobby
            print("Not enough adjudicators to assign to each lobby.")
            return

        # Shuffle adjudicators for random distribution
        random.shuffle(adjudicators)
        adjudicator_queue = deque(adjudicators)  # Use a deque for efficient rotation

        # Create lobbies and assign adjudicators
        lobbies = []
        for index, group in enumerate(match_groups):
            lobby_name = f"PQF Lobby {index + 1}"
            lobby = Lobby.objects.create(
                tournament=tournament,
                name=lobby_name,
                outround=True,
                round=24
            )
            lobbies.append(lobby)

            # Assign up to 5 adjudicators to each lobby
            for _ in range(5):
                if adjudicator_queue:
                    adjudicator = adjudicator_queue.popleft()
                    lobby.adjudicators.add(adjudicator)
                    adjudicator_queue.append(adjudicator)  # Reappend to the end for round-robin distribution

            # Assign positions randomly to teams in the lobby
            positions = ['OG', 'OO', 'CG', 'CO']
            random.shuffle(positions)
            for i, team in enumerate(group):
                TeamAssignment.objects.create(
                    tournament=tournament,
                    lobby=lobby,
                    team=team,
                    position=positions[i]
                )

        # Eliminate teams below the top 24
        for team in teams[24:]:
            team.eliminated = True
            team.save()

        # Mark the tournament as having advanced to this round
        tournament.outround = True
        tournament.save()

admin.site.add_action(foldingpqf, 'Folding Partial-Quarter Final')


def setup_next_round(modeladmin, request, queryset):
    for tournament in queryset:
        # Retrieve and sort teams
        teams = list(Team.objects.filter(tournament=tournament))
        teams.sort(key=lambda team: (-team.total_team_points(), -team.teams_total_speaker_points()))

        if len(teams) < 24:
            print("Not enough teams to form the next round.")
            continue

        # Define the specific teams for each lobby
        lobby_one_teams = [teams[0], teams[7]]
        lobby_two_teams = [teams[1], teams[6]]
        lobby_three_teams = [teams[2], teams[5]]
        lobby_four_teams = [teams[3], teams[4]]

        # Fetching non-eliminated teams from specific previous lobbies
        lobby_one_additional = Team.objects.filter(
            tournament=tournament,
            eliminated=False,
            id__in=[teams[8].id, teams[15].id, teams[16].id, teams[23].id]
        ).order_by('-total_points')[:2]

        lobby_two_additional = Team.objects.filter(
            tournament=tournament,
            eliminated=False,
            id__in=[teams[9].id, teams[14].id, teams[17].id, teams[22].id]
        ).order_by('-total_points')[:2]

        lobby_three_additional = Team.objects.filter(
            tournament=tournament,
            eliminated=False,
            id__in=[teams[10].id, teams[13].id, teams[18].id, teams[21].id]
        ).order_by('-total_points')[:2]

        lobby_four_additional = Team.objects.filter(
            tournament=tournament,
            eliminated=False,
            id__in=[teams[11].id, teams[12].id, teams[19].id, teams[20].id]
        ).order_by('-total_points')[:2]

        # Combine and shuffle the teams for random position assignment
        lobby_one_teams.extend(lobby_one_additional)
        lobby_two_teams.extend(lobby_two_additional)
        lobby_three_teams.extend(lobby_three_additional)
        lobby_four_teams.extend(lobby_four_additional)

        semi_final_groups = [
            ('Quarter Final Lobby 1', lobby_one_teams),
            ('Quarter Final Lobby 2', lobby_two_teams),
            ('Quarter Final Lobby 3', lobby_three_teams),
            ('Quarter Final Lobby 4', lobby_four_teams)
        ]

        # Retrieve and shuffle adjudicators
        adjudicators = list(Adjudicator.objects.filter(tournament=tournament).order_by('-points'))
        if len(adjudicators) < 4:  # Need at least 5 adjudicators per lobby
            print("Not enough adjudicators.")
            continue

        # Shuffle adjudicators for random distribution
        random.shuffle(adjudicators)
        adjudicator_queue = deque(adjudicators)  # Use a deque for efficient rotation

        for index, (lobby_name, teams_group) in enumerate(semi_final_groups):
            lobby = Lobby.objects.create(
                tournament=tournament,
                name=lobby_name,
                outround=True,
                round=16
            )

            # Assign up to 5 adjudicators to each lobby
            for _ in range(5):
                if adjudicator_queue:
                    adjudicator = adjudicator_queue.popleft()
                    lobby.adjudicators.add(adjudicator)
                    adjudicator_queue.append(adjudicator)  # Reappend to the end for round-robin distribution

            # Assign positions randomly to teams in the lobby
            positions = ['OG', 'OO', 'CG', 'CO']
            random.shuffle(positions)
            for i, team in enumerate(teams_group):
                TeamAssignment.objects.create(
                    tournament=tournament,
                    lobby=lobby,
                    team=team,
                    position=positions[i]
                )

        print(f"Tournament {tournament.name} updated to the next round with balanced adjudicator distribution.")

admin.site.add_action(setup_next_round, 'Setup Next Round After Partial QF')


def setup_semi_finals(modeladmin, request, queryset):
    for tournament in queryset:
        teams = list(Team.objects.filter(tournament=tournament))
        teams.sort(key=lambda team: (-team.total_points, -team.total_speaker_points))

        if len(teams) < 12:
            print("Not enough teams to form semi-finals.")
            continue

        # Determine the specific teams for each lobby
        lobby_one_teams = [teams[0], teams[3]]  # First and Fourth highest teams
        lobby_two_teams = [teams[1], teams[2]]  # Second and Third highest teams

        # Fetching non-eliminated teams from specific lobbies
        lobby_one_additional = Team.objects.filter(
            tournament=tournament,
            eliminated=False,
            id__in=[teams[4].id, teams[7].id, teams[8].id, teams[11].id]
        )

        lobby_two_additional = Team.objects.filter(
            tournament=tournament,
            eliminated=False,
            id__in=[teams[5].id, teams[6].id, teams[9].id, teams[10].id]
        )

        # Combine and shuffle the teams for random position assignment
        lobby_one_teams.extend(lobby_one_additional)
        lobby_two_teams.extend(lobby_two_additional)

        semi_final_groups = [
            ('PSF Lobby 1', lobby_one_teams),
            ('PSF Lobby 2', lobby_two_teams)
        ]

        adjudicators = list(Adjudicator.objects.filter(tournament=tournament).order_by('-points'))
        if len(adjudicators) < 2:  
            print("Not enough adjudicators.")
            continue

        # Split adjudicators to ensure equal high-point adjudicator distribution
        top_adjudicators = adjudicators[:10]  # Assuming 10 or more adjudicators are available
        random.shuffle(top_adjudicators)
        adjudicator_queue = deque(top_adjudicators[:5] + top_adjudicators[5:])  # Round-robin queue for fairness

        for index, (lobby_name, teams_group) in enumerate(semi_final_groups):
            lobby = Lobby.objects.create(
                tournament=tournament,
                name=lobby_name,
                outround=True,
                round=8
            )

            # Assign adjudicators
            while len(lobby.adjudicators.all()) < 5 and adjudicator_queue:
                adjudicator = adjudicator_queue.popleft()
                lobby.adjudicators.add(adjudicator)

            positions = ['OG', 'OO', 'CG', 'CO']
            random.shuffle(positions)
            for i, team in enumerate(teams_group):
                TeamAssignment.objects.create(
                    tournament=tournament,
                    lobby=lobby,
                    team=team,
                    position=positions[i]
                )

        print(f"Tournament {tournament.name} updated to semi-final stage with balanced adjudicator distribution.")

admin.site.add_action(setup_semi_finals, 'Setup Semi Finals after Partial SF')