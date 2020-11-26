from . import db

class Access(db.Model):
    """ Data model. """

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    metric = db.Column(
        db.String(64),
        index=False,
        nullable=False
    )
    aggregation_level = db.Column(
        db.String(64),
        index=True,
        nullable=False
    )
    monitor = db.Column(
        db.String(64),
        index=False,
        unique=False,
        nullable=False
    )

    def __repr__(self):
        return '<Access {}>'.format(self.id)

