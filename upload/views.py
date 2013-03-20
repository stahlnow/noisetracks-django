# -*- coding: utf-8 -*-
import uuid
import os
import datetime
from django.conf import settings
from django.shortcuts import render_to_response
from django.template import RequestContext, Template
from django.template.loader import render_to_string
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required

from django.contrib.gis.geos import Point
from django.contrib.gis.gdal import DataSource

from tracks.models import Entry
from upload.forms import EntryForm


def handle_uploaded_file(f,n):
    destination = open(n, 'wb+')
    for chunk in f.chunks():
        destination.write(chunk)
    destination.close()


# Remove CRSF protection for external access
@csrf_exempt
# @login_required
def upload(request):
    # Handle file upload
    if request.method == "POST":
  
        form = EntryForm(request.POST, request.FILES)
        
        if form.is_valid():
        	#u = str(uuid.uuid1())
        	#fname = os.path.join(settings.MEDIA_ROOT, u)
        	#handle_uploaded_file(request.FILES['wavfile'],fname)
        	
        	user_id = request.POST.get('user_id')
        	newdoc = Document(wavfile = request.FILES['wavfile'], likes = 100)
        	newdoc.save()
        	
        	return HttpResponseRedirect(reverse('upload.views.upload'))
        	#return HttpResponse(content="", status=201)
        
    else:
        form = EntryForm() # A empty, unbound form
        # return  HttpResponseBadRequest()

    # Load entries for the list page
    entries = Entry.objects.all()

    # Render list page with the documents and the form
    return render_to_response(
        'upload/upload.html',
        {'entries': entries, 'form': form},
        context_instance=RequestContext(request)
    )
