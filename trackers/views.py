from userena import views as userena_views
from userena.views import ExtraContextTemplateView
from trackers.forms import SignupFormBeta


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
