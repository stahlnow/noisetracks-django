from django import forms


class UploadForm(forms.Form):
    wavfile = forms.FileField()

