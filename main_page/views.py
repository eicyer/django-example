from main_page import models
from datetime import datetime, timedelta
from django.shortcuts import render, get_object_or_404
from .models import Tournament
from django.utils import timezone
from django.views.generic import ListView, TemplateView,DetailView


def tourn_list_view(request):
    today = timezone.now()
    previous_saturday = today - timedelta(days=(today.weekday() + 2) % 7)

    # Categorize the data
    before_weekend = []
    in_weekend = []
    after_weekend = []

    queryset = Tournament.objects.all()  # Replace with your queryset
    
    for item in queryset:
        if item.date < previous_saturday:
            before_weekend.append(item)
        elif previous_saturday <= item.date < today:
            in_weekend.append(item)
        else:
            after_weekend.append(item)

    return render(request, 'main_page/main_p.html', {
        'before_weekend': before_weekend,
        'in_weekend': in_weekend,
        'after_weekend': after_weekend,
    })
    

def host_view(request):
    return render(request,"main_page/host_turn.html")

def tourn_info_view(request, tournament_name):
    template = "tourn_info/tournament_detail.html"
    tournament = get_object_or_404(Tournament, name=tournament_name)
    context = {'tournament': tournament}
    return render(request,template,context)