from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from xml.etree import ElementTree

import html5lib
import html5lib.treebuilders

from sqlalchemy.dialects import postgresql as pg
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm.exc import NoResultFound

from warehouse import db
from warehouse.database.mixins import UUIDPrimaryKeyMixin
from warehouse.database.utils import table_args


class ProjectLink(UUIDPrimaryKeyMixin, db.Model):

    __tablename__ = "project_links"
    __table_args__ = declared_attr(table_args((
        db.Index("project_link_idx", "project_id", "link", unique=True),
    )))

    project_id = db.Column(pg.UUID(as_uuid=True),
                    db.ForeignKey("projects.id", ondelete="CASCADE"),
                    nullable=False
                )
    link = db.Column(db.UnicodeText, nullable=False)

    @classmethod
    def extract(cls, project, html):
        parser = html5lib.HTMLParser(
            tree=html5lib.treebuilders.getTreeBuilder("etree", ElementTree),
            namespaceHTMLElements=False,
        )
        parsed = parser.parse(html)
        for anchor in parsed.iter("a"):
            if "href" in anchor.attrib:
                href = anchor.attrib["href"]

                try:
                    link = cls.query.filter_by(
                                project=project,
                                link=href,
                            ).one()
                except NoResultFound:
                    link = cls(project=project, link=href)

                db.session.add(link)
