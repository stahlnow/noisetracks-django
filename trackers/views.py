from userena import views as userena_views
from userena.views import ExtraContextTemplateView
from trackers.forms import SignupFormBeta, EditProfileFormBeta


def signup(request, signup_form=SignupFormBeta, template_name='userena/signup_form.html', success_url=None,
           extra_context=None):

    form = SignupFormBeta()

    if request.method == 'POST':    # If the form has been submitted...
        form = SignupFormBeta(request.POST, request.FILES)
        if request.POST.get('beta_access') == 'noisetracker':
            return userena_views.signup(request, signup_form)

    if not extra_context: extra_context = dict()
    extra_context['form'] = form
    return ExtraContextTemplateView.as_view(template_name=template_name, extra_context=extra_context)(request)


from guardian.decorators import permission_required_or_403
from userena.decorators import secure_required
from userena.utils import get_profile_model


'''
not used right now
'''
@secure_required
@permission_required_or_403('change_profile', (get_profile_model(), 'user__username', 'username'))
def profile_edit(request, username, edit_profile_form=EditProfileFormBeta,
                 template_name='userena/profile_form.html', success_url=None,
                 extra_context=None, **kwargs):

    return userena_views.profile_edit(request)