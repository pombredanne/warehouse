from django import forms
from django.db.models import Q

from warehouse.models import Project
from warehouse.models.packaging import _normalize_regex


__all__ = ["ProjectForm"]


class ProjectForm(forms.Form):
    name = forms.CharField(max_length=150)

    def clean_name(self):
        data = self.cleaned_data["name"]

        if Project.objects.filter(Q(name=data) | Q(normalized__iexact=_normalize_regex.sub("-", data).lower())).exists():
            raise forms.ValidationError("already_exists")

        return data
