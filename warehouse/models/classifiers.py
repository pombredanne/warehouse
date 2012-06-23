from django.db import models


__all__ = ["Classifier"]


# @@@ These are by Nature Hierarchical. Would we benefit from a tree structure?
class Classifier(models.Model):
    trove = models.CharField(max_length=350, unique=True)

    class Meta:
        app_label = "warehouse"

    def __unicode__(self):
        return self.trove
