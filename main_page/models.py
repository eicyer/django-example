from django.db import models
from django.urls import reverse
from django.contrib.auth.models import Group
from django.utils import timezone


# Create your models here.
class Tournament(models.Model):
    name = models.CharField(max_length=100,unique = True, primary_key = True)
    host = models.CharField(max_length=100,null=True)
    date = models.DateTimeField(max_length=100)
    round = models.IntegerField(default=1)
    outround = models.BooleanField(default = False)
    motions = models.TextField(max_length=400,null=True,blank=True)
    #image = models.ImageField()
    adjudicator_view_accessible = models.BooleanField(default=False, verbose_name="Juri Listesini Görünür Yap")
    team_view_accessible = models.BooleanField(default=False, verbose_name="Takım Listesini Görünür Yap")
    participant_view_accessible = models.BooleanField(default=False, verbose_name="Katılımcı Listesini Görünür Yap")
    ordered_speaker_view_accessible = models.BooleanField(default=False, verbose_name="Konuşmacı Puanlarını Yap")
    ordered_team_view_accessible = models.BooleanField(default=False, verbose_name="Takım Puanlarını Görünür Yap")
    r1_view_accessible = models.BooleanField(default=False, verbose_name="1. Raundu Görünür Yap")
    r2_view_accessible = models.BooleanField(default=False, verbose_name="2. Raundu Görünür Yap")
    r3_view_accessible = models.BooleanField(default=False, verbose_name="3. Raundu Görünür Yap")
    r4_view_accessible = models.BooleanField(default=False, verbose_name="4. Raundu Görünür Yap")
    r5_view_accessible = models.BooleanField(default=False, verbose_name="5. Raundu Görünür Yap")
    otuziki_view_accessible = models.BooleanField(default=False, verbose_name="Ön Çeyrek Turunu Görünür Yap")
    yirmidort_view_accessible = models.BooleanField(default=False, verbose_name="Kısmi Çeyrek Turunu Görünür Yap")
    onalti_view_accessible = models.BooleanField(default=False, verbose_name="Çeyrek Final Turunu Görünür Yap")
    oniki_view_accessible = models.BooleanField(default=False, verbose_name="Kısmi Yarı Turunu Görünür Yap")
    sekiz_view_accessible = models.BooleanField(default=False, verbose_name="Yarı Final Turunu Görünür Yap")
    final_view_accessible = models.BooleanField(default=False, verbose_name="Final Turunu Görünür Yap")
   
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse("tourn_info", kwargs={"pk": self.pk})

    class Meta:
        ordering = ["date"]
    
    def save(self, *args, **kwargs):
        # Custom save logic
        super().save(*args, **kwargs)