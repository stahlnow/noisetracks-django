from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _

from userena.models import UserenaBaseProfile
from guardian.shortcuts import assign

from tastypie.models import create_api_key


ASSIGNED_PERMISSIONS = {
    'profile':
        (('view_profile', 'Can view profile'),
         ('change_profile', 'Can change profile'),
         ('delete_profile', 'Can delete profile')),
    'user':
        (('change_user', 'Can change user'),
         ('delete_user', 'Can delete user'))
}


class Profile(UserenaBaseProfile):
    user = models.OneToOneField(User, unique=True, verbose_name=_('User'), related_name=_('Profile'))
    name = models.CharField(max_length=30)
    website = models.URLField()
    bio = models.CharField(max_length=160)


def create_profile(sender, **kwargs):
    """
    A signal for hooking up automatic ``Profile`` creation.
    """
    if kwargs.get('created') is True:

        p = Profile.objects.create(user=kwargs.get('instance'))

        # Give permissions to view and change profile
        for perm in ASSIGNED_PERMISSIONS['profile']:
            assign(perm[0], kwargs.get('instance'), p)

        # Give permissions to view and change itself
        for perm in ASSIGNED_PERMISSIONS['user']:
            assign(perm[0], kwargs.get('instance'), kwargs.get('instance'))

# create profile, when user is created
# -> deactivate before initial syncdb!
models.signals.post_save.connect(create_profile, sender=User)

# create api key, when user is created
models.signals.post_save.connect(create_api_key, sender=User)
