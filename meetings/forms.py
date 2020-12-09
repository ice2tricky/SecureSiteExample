from datetime import date

from django.forms import ModelForm, DateInput, TimeInput, TextInput, IntegerField
from django.core.exceptions import ValidationError

from .models import Meeting


class MeetingForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super(MeetingForm, self).__init__(*args, **kwargs)
        # remove username
        self.fields.pop('user')

    class Meta:
        model = Meeting
        fields = '__all__'
        widgets = {
            'date': DateInput(attrs={"type": "date"}),
            'start': TimeInput(attrs={"type": "time"}),
            'duration': TextInput(attrs={"type": "number", "min": "1", "max": "4"})
        }

    def clean_date(self):
        d = self.cleaned_data.get("date")
        if d < date.today():
            raise ValidationError("Meeting cannot be in the past")
        return d
