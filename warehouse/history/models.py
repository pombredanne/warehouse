import calendar

from sqlalchemy.orm.exc import NoResultFound

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
    def upsert(cls, **kwargs):
        try:
            obj = cls.query.filter_by(**kwargs).one()
        except NoResultFound:
            obj = cls(**kwargs)

        db.session.add(obj)

        return obj
