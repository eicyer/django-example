from django import forms
from django.forms import MultiValueField
from main_page.models import Tournament

class TournamentAdminForm(forms.ModelForm):
    view_access_fields = MultiValueField(
        fields=[
            forms.BooleanField(required=False, label='Adjudicator View Accessible'),
            forms.BooleanField(required=False, label='Team View Accessible'),
            forms.BooleanField(required=False, label='Participant View Accessible'),
            forms.BooleanField(required=False, label='Ordered Speaker View Accessible'),
            forms.BooleanField(required=False, label='Ordered Team View Accessible'),
            forms.BooleanField(required=False, label='Round 1 View Accessible'),
            forms.BooleanField(required=False, label='Round 2 View Accessible'),
            forms.BooleanField(required=False, label='Round 3 View Accessible'),
            forms.BooleanField(required=False, label='Round 4 View Accessible'),
            forms.BooleanField(required=False, label='Round 5 View Accessible'),
            forms.BooleanField(required=False, label='32 View Accessible'),
            forms.BooleanField(required=False, label='24 View Accessible'),
            forms.BooleanField(required=False, label='16 View Accessible'),
            forms.BooleanField(required=False, label='12 View Accessible'),
            forms.BooleanField(required=False, label='8 View Accessible'),
            forms.BooleanField(required=False, label='Final View Accessible'),
        ],
        widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        model = Tournament
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            self.fields['view_access_fields'].initial = [
                self.instance.adjudicator_view_accessible,
                self.instance.team_view_accessible,
                self.instance.participant_view_accessible,
                self.instance.ordered_speaker_view_accessible,
                self.instance.ordered_team_view_accessible,
                self.instance.r1_view_accessible,
                self.instance.r2_view_accessible,
                self.instance.r3_view_accessible,
                self.instance.r4_view_accessible,
                self.instance.r5_view_accessible,
                self.instance.otuziki_view_accessible,
                self.instance.yirmidort_view_accessible,
                self.instance.onalti_view_accessible,
                self.instance.oniki_view_accessible,
                self.instance.sekiz_view_accessible,
                self.instance.final_view_accessible,
            ]

    def save(self, commit=True):
        data = self.cleaned_data['view_access_fields']
        self.instance.adjudicator_view_accessible = data[0]
        self.instance.team_view_accessible = data[1]
        self.instance.participant_view_accessible = data[2]
        self.instance.ordered_speaker_view_accessible = data[3]
        self.instance.ordered_team_view_accessible = data[4]
        self.instance.r1_view_accessible = data[5]
        self.instance.r2_view_accessible = data[6]
        self.instance.r3_view_accessible = data[7]
        self.instance.r4_view_accessible = data[8]
        self.instance.r5_view_accessible = data[9]
        self.instance.otuziki_view_accessible = data[10]
        self.instance.yirmidort_view_accessible = data[11]
        self.instance.onalti_view_accessible = data[12]
        self.instance.oniki_view_accessible = data[13]
        self.instance.sekiz_view_accessible = data[14]
        self.instance.final_view_accessible = data[15]
        return super().save(commit)
