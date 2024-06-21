from django.db import models
from main_page.models import Tournament
from django.core.exceptions import ValidationError
from django.contrib.auth.models import Group

#class AdjudicatorGroup(Group):
 #   name = models.CharField(max_length = 50)
  #  institution = models.CharField(max_length=50)
   # committee = models.BooleanField(null=True, blank=True)
    #experience = models.TextField(null=True, blank=True)
    #tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)

    #def __str__(self):
     #   return self.name

class Adjudicator(models.Model):
    name = models.CharField(max_length = 50)
    institution = models.CharField(max_length = 50)
    #commitee = models.BooleanField(null=True,blank=True)
    experience = models.TextField(null=True,blank=True)
    points = models.IntegerField(default = 0)
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    def __str__(self):
        return self.name   
class Team(models.Model):
    name = models.CharField(max_length = 50)
    institution = models.CharField(max_length = 50,null=True)
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE,related_name = "teams")
    og = models.IntegerField(default=0)
    oo = models.IntegerField(default=0)
    cg = models.IntegerField(default=0)
    co = models.IntegerField(default=0)
    #participants = models.CharField(max_length=100)
    r1_pt = models.IntegerField(default=0)
    r2_pt = models.IntegerField(default=0)
    r3_pt = models.IntegerField(default=0)
    r4_pt = models.IntegerField(default=0)
    r5_pt = models.IntegerField(default=0)
    total_points = models.IntegerField(default=0, editable=False) 
    total_speaker_points = models.IntegerField(default=0, editable=False)
    eliminated = models.BooleanField(default = False)
    class Meta:
        permissions = (("set_r1_pt","can set round 1's team points"),
                       ("set_r2_pt","can set round 2's team points"),
                       ("set_r3_pt","can set round 3's team points"),
                       ("set_r4_pt","can set round 4's team points"),
                       ("set_r5_pt","can set round 5's team points"))
    def total_team_points(self):
        return self.r1_pt + self.r2_pt + self.r3_pt + self.r4_pt + self.r5_pt
    def teams_total_speaker_points(self):
        return sum(participant.total_spk_points() for participant in self.participants.all())
    def __str__(self):
        return self.name   
    def save(self, *args, **kwargs):
            # First save: establish the primary key if it's a new instance
        creating = not self.pk
        super(Team, self).save(*args, **kwargs)

        # Calculate and update total points every time save is called
        new_total_points = self.total_team_points()
        if self.total_points != new_total_points:
            self.total_points = new_total_points
            super(Team, self).save(*args, **kwargs)

        new_speaker_points = self.teams_total_speaker_points()
        if self.total_speaker_points != new_speaker_points:
            self.total_speaker_points = new_speaker_points
            super(Team, self).save(*args, **kwargs)
        
class Participant(models.Model):
    name = models.CharField(max_length = 50)
    institution = models.CharField(max_length = 50,null=True)
    r1_spkr = models.IntegerField(default=0)
    r2_spkr = models.IntegerField(default=0)
    r3_spkr = models.IntegerField(default=0)
    r4_spkr = models.IntegerField(default=0)
    r5_spkr = models.IntegerField(default=0)
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE,related_name = 'participants')
    total_speaker_points = models.IntegerField(default=0, editable=False)
    context_object_name = 'participants'
    
    def total_spk_points(self):
        return self.r1_spkr + self.r2_spkr + self.r3_spkr + self.r4_spkr + self.r5_spkr
    def average_speaker_points(self):
        points = [self.r1_spkr, self.r2_spkr, self.r3_spkr, self.r4_spkr, self.r5_spkr]
        # Count only rounds with points > 0
        count = sum(1 for point in points if point > 0)
        if count == 0:
            return 0  # To avoid division by zero
        return sum(points) / count
    
    class Meta:
        permissions = (
                       ("set_r3_spkr","can set round 3's speaker points"),
                       ("set_r4_spkr","can set round 4's speaker points"),
                       ("set_r5_spkr","can set round 5's speaker points"))
    def __str__(self):
        return self.name   
    def save(self, *args, **kwargs):
        # First save to ensure Participant has all fields calculated
        super(Participant, self).save(*args, **kwargs)
    
    # If this participant is linked to a team, trigger a save on the team
    # to recalculate its total speaker points
        if self.team:
            self.team.save()
 # Trigger a save on the team to recalculate its total speaker points
 



class Lobby(models.Model):
    name = models.CharField(max_length=100, null=True, blank=True)
    teams = models.ManyToManyField(Team, through='TeamAssignment')
    adjudicators = models.ManyToManyField(Adjudicator)  # Changed to ManyToManyField
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    round = models.IntegerField(default=1)
    outround = models.BooleanField(default=False)

    def __str__(self):
        return self.name or "Unnamed Lobby"

    def clean(self):
        # Custom validation to ensure at least one adjudicator is assigned
        if not self.adjudicators.exists():
            raise ValidationError("At least one adjudicator is required for each lobby.")

class TeamAssignment(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    lobby = models.ForeignKey(Lobby, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    position = models.CharField(max_length=2, choices=[('OG', 'Opening Government'), ('OO', 'Opening Opposition'), ('CG', 'Closing Government'), ('CO', 'Closing Opposition')])

    def save(self, *args, **kwargs):
        # Set the round to match the related lobby's round
        if self.lobby:
            self.round = self.lobby.round
        super(TeamAssignment, self).save(*args, **kwargs)

class Conflict(models.Model):
    adjudicator = models.ForeignKey(Adjudicator, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, null=True, blank=True)
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, null=True, blank=True)
    is_strict = models.BooleanField(default=False)
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    def __str__(self):
        if self.team:
            return f"Conflict with {self.adjudicator} and Team {self.team}"
        return f"Conflict with {self.adjudicator} and Participant {self.participant}"
    