from tastypie import fields
from tastypie.exceptions import NotFound, BadRequest
from django.core.context_processors import request

from tastypie.contrib.gis.resources import ModelResource

from tastypie.resources import ALL_WITH_RELATIONS, Resource
from tastypie.authentication import Authentication, BasicAuthentication, ApiKeyAuthentication
from tastypie.authorization import Authorization
from tastypie.models import ApiKey
from tastypie.validation import FormValidation

from django.contrib.contenttypes.models import ContentType
from tastypie.contrib.contenttypes.fields import GenericForeignKeyField

from django.contrib.auth.models import User

import django.core.exceptions
from django.db import models
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseBadRequest

from tracks.models import AudioFile, Entry
from trackers.models import Profile
from voting.models import Vote

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
        list_allowed_methods = ["get"]
        detail_allowed_methods = ["get"]
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
        except django.core.exceptions.ObjectDoesNotExist:
            pass

        # set email only if it belongs to the user
        if bundle.obj.pk == bundle.request.user.pk:
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

    score = fields.IntegerField()   # total score for entry based on likes
    vote = fields.IntegerField()    # 0 = user doesn't care, 1 = user likes, -1 = user dislikes

    class Meta:
        queryset = Entry.objects.all()
        resource_name = 'entry'
        list_allowed_methods = ["get", "post"]
        detail_allowed_methods = ["get", "put"]
        include_resource_uri = True

        limit = 20

        fields = ['uuid', 'location', 'recorded', 'created', 'score', 'likes']

        ordering = ['created', 'recorded', 'user']

        filtering = {
            'created': ['exact', 'lt', 'lte', 'gte', 'gt'],
            'recorded': ['exact', 'lt', 'lte', 'gte', 'gt'],
            'audiofile': ALL_WITH_RELATIONS,
            'user': ALL_WITH_RELATIONS
        }	
        
        authentication = ApiKeyAuthentication()
        authorization = Authorization()

    def put_detail(self, request, **kwargs):
        pk = int(kwargs['pk'])
        entry = Entry.objects.get(pk=pk)
        if entry.user == request.user:
            return super(EntryResource, self).put_detail(request, **kwargs)
        else:
            return HttpResponse(status=401)

    def hydrate_audiofile(self, bundle):
        try:
            bundle.obj.audiofile = AudioFile.objects.get(uuid=bundle.data['audio'])
            return bundle
        except AudioFile.DoesNotExist:
            raise BadRequest('Audio file does not exist.')

    def hydrate_user(self, bundle):
        bundle.obj.user = bundle.request.user
        return bundle

    def dehydrate_score(self, bundle):
        return Vote.objects.get_score(bundle.obj).get('score')

    def dehydrate_vote(self, bundle):
        ct = ContentType.objects.get_for_model(bundle.obj)
        try:
            v = Vote.objects.get(content_type=ct, object_id=bundle.obj._get_pk_val(), user=bundle.request.user)
            return 1 if v.is_upvote() else -1
        except models.ObjectDoesNotExist:
            return 0


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


class EntryVoteResource(Resource):
    uuid = fields.CharField(attribute='uuid')
    vote = fields.IntegerField(attribute='vote')

    class Meta:
        resource_name = 'vote'
        object_class = Vote
        list_allowed_methods = ["post"]
        detail_allowed_methods = []
        include_resource_uri = False
        always_return_data = True
        authentication = ApiKeyAuthentication()
        authorization = Authorization()

    def detail_uri_kwargs(self, bundle_or_obj):
        kwargs = {}
        return kwargs

    def obj_create(self, bundle, request=None, **kwargs):
        bundle = self.full_hydrate(bundle)

        try:
            e = Entry.objects.get(uuid=bundle.data.get('uuid'))
        except Entry.DoesNotExist:
            e = None
        Vote.objects.record_vote(e, request.user, bundle.data.get('vote'))

        return bundle

    def obj_update(self, bundle, request=None, **kwargs):
        return self.obj_create(bundle, request, **kwargs)


'''
class EntryVoteResourceForm(ModelResource):
    class Meta:
        resource_name = 'voteform'
        list_allowed_methods = ["post"]
        detail_allowed_methods = []
        authentication = ApiKeyAuthentication()
        authorization = Authorization()

    def post_list(self, request, **kwargs):
        uuid = request.POST.get('uuid', None)
        vote = request.POST.get('vote', None)
        if None in (uuid, vote):
            return HttpResponseBadRequest('dude, we need uuid and a vote (0, -1 or +1)')
        try:
            e = Entry.objects.get(uuid=uuid)
        except models.ObjectDoesNotExist:
            return HttpResponseBadRequest('this entry was not found.')

        if not vote > 1 and not vote < -1:
            Vote.objects.record_vote(e, request.user, vote)
            return self.create_response(request, {'result': vote})
        return HttpResponseBadRequest()

class ContentTypeResource(ModelResource):
    class Meta:
        resource_name = 'content_type'
        queryset = ContentType.objects.all()
        authentication = ApiKeyAuthentication()
        authorization = Authorization()


class VoteResource(ModelResource):
    user = fields.ForeignKey(UserResource, 'user')
    content_object = GenericForeignKeyField({ContentType: ContentTypeResource, Entry: EntryResource}, 'object')

    class Meta:
        queryset = Vote.objects.all()
        resource_name = 'votes'
        authentication = ApiKeyAuthentication()
        authorization = Authorization()
        always_return_data = True
        include_resource_uri = False
        fields = ['id', 'vote', 'content_object']

    def hydrate_user(self, bundle):
        bundle.obj.user = bundle.request.user
        return bundle

    def obj_update(self, bundle, **kwargs):
        return bundle

'''