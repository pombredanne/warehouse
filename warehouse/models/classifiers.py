from uuid import uuid4

from sqlalchemy.dialects import postgresql

from warehouse.core import db


__all__ = ["Classifier"]


# @@@ These are by Nature Hierarchical. Would we benefit from a tree structure?
class Classifier(db.Model):
    id = db.Column(postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4)
    trove = db.Column(db.Unicode(350), unique=True, nullable=False)
