from haystack import indexes

from warehouse.models import Project


class ProjectIndex(indexes.RealTimeSearchIndex, indexes.Indexable):

    text = indexes.CharField(document=True, use_template=True)

    def get_model(self):
        return Project
