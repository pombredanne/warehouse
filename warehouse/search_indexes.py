from django.db.models import signals

from haystack import indexes

from warehouse.models import Project, Version, VersionFile


class ProjectRealTimeSearchIndex(indexes.RealTimeSearchIndex):

    def _setup_save(self):
        signals.post_save.connect(self.update_object, sender=self.get_model())
        signals.post_save.connect(self.update_version, sender=Version)
        signals.post_save.connect(self.update_versionfile, sender=VersionFile)

    def _setup_delete(self):
        signals.post_delete.connect(self.remove_object, sender=self.get_model())
        # Deleting a Version or VersionFile should just update the Project index
        signals.post_save.connect(self.update_version, sender=Version)
        signals.post_save.connect(self.update_versionfile, sender=VersionFile)

    def _teardown_save(self):
        signals.post_save.disconnect(self.update_object, sender=self.get_model())
        signals.post_save.disconnect(self.update_version, sender=Version)
        signals.post_save.disconnect(self.update_versionfile, sender=VersionFile)

    def _teardown_delete(self):
        signals.post_delete.disconnect(self.remove_object, sender=self.get_model())
        signals.post_save.disconnect(self.update_version, sender=Version)
        signals.post_save.disconnect(self.update_versionfile, sender=VersionFile)

    def update_version(self, instance, using=None, **kwargs):
        return self.update_object(instance.project, using=using, **kwargs)

    def update_versionfile(self, instance, using=None, **kwargs):
        return self.update_object(instance.version.project, using=using, **kwargs)

    # @@@ Move this into Haystack proper?
    def update_object(self, instance, using=None, **kwargs):
        # Check to make sure we want to index this first.
        if self.should_update(instance, **kwargs):
            self._get_backend(using).update(self, [instance], commit=False)


class ProjectIndex(ProjectRealTimeSearchIndex, indexes.Indexable):

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
