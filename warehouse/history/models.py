import calendar

from warehouse import db
from warehouse.database.mixins import UUIDPrimaryKeyMixin, TimeStampedMixin


class Journal(UUIDPrimaryKeyMixin, TimeStampedMixin, db.Model):

    __tablename__ = "journals"

    name = db.Column(db.Unicode, nullable=False)
    version = db.Column(db.Unicode)
    action = db.Column(db.Unicode, nullable=False)
    pypi_id = db.Column(db.Integer, nullable=False, unique=True)

    @property
    def timestamp(self):
        return calendar.timegm(self.created.timetuple())

    @classmethod
    def create(cls, **kwargs):
        obj = cls(**kwargs)
        db.session.add(obj)
        return obj
