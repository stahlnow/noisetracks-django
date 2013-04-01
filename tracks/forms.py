from django import forms


class VoteForm(forms.Form):
    uuid = forms.CharField()
    vote = forms.IntegerField()


class UploadForm(forms.Form):
    wavfile = forms.FileField()

