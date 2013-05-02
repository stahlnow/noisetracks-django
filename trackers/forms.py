from django.contrib.admin import widgets

__author__ = 'stahl'

from django import forms
from django.utils.translation import ugettext_lazy as _

from userena.forms import SignupForm, EditProfileForm
from userena.utils import get_profile_model


class SignupFormBeta(SignupForm):
    """
    A form to demonstrate how to add extra fields to the signup form, in this
    case adding the first and last name.
    """
    beta_access = forms.CharField(label=_(u'Access Code'),
                                  max_length=12,
                                  required=True)

    def __init__(self, *args, **kw):
        """
        A bit of hackery to reorder items
        """
        super(SignupFormBeta, self).__init__(*args, **kw)
        # Put beta_access to top
        new_order = self.fields.keyOrder[:-1]
        new_order.insert(0, 'beta_access')
        self.fields.keyOrder = new_order

    def save(self):
        """
        Override the save method to save the first and last name to the user
        field.
        """
        # First save the parent form and get the user.
        new_user = super(SignupFormBeta, self).save()

        new_user.beta_access = self.cleaned_data['beta_access']
        new_user.save()

        # Userena expects to get the new user from this form, so return the new
        # user.
        return new_user


from form_utils.widgets import ImageWidget
from form_utils.fields import ClearableImageField

class EditProfileFormBeta(EditProfileForm):

    name = forms.CharField(label=_(u'Name'), max_length=30, required=False)

    website = forms.URLField(required=False)

    bio = forms.CharField(label=_(u'Bio'),
                          max_length=160,
                          required=False)

    mugshot = ClearableImageField(label=_(u'Photo'),
                                    widget=ImageWidget(),
                                    required=False)

    def __init__(self, *args, **kw):
        super(EditProfileForm, self).__init__(*args, **kw)
        # remove unused fields
        del self.fields["first_name"]
        del self.fields["last_name"]
        del self.fields["privacy"]

    class Meta:
        model = get_profile_model()
        exclude = ['user']

    def save(self, force_insert=False, force_update=False, commit=True):

        profile = super(EditProfileForm, self).save(commit=commit)

        # Save first and last name
        #user = profile.user
        #user.first_name = self.cleaned_data['first_name']
        #user.last_name = self.cleaned_data['last_name']
        #user.save()

        return profile