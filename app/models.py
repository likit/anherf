from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
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
    affiliation = Column('affil', String(), nullable=True)
    mobile = Column('mobile', String(), nullable=True)
    delivery_address = Column('delivery_address', String(), nullable=True)
    position_type = Column('position_type', String(), nullable=True)
    registers = relationship('Registration', backref="participant")
    role_id = Column('role_id', Integer(), ForeignKey('roles.id'))
    role = relationship('Role', backref='participants')


class Registration(db.Model):
    __tablename__ = 'registrations'
    id = Column('id', Integer, primary_key=True, autoincrement=True)
    registered_at = Column('registered_at', DateTime())
    participant_id = Column('participant_id', ForeignKey('participants.id'))
    checked_at = Column('checked_at', DateTime())
    payment_required = Column('payment_required', Boolean(), default=False)
    pay_status = Column('pay_status', Boolean(), default=False)


class Role(db.Model):
    __tablename__ = 'roles'
    id = Column('id', Integer, primary_key=True, autoincrement=True)
    desc = Column('desc', String())


