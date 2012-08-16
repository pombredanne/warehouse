from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpResponsePermanentRedirect, Http404
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from warehouse.models import Project
from warehouse.models.packaging import _normalize_regex


class ProjectIndex(ListView):

    restricted = False
    queryset = Project.objects.all().order_by("name")
    template_name = "api/simple/index.html"


class ProjectDetail(DetailView):

    restricted = False
    queryset = Project.objects.all()
    template_name = "api/simple/detail.html"

    def get_object(self, queryset=None):
        # Use a custom queryset if provided; this is required for subclasses
        # like DateDetailView
        if queryset is None:
            queryset = self.get_queryset()

        slug = self.kwargs.get(self.slug_url_kwarg, None)

        if slug is not None:
            queryset = queryset.filter(Q(name__iexact=slug) | Q(normalized=_normalize_regex.sub("-", slug).lower()))
        else:
            # If there is no slug it is an error
            raise AttributeError(u"Generic detail view %s must be called with "
                                 u"either an object pk or a slug."
                                 % self.__class__.__name__)

        try:
            obj = queryset.get()
        except queryset.model.DoesNotExist:
            raise Http404()

        return obj

    def get_context_data(self, **kwargs):
        ctx = super(ProjectDetail, self).get_context_data(**kwargs)

        versions = self.object.versions.all()

        if self.kwargs.get("version"):
            versions = versions.filter(version=self.kwargs["version"])
        else:
            versions = versions.filter(yanked=False).order_by("-order")

        ctx.update({
            "versions": versions,
            "restricted": self.restricted,
            "show_hidden": True if self.kwargs.get("version") else False,
        })

        return ctx

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        # Check that the case matches what it's supposed to be
        if self.object.name != self.kwargs.get(self.slug_url_kwarg, None):
            return HttpResponsePermanentRedirect(reverse("api_simple_detail", kwargs={"slug": self.object.name}))

        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)
