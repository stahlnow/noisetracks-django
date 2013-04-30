from django.conf.urls import patterns, url, include
from django.conf import settings
from django.conf.urls.static import static

from django.contrib.gis import admin

from tastypie.api import Api

from tracks.views import Entries
from tracks.api import SignupResource, ApiTokenResource, UserResource, AudioFileResource, EntryResource,\
    ProfileResource, EntryVoteResource


v1_api = Api(api_name='v1')
v1_api.register(SignupResource())
v1_api.register(ApiTokenResource())
v1_api.register(UserResource())
v1_api.register(AudioFileResource())
v1_api.register(EntryResource())
v1_api.register(ProfileResource())

#v1_api.register(ContentTypeResource())
#v1_api.register(VoteResource())
v1_api.register(EntryVoteResource())
#v1_api.register(EntryVoteResourceForm())


admin.autodiscover()

urlpatterns = patterns('',
                       #url(r'^$', Entries.as_view(), name='entries'),
                       #url(r'^$', 'tracks.views.map', name='home'),
                       url(r'^$', 'tracks.views.index', name='index'),
                       url(r'^beta/', 'tracks.views.beta', name='beta'),
                       url(r'^api/', include(v1_api.urls)),
                       url(r'^audio/', 'tracks.views.stream', name='stream'),
                       url(r'^upload/', 'tracks.views.upload', name='upload'),
                       url(r'^admin/', include(admin.site.urls)),
                       url(r'^', include('userena.urls')),
                       ) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


if settings.DEBUG:
    urlpatterns += patterns('',
                            (r'^audio/^', 'tracks.views.stream', {}),
                            )
