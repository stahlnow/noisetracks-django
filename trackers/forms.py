__author__ = 'stahl'

from django import forms
from django.utils.translation import ugettext_lazy as _

from userena.forms import SignupForm


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

        A bit of hackery to get the first name and last name at the top of the
        form instead at the end.

        """
        super(SignupFormBeta, self).__init__(*args, **kw)
        # Put the first and last name at the top
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

        #new_user.first_name = self.cleaned_data['first_name']
        #new_user.last_name = self.cleaned_data['last_name']
        new_user.beta_access = self.cleaned_data['beta_access']
        new_user.save()

        # Userena expects to get the new user from this form, so return the new
        # user.
        return new_user

