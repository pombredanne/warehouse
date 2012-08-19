import os

from distutils2 import version as verlib
from distutils2 import markers

from django import forms
from django.db.models import Q

from warehouse.api.v1.forms.base import BaseForm, RelatedResourceField
from warehouse.api.validation import ERROR_MESSAGES
from warehouse.conf import settings
from warehouse.models import Project, Version, VersionFile
from warehouse.models.packaging import _normalize_regex


__all__ = ["ProjectForm"]


class ProjectForm(BaseForm):
    name = forms.CharField(max_length=150, error_messages=ERROR_MESSAGES)

    class Meta:
        model = Project
        fields = ["name"]

    def clean_name(self):
        data = self.cleaned_data["name"]

        if self.instance:
            if self.instance.name != data:
                raise forms.ValidationError("invalid")
        else:
            if Project.objects.filter(Q(name=data) | Q(normalized__iexact=_normalize_regex.sub("-", data).lower())).exists():
                raise forms.ValidationError("already_exists")

        return data


class VersionForm(BaseForm):
    project = RelatedResourceField("warehouse.api.v1.resources.packaging.ProjectResource", error_messages=ERROR_MESSAGES)
    version = forms.CharField(error_messages=ERROR_MESSAGES)
    uris = forms.Field(error_messages=ERROR_MESSAGES, required=False)
    author = forms.Field(error_messages=ERROR_MESSAGES, required=False)
    maintainer = forms.Field(error_messages=ERROR_MESSAGES, required=False)

    requires = forms.Field(required=False)
    obsoletes = forms.Field(required=False)
    provides = forms.Field(required=False)

    class Meta:
        model = Version
        fields = ["project", "version", "uris", "author", "maintainer", "requires", "obsoletes", "provides"]

    def clean_version(self):
        data = self.cleaned_data["version"]

        suggested = verlib.suggest_normalized_version(data)

        if suggested is None or suggested != data:
            if not self.user.username in settings.WAREHOUSE_SYNC_USERS:
                raise forms.ValidationError("invalid")

        return data

    def clean_uris(self):
        uris = self.cleaned_data["uris"]

        for key, value in uris.iteritems():
            if not key or not value:
                forms.ValidationError("invalid")

            if len(key) > 32:
                forms.ValidationError("invalid")

            f = forms.URLField(error_messages=ERROR_MESSAGES)
            f.to_python(value)
            f.validate(value)
            f.run_validators(value)

        return uris

    def clean_author(self):
        author = self.cleaned_data["author"]

        if set(author) - set(["name", "email"]):
            forms.ValidationError("invalid")

        return author

    def clean_maintainer(self):
        maintainer = self.cleaned_data["maintainer"]

        if set(maintainer) - set(["name", "email"]):
            forms.ValidationError("invalid")

        return maintainer

    def clean_requires(self):
        requires = self.cleaned_data["requires"]

        if requires is None:
            return

        for require in requires:
            form = RequireForm(data=require)

            if not form.is_valid():
                raise forms.ValidationError("invalid")

        return requires

    def clean_obsoletes(self):
        obsoletes = self.cleaned_data["obsoletes"]

        if obsoletes is None:
            return

        for obsolete in obsoletes:
            form = RequireForm(data=obsolete)

            if not form.is_valid():
                raise forms.ValidationError("invalid")

        return obsoletes

    def clean_provides(self):
        provides = self.cleaned_data["provides"]

        if provides is None:
            return

        for provide in provides:
            form = RequireForm(data=provide)

            if not form.is_valid():
                raise forms.ValidationError("invalid")

        return provides

    def clean(self):
        cleaned_data = super(VersionForm, self).clean()

        if self.instance:
            if self.instance.project != cleaned_data.get("project"):
                raise forms.ValidationError("invalid")
            if self.instance.version != cleaned_data.get("version"):
                raise forms.ValidationError("invalid")
        else:
            if Version.objects.filter(project=cleaned_data.get("project"), version=cleaned_data.get("version")).exists():
                raise forms.ValidationError("already_exists")

        return cleaned_data


class RequireForm(forms.Form):
    name = forms.CharField(max_length=150, error_messages=ERROR_MESSAGES)
    version = forms.CharField(error_messages=ERROR_MESSAGES, required=False)
    environment = forms.CharField(error_messages=ERROR_MESSAGES, required=False)

    def clean_version(self):
        data = self.cleaned_data["version"]

        if data:
            suggested = verlib.suggest_normalized_version(data)

            if suggested is None or suggested != data:
                raise forms.ValidationError("invalid")

        return data

    def clean_environment(self):
        environment = self.cleaned_data["environment"]

        if environment:
            try:
                markers.interpret(environment)
            except Exception:
                raise forms.ValidationError("invalid")

        return environment


class VersionFileForm(BaseForm):

    class Meta:
        model = VersionFile
        fields = ["type", "python_version", "comment", "file"]

    def clean_file(self):
        f = self.cleaned_data["file"]

        filename = os.path.basename(f.file.name)

        print "1", self.instance, "2", filename, "3", self.instance.filename
        print "4", bool(self.instance)
        print "5", f
        print "6", f.file
        print "7", f.file.name
        print "8", type(self.instance)
        print "9", dir(self.instance)
        print "10", self.instance.pk

        if self.instance:
            if self.instance.filename != filename:
                raise forms.ValidationError("invalid")
        else:
            if VersionFile.objects.filter(filename=filename).exists():
                raise forms.ValidationError("already_exists")

        return f
