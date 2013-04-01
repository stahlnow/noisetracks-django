import os
from django.utils.translation import ugettext as _
from django.conf import settings
from django.contrib.gis.db import models
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from django_extensions.db.fields import *

from subprocess import check_call


class BaseModel(models.Model):
    uuid = UUIDField()

    created = CreationDateTimeField()
    updated = ModificationDateTimeField()

    class Meta:
        abstract = True


audio_store = FileSystemStorage(location=settings.AUDIO_ROOT, base_url=settings.AUDIO_URL)


def generate_audiofile_path(obj, file):
    path = "%s%s" % (obj.uuid, os.path.splitext(file)[1])
    return path.replace('-', '/')


class AudioFile(BaseModel):
    file = models.FileField(upload_to=generate_audiofile_path, storage=audio_store)  # file path

    spectrogram = models.ImageField(upload_to=generate_audiofile_path, storage=audio_store,
                                    blank=True) # spectrogram, this is generated in post_save

    STATUS_CHOICES = ( (0, _('Waiting')), (1, _('Done')), (2, _('Error')), )

    status = models.PositiveIntegerField(default=0, choices=STATUS_CHOICES)        # .objects.filter(status='Done')

    # meta
    class Meta(BaseModel.Meta):
        app_label = 'tracks'
        verbose_name = _('audiofile')
        verbose_name_plural = _('audiofiles')
        ordering = ('-created', )

    def __unicode__(self):
        return self.file.url

    def spectrogram_img(self):
        return '<img src="http://stahlnow:8000/audio/%s" height="50px"/>' % self.spectrogram

    spectrogram_img.allow_tags = True



# create spectrogram and mp3 using sox
def post_save_audiofile(sender, **kwargs):
    if kwargs.get('created') is True:
        f = kwargs.get('instance')
        print '%s is being processed...' % f.file

        # spectrogram
        # same path/name as audio file with '-sp' added and '.png' as extension
        file_spec = os.path.splitext(f.file.name)[0] + '-sp.png'

        # mp3
        file_mp3 = os.path.splitext(f.file.name)[0] + '.mp3'

        try:
            check_call(["sox", f.file.name, "-S", "-n", "remix", "-", "spectrogram", "-m", "-y", "256", "-X", "50", "-r", "-l", "-z", "80", "-o", file_spec], cwd=settings.AUDIO_ROOT)
            f.spectrogram.name = file_spec
            check_call(["sox", f.file.name, file_mp3], cwd=settings.AUDIO_ROOT)


            f.file.name = file_mp3

            f.status = 1
            f.save()

        except Exception as e:
            print 'Error: ', str(e)


def post_delete_audiofile(sender, **kwargs):
    f = kwargs['instance']
    try:
        audio_store.delete(f.file.path)  # delete audio
    except:
        pass
    try:
        audio_store.delete(f.spectrogram.path)  # delete spectrogram image
    except:
        pass


models.signals.post_save.connect(post_save_audiofile, sender=AudioFile)
models.signals.post_delete.connect(post_delete_audiofile, sender=AudioFile)


class Entry(BaseModel):
    user = models.ForeignKey(User)                                                    # user
    audiofile = models.OneToOneField(AudioFile, unique=True, verbose_name=_('AudioFile'),
                                     related_name=_('Entry'))    # audio file
    location = models.PointField(srid=4326)  # location coordinates
    recorded = models.DateTimeField()  # date and time when the audio was recorded
    objects = models.GeoManager()

    # meta
    class Meta(BaseModel.Meta):
        app_label = 'tracks'
        verbose_name = _('entry')
        verbose_name_plural = _('entries')
        ordering = ('-created', )

    def __unicode__(self):
        return self.audiofile.file.url

    def spectrogram_img(self):
        return self.audiofile.spectrogram_img()

    spectrogram_img.allow_tags = True
