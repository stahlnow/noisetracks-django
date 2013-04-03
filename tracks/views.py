import uuid
import os
import datetime
import re
from django.conf import settings
from django.shortcuts import render_to_response
from django.template import RequestContext, Template
from django.template.loader import render_to_string
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest
from django.core.servers.basehttp import FileWrapper
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

from django.contrib.gis.geos import Point

from django.utils.decorators import method_decorator
from django.utils import timezone

from django.views.generic.list import ListView

from tastypie.models import ApiKey

from tracks.models import Entry, AudioFile
from tracks.forms import VoteForm, UploadForm
from voting.models import Vote

AUTH_HEADER_RE = re.compile(r"ApiKey .+:.+")


class Entries(ListView):
    model = Entry

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(Entries, self).dispatch(*args, **kwargs)


def stream(request):
    path = settings.PROJECT_ROOT + request.path

    if not (os.path.splitext(request.path)[1] == '.png'):
        response = HttpResponse(FileWrapper(open(path, "rb")), mimetype='audio/mpeg')
        response['Content-Length'] = os.path.getsize(path)
        response['Content-Disposition'] = 'filename=%s' % ( os.path.basename(request.path) )
        return response
    return HttpResponse(FileWrapper(open(path, "rb")), mimetype='image/png')


@csrf_exempt
def vote(request):
    if request.method == "POST":
        # Handle vote form
        form = VoteForm(request.POST, request.FILES)
        if form.is_valid():
            auth = request.META.get('HTTP_AUTHORIZATION')          # ApiKey Authorization header as defined in tastypie
            if auth:                                               # should look like "ApiKey user:key"
                if AUTH_HEADER_RE.match(auth):
                    auth = auth.split(' ')[1]
                    username = auth.split(':')[0]
                    api_key = auth.split(':')[1]
                else:
                    return HttpResponseBadRequest()                 # fail: bad header

                try:
                    user = User.objects.get(username=username)      # try getting user from table
                except ObjectDoesNotExist:
                    return HttpResponseBadRequest()                 # ups, user does not exist

                try:
                    key = ApiKey.objects.get(user=user).key         # try getting api key from user
                except ObjectDoesNotExist:
                    return HttpResponseBadRequest()                 # todo: send info to client, that the key is missing

                if api_key == key:                                  # check if the keys match
                    try:
                        e = Entry.objects.get(uuid=form.cleaned_data.get('uuid'))
                    except ObjectDoesNotExist:
                        return HttpResponseBadRequest('sorry dude, that entry was not found.')

                    if not form.cleaned_data.get('vote') > 1 and not form.cleaned_data.get('vote') < -1:
                        Vote.objects.record_vote(e, user, form.cleaned_data.get('vote'))
                    else:
                        return HttpResponseBadRequest('dude, votes should be 0, -1 or +1.')
                else:
                    # todo: send info to client, that the key is not valid
                    return HttpResponseBadRequest("keys don't match")

                return HttpResponse(content='', status=202)  # return with status 202 'accepted'
            else:
                return HttpResponseBadRequest("auth is empty")
        else:
            return HttpResponseBadRequest("form not valid")

    else:
        return HttpResponseBadRequest()

@csrf_exempt
def upload(request):
    if request.method == "POST":

        # Handle file upload
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            auth = request.META.get('HTTP_AUTHORIZATION')          # ApiKey Authorization header as defined in tastypie
            if auth:                                               # should look like "ApiKey user:key"
                if AUTH_HEADER_RE.match(auth):
                    auth = auth.split(' ')[1]
                    username = auth.split(':')[0]
                    api_key = auth.split(':')[1]
                else:
                    return HttpResponseBadRequest()                 # fail: bad header

                try:
                    user = User.objects.get(username=username)      # try getting user from table
                except ObjectDoesNotExist:
                    return HttpResponseBadRequest()                 # ups, user does not exist

                try:
                    key = ApiKey.objects.get(user=user).key         # try getting api key from user
                except ObjectDoesNotExist:
                    return HttpResponseBadRequest()                 # todo: send info to client, that the key is missing

                if api_key == key:                                  # check if the keys match
                    f = AudioFile(file=request.FILES['wavfile'], status=0)  # create file with status = waiting
                    f.save()
                else:
                    return HttpResponseBadRequest(
                        "keys don't match")         # todo: send info to client, that the key is not valid

                return HttpResponse(content=f.uuid, status=201)  # return with status 201 'created' + uuid of audiofile
            else:
                return HttpResponseBadRequest("auth is empty")
        else:
            return HttpResponseBadRequest("form not valid")

    else:
        return HttpResponseBadRequest()


def map(request):
    '''
    w = Document()
    w.uploader = request.user.get_profile()
    w.wavfile = 'bla.wav'
    w.date = datetime.datetime.now()
    w.geometry = Point((-38.462547000, 176.148087000))
    w.length = 1234.5
    w.likes = 100

    w.save()

    wavs = Entry.objects.order_by('-created')

    if request.user.is_authenticated():
        user_str = str("Hello, " + request.user.username + "!")
    else:
        user_str = "Anonymous"

    return render_to_response('tracks/index.html', {
    'user': user_str,
    'wavs': wavs,
    'content': render_to_string('tracks/wavs.html', {'wavs': wavs}),
    }, context_instance=RequestContext(request))
    '''

