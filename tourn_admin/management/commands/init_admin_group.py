from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from django.apps import apps
from tourn_info.models import Adjudicator
from main_page.models import Tournament

# class Command(BaseCommand):
   # help = 'Initialize admin group and permissions'

    #def handle(self, *args, **options):
        
     #   content_type = ContentType.objects.get_for_model(Tournament)
      #  tourn_edit_permission, created = Permission.objects.get_or_create(
       # codename='can_change_tournament',
        # name='Can Change Tournament',
        # content_type=content_type, )
        
        # for tournament in Tournament.objects.all():
            # Define a group name for each tournament (e.g., 'Tournament Group 1')
           #  group_name = f'Tournament Group {tournament.id}'

            # Create or retrieve the group
            # group, created = Group.objects.get_or_create(name=group_name)

            # Add the 'can_change_tournament' permission to the group
            # group.permissions.add(tourn_edit_permission)

    

        
        
