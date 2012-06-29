import datetime
import uuid

from sqlalchemy.dialects import postgresql

from warehouse.core import db


__all__ = ["Project"]


class Project(db.Model):
    id = db.Column(postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    created = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.datetime.now)
    # modified

    name = db.Column(db.Unicode(150), unique=True, nullable=False)

    # This mostly exists for sake of the Simple and Simple-Restricted API
    # uris

    # De-normalization
    normalized = db.Column(db.Unicode(150), unique=True, nullable=False)
