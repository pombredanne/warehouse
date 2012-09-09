import base64
import datetime

import redis

from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponsePermanentRedirect, Http404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from django.contrib.auth import authenticate

from warehouse.conf import settings
from warehouse.models import Project
from warehouse.models.packaging import _normalize_regex


class ProjectIndex(ListView):

    restricted = False
    queryset = Project.objects.all().order_by("name")
    template_name = "api/simple/index.html"

    def get_context_data(self, **kwargs):
        ctx = super(ProjectIndex, self).get_context_data(**kwargs)

        ctx.update({
            "restricted": self.restricted,
        })

        return ctx


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


@csrf_exempt
@require_http_methods(["HEAD", "GET", "POST"])
def last_modified(request):
    if settings.WAREHOUSE_ALWAYS_MODIFIED_NOW:
        return HttpResponse(datetime.datetime.utcnow().isoformat(), content_type="text/plain")

    datastore = redis.StrictRedis(**dict([(k.lower(), v) for k, v in settings.REDIS.items()]))

    if request.method in ["POST"]:
        if not request.META.get("HTTP_AUTHORIZATION"):
            return HttpResponse("Unauthorized", status=401)

        try:
            (auth_type, data) = request.META['HTTP_AUTHORIZATION'].split()
            if auth_type.lower() != 'basic':
                return HttpResponse("Unauthorized", status=401)
            user_pass = base64.b64decode(data)
        except Exception:
            return HttpResponse("Unauthorized", status=401)

        bits = user_pass.split(':', 1)

        if len(bits) != 2:
            return HttpResponse("Unauthorized", status=401)

        request.user = authenticate(username=bits[0], password=bits[1])

        if request.user is None or not request.user.is_active:
            return HttpResponse("Unauthorized", status=401)

        if request.user.is_authenticated() and request.user.has_perm("warehouse.set_last_modified"):
            if request.POST.get("date"):
                datastore.set("warehouse:api:simple:last_modified", request.POST["date"])
                return HttpResponse("", status=204)
            return HttpResponseBadRequest("No date supplied")
        else:
            return HttpResponse("Unauthorized", status=401)
    else:
        modified = datastore.get("warehouse:api:simple:last_modified")

        if modified:
            return HttpResponse(modified, content_type="text/plain")

        raise Http404("API has not been synchronized")
