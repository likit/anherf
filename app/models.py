import arrow
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Date
from sqlalchemy.orm import relationship, backref
from .main import db


class Participant(db.Model):
    __tablename__ = 'participants'
    id = Column('id', Integer, primary_key=True, autoincrement=True)
    old_id = Column('old_id', Integer)
    title = Column('title', String(), nullable=True)
    firstname = Column('firstname', String(), nullable=False)
    lastname = Column('lastname', String(), nullable=False)
    email = Column('email', String(), nullable=False)
    faculty = Column('faculty', String(), nullable=True)
    department = Column('department', String())
    officephone = Column('officephone', String())
    fax = Column('fax', String())
    affiliation = Column('affil', String(), nullable=True)
    mobile = Column('mobile', String(), nullable=True)
    delivery_address = Column('delivery_address', String(), nullable=True)
    position_type = Column('position_type', String(), nullable=True)
    profession = Column('profession', String(), nullable=True)
    role_id = Column('role_id', Integer(), ForeignKey('roles.id'))
    role = relationship('Role', backref='participants')
    attend_as = Column('attend_as', String())

    @property
    def fullname(self):
        return u'{}{} {}'.format(self.title, self.firstname, self.lastname)

    def to_dict(self):
        return {'firstname': self.firstname,
                'lastname': self.lastname,
                'email': self.email,
                'mobile': self.mobile,
                'faculty': self.faculty,
                'title': self.title,
                'code': self.regcode
                }


class Registration(db.Model):
    __tablename__ = 'registrations'
    id = Column('id', Integer, primary_key=True, autoincrement=True)
    regcode = Column('regcode', String(16), unique=True)
    registered_at = Column('registered_at', DateTime(timezone=True))
    participant_id = Column('participant_id', ForeignKey('participants.id'))
    participant = db.relationship('Participant', backref=backref('registers'))
    payment_required = Column('payment_required', Boolean(), default=False)
    badge = Column('badge', String(32))
    pay_status = Column('pay_status', Boolean(), default=False)
    paid_on = Column('paid_on', Date(), nullable=True)

    def generate_regcode(self):
        self.regcode = '{}{:05}'.format(arrow.now().year, self.id)


class CheckIn(db.Model):
    __tablename__ = 'checkins'
    id = Column('id', Integer, primary_key=True, autoincrement=True)
    checked_at = Column('checked_at', DateTime(timezone=True))
    reg_id = Column('reg_id', db.ForeignKey('registrations.id'))
    registration = relationship('Registration', backref='checkins')

    def __repr__(self):
        return self.checked_at.strftime('%d-%m-%Y %H:%M:%S')


class Role(db.Model):
    __tablename__ = 'roles'
    id = Column('id', Integer, primary_key=True, autoincrement=True)
    desc = Column('desc', String())

    def __repr__(self):
        return self.desc.title()
