from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import EMPTY_VALUES
from django.utils import importlib


__all__ = ["BaseForm", "RelatedResourceField"]


class RelatedResourceField(forms.Field):

    def __init__(self, resource, *args, **kwargs):
        self.resource = resource

        super(RelatedResourceField, self).__init__(*args, **kwargs)

    def to_class(self):
        # We need to be lazy here, because when the metaclass constructs the
        # Resources, other classes may not exist yet.
        # That said, memoize this so we never have to relookup/reimport.
        if hasattr(self, "_to_class"):
            return self._to_class

        if not isinstance(self.resource, basestring):
            self._to_class = self.to
            return self._to_class

        # It's a string. Let's figure it out.
        if "." in self.resource:
            # Try to import.
            module_bits = self.resource.split(".")
            module_path, class_name = ".".join(module_bits[:-1]), module_bits[-1]
            module = importlib.import_module(module_path)
        else:
            # We've got a bare class name here, which won't work (No AppCache
            # to rely on). Try to throw a useful error.
            raise ImportError("Tastypie requires a Python-style path (<module.module.Class>) to lazy load related resources. Only given '%s'." % self.resource)

        self._to_class = getattr(module, class_name, None)

        if self._to_class is None:
            raise ImportError("Module '%s' does not appear to have a class called '%s'." % (module_path, class_name))

        return self._to_class

    def resource_from_uri(self, fk_resource, uri, request=None, related_obj=None, related_name=None):
        """
        Given a URI is provided, the related resource is attempted to be
        loaded based on the identifiers in the URI.
        """
        try:
            obj = fk_resource.get_via_uri(uri, request=request)
            bundle = fk_resource.build_bundle(obj=obj, request=request)
            return fk_resource.full_dehydrate(bundle).obj
        except ObjectDoesNotExist:
            raise forms.ValidationError(self.error_messages["invalid_choice"])

    def to_python(self, value):
        if value in EMPTY_VALUES:
            return None

        return self.resource_from_uri(self.to_class()(), value)


class BaseForm(forms.Form):

    def __init__(self, user=None, *args, **kwargs):
        self.user = user

        super(BaseForm, self).__init__(*args, **kwargs)
