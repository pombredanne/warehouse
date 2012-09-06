from haystack import indexes

from warehouse.models import Project


class ProjectIndex(indexes.RealTimeSearchIndex, indexes.Indexable):

    text = indexes.CharField(document=True, use_template=True)

    name = indexes.CharField(model_attr="name")
    normalized = indexes.CharField(model_attr="normalized")

    def get_model(self):
        return Project
