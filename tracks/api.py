from tastypie import fields
from tastypie.exceptions import NotFound, BadRequest

from tastypie.contrib.gis.resources import ModelResource
#from tastypie.resources import ModelResource

from tastypie.resources import ALL_WITH_RELATIONS
from tastypie.authentication import Authentication, BasicAuthentication, ApiKeyAuthentication
from tastypie.authorization import Authorization
from tastypie.models import ApiKey
from tastypie.validation import FormValidation

from django.contrib.auth.models import User

from django.contrib.gis.db import models

from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError

from tracks.models import AudioFile, Entry
from trackers.models import Profile

from userena.forms import SignupForm


class BaseModelResource(ModelResource):
    @classmethod
    def get_fields(cls, fields=None, excludes=None):
        """
        Unfortunately we must override this method because tastypie ignores 'blank' attribute
        on model fields.

        Here we invoke an insane workaround hack due to metaclass inheritance issues:
        http://stackoverflow.com/questions/12757468/invoking-super-in-classmethod-called-from-metaclass-new
        """
        this_class = next(c for c in cls.__mro__ if c.__module__ == __name__ and c.__name__ == 'BaseModelResource')
        fields = super(this_class, cls).get_fields(fields=fields, excludes=excludes)
        if not cls._meta.object_class:
            return fields
        for django_field in cls._meta.object_class._meta.fields:
            if django_field.blank is True:
                res_field = fields.get(django_field.name, None)
                if res_field:
                    res_field.blank = True
        return fields


class SignupResource(ModelResource):
    class Meta:
        queryset = User.objects.all()
        resource_name = 'signup'
        allowed_methods = ['post']
        validation = FormValidation(form_class=SignupForm)    # userena signup form is used here
        authentication = Authentication()
        authorization = Authorization()
        include_resource_uri = False
        fields = ['username', 'email']

    def obj_create(self, bundle, request=None, **kwargs):
        try:
            bundle = super(SignupResource, self).obj_create(bundle, request, **kwargs)
            bundle.obj.set_password(bundle.data.get('password1'))
            bundle.obj.email = bundle.data.get('email')
            bundle.obj.save()
        except IntegrityError:
            raise BadRequest('That username already exists')

        return bundle


class ApiTokenResource(ModelResource):
    class Meta:
        queryset = ApiKey.objects.all()
        resource_name = "token"
        include_resource_uri = False
        fields = ['key']
        list_allowed_methods = []
        detail_allowed_methods = ["get"]
        authentication = BasicAuthentication()

    def obj_get(self, request=None, **kwargs):
        if kwargs["pk"] != "auth":
            raise NotImplementedError("Resource not found")

        user = request.user
        if not user.is_active:
            raise NotFound("User not active")

        api_key = ApiKey.objects.get(user=request.user)
        return api_key


class UserResource(ModelResource):
    class Meta:
        queryset = User.objects.all()
        resource_name = 'user'
        authentication = ApiKeyAuthentication()
        authorization = Authorization()

        include_resource_uri = False
        fields = ['username']

        ordering = ['username']

        filtering = {
            'username': ALL_WITH_RELATIONS,
        }

    def dehydrate(self, bundle):
        try:
            bundle.data['mugshot'] = bundle.obj.get_profile().get_mugshot_url()
        except ObjectDoesNotExist:
            pass

        if bundle.request.user.pk == bundle.obj.pk:
            bundle.data['email'] = bundle.obj.email

        return bundle


class AudioFileResource(BaseModelResource):
    class Meta:
        queryset = AudioFile.objects.all()
        resource_name = 'audiofile'
        authentication = ApiKeyAuthentication()
        authorization = Authorization()

        include_resource_uri = False
        fields = ['file', 'spectrogram', 'status']

        filtering = {
            'created': ['exact', 'lt', 'lte', 'gte', 'gt'],
            'status': ['exact']
        }


class EntryResource(BaseModelResource):
    user = fields.ForeignKey(UserResource, 'user', full=True)

    audiofile = fields.ForeignKey(AudioFileResource, 'audiofile', full=True)

    class Meta:
        queryset = Entry.objects.all()
        resource_name = 'entry'
        authentication = ApiKeyAuthentication()
        authorization = Authorization()

        limit = 4

        fields = ['location','recorded', 'created', 'uuid']

        ordering = ['created', 'recorded', 'user']

        filtering = {
            'created': ['exact', 'lt', 'lte', 'gte', 'gt'],
            'recorded': ['exact', 'lt', 'lte', 'gte', 'gt'],
            'audiofile': ( ALL_WITH_RELATIONS ),
            'user': ( ALL_WITH_RELATIONS )
        }

    def hydrate_audiofile(self, bundle):
        try:
            a = AudioFile.objects.get(uuid=bundle.data['uuid'])
        except AudioFile.DoesNotExist:
            print 'file not found...'   # todo: error handling, currently returns 404
            return bundle
        bundle.obj.audiofile = a
        return bundle


class ProfileResource(ModelResource):
    user = fields.ToOneField(UserResource, 'user', full=True)

    class Meta:
        queryset = Profile.objects.all()
        resource_name = 'profile'
        include_resource_uri = False
        list_allowed_methods = ["get"]
        detail_allowed_methods = ["get"]

        fields = ['name', 'bio', 'website']

        ordering = ['user']

        filtering = {
            'user': ALL_WITH_RELATIONS,
        }
        authentication = ApiKeyAuthentication()
        authorization = Authorization()

    def dehydrate(self, bundle):
        bundle.data['tracks'] = bundle.obj.user.entry_set.count()    # number of tracks
        return bundle


