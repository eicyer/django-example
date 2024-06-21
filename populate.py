import os
import django
from faker import Faker
from django.utils import timezone
import datetime

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tab_project.settings")
django.setup()

from main_page.models import Tournament
from tourn_info.models import Participant, Team, Adjudicator

fakegen = Faker()

def populate_tourn(n=4):
    tournaments = []
    for i in range(n):
        nm = fakegen.name()
        dt = fakegen.date_object()  # Generates a date object
        # Convert date object to datetime object with time set to midnight
        dt_midnight = datetime.datetime(dt.year, dt.month, dt.day)
        # Make the datetime object timezone aware
        aware_dt = timezone.make_aware(dt_midnight)
        tourn, created = Tournament.objects.get_or_create(name=nm, date=aware_dt, round=1, outround=False)
        tournaments.append(tourn)
    return tournaments

def populate_adjudicators(tourns, n=16):
    adjudicators = []
    for tourn in tourns:
        for i in range(n):
            adjudicator_name = fakegen.name()
            institution_name = fakegen.company()
            point = fakegen.pyint(0,3)
            adjudicator, created = Adjudicator.objects.get_or_create(
                name=adjudicator_name, institution=institution_name, tournament=tourn, points=point
            )
            adjudicators.append(adjudicator)
    return adjudicators

def populate_teams(tourns, n=40):
    teams = []
    for tourn in tourns:
        for _ in range(n):
            team_name = fakegen.name()
            institution_name = fakegen.company()
            team, created = Team.objects.get_or_create(
                name=team_name,
                institution=institution_name,
                tournament=tourn
            )
            team.save()
            teams.append(team)
    return teams

def populate_participants(teams, n=2):
    for team in teams:
        for _ in range(n):
            partname = fakegen.name()
            participant, created = Participant.objects.get_or_create(
                name=partname,
                institution=team.institution,
                team=team,
                tournament=team.tournament
            )

if __name__ == "__main__":
    print("Populating script...")
    tourns = populate_tourn()
    teams = populate_teams(tourns)
    if teams is not None:
        populate_participants(teams)
        populate_adjudicators(tourns)
        print("Populating complete.")
    else:
        print("Failed to populate teams, terminating script.")
