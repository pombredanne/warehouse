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
