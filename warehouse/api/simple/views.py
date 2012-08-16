from django.views.generic.list import ListView

from warehouse.models import Project


class ProjectIndex(ListView):

    restricted = False
    queryset = Project.objects.all().order_by("name")
    template_name = "api/simple/index.html"
