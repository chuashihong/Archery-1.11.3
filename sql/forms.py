# File: common/forms.py (or sql/forms.py)

from django import forms
from .models import RestoreRequest
class BackupSettingsForm(forms.Form):
    """Form for configuring backup settings."""
    backup_frequency = forms.ChoiceField(
        choices=[
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
        ],
        label='Backup Frequency',
        required=True
    )
    backup_time = forms.TimeField(label='Backup Time', required=True)
    backup_destination = forms.CharField(
        max_length=255,
        label='Backup Destination',
        required=True
    )

    def save(self):
        # Logic for saving the backup settings, e.g., to a config file or database
        data = self.cleaned_data
        # Save or update backup settings logic here
        # For example, save to a model, or write to a settings file

class RestoreRequestForm(forms.ModelForm):
    class Meta:
        model = RestoreRequest
        fields = ['instance', 'restore_time', 'db_name', 'table_name', 'unzip_password']
        widgets = {
            'restore_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }