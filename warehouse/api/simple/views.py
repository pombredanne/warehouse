from django.views.generic.list import ListView

from warehouse.models import Project


class ProjectIndex(ListView):

    restricted = False
    queryset = Project.objects.all().order_by("name")
    template_name = "api/simple/index.html"

    #@method_decorator(cache_page(60 * 15))
    def dispatch(self, *args, **kwargs):
        return super(ProjectIndex, self).dispatch(*args, **kwargs)
