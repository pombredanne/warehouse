import base64

from django.core.files.uploadedfile import SimpleUploadedFile

from tastypie.fields import FileField
from tastypie.fields import ToManyField, ToOneField


__all__ = ["ConditionalToMany", "ConditionalToOne"]


class ConditionalRelated(ToManyField):
    truthy = set(["yes", "on", "true", "t", "1"])

    def dehydrate_related(self, bundle, related_resource):
        full = bundle.request.GET.get("full", "").lower()
        if full not in self.truthy:
            return related_resource.get_resource_uri(bundle)
        else:
            bundle = related_resource.build_bundle(obj=related_resource.instance, request=bundle.request)
            return related_resource.full_dehydrate(bundle)


class ConditionalToMany(ConditionalRelated, ToManyField):
    pass


class ConditionalToOne(ConditionalRelated, ToOneField):
    pass


class Base64FileField(FileField):
    """
    A django-tastypie field for handling file-uploads through raw post data.
    It uses base64 for en-/decoding the contents of the file.

    Usage:

        class MyResource(ModelResource):
            file_field = Base64FileField("file_field")

            class Meta:
                queryset = ModelWithFileField.objects.all()

    In the case of multipart for submission, it would also pass the filename.
    By using a raw post data stream, we have to pass the filename within our
    file_field structure:

        file_field = {"name": "myfile.png", "file": "longbas64encodedstring"}
    """

    def hydrate(self, obj):
        value = super(Base64FileField, self).hydrate(obj)
        if value:
            value = SimpleUploadedFile(value["name"], base64.b64decode(value["file"]))
            return value
        return None
