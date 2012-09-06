from haystack import indexes

from warehouse.models import Project


class ProjectIndex(indexes.RealTimeSearchIndex, indexes.Indexable):

    text = indexes.CharField(document=True, use_template=True)

    name = indexes.CharField(model_attr="name", boost=1.5)
    normalized = indexes.CharField(model_attr="normalized")

    summary = indexes.CharField(indexed=False, default="")
    description = indexes.CharField(indexed=False, default="")

    def get_model(self):
        return Project

    def prepare(self, obj):
        data = super(ProjectIndex, self).prepare(obj)

        if obj.latest:
            data["summary"] = obj.latest.summary
            data["description"] = obj.latest.description

        return data
