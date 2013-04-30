from django.contrib.gis import admin
from tracks.models import AudioFile, Entry


class BaseAdmin(admin.ModelAdmin):
    fieldsets = [
        ('UUID', {'fields': ['uuid']}),
        ('Created', {'fields': ['created']}),
        ('Updated', {'fields': ['updated']}),
    ]


class EntryInline(admin.TabularInline):
    model = Entry
    readonly_fields = ('location', 'recorded', 'uuid', 'user',)


class EntryAdmin(BaseAdmin, admin.OSMGeoAdmin):
    readonly_fields = ('created', 'updated', 'uuid')
    fieldsets = BaseAdmin.fieldsets + [
        (None, {'fields': ['user']}),
        (None, {'fields': ['audiofile']}),
        ('Location', {'fields': ['location']}),
        ('Recorded', {'fields': ['recorded']}),
    ]
    list_display = ('__unicode__', 'created', 'user', 'spectrogram_img')


class AudioFileAdmin(BaseAdmin):
    readonly_fields = ('created', 'updated', 'uuid', 'spectrogram')
    fieldsets = BaseAdmin.fieldsets + [
        ('File Path', {'fields': ['file']}),
        ('Spectrogram Path', {'fields': ['spectrogram']}),
        ('Status', {'fields': ['status']}),
        ]
    list_display = ('__unicode__', 'spectrogram_img')
    inlines = [EntryInline]

admin.site.register(Entry, EntryAdmin)
admin.site.register(AudioFile, AudioFileAdmin)


