from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship, backref
from .main import db

class Participant(db.Model):
    __tablename__ = 'participants'
    id = Column('id', Integer, primary_key=True, autoincrement=False)
    title = Column('title', String())
    firstname = Column('firstname', String())
    lastname = Column('lastname', String())
    email = Column('email', String())
    faculty = Column('faculty', String(), nullable=True)
    affiliation = Column('affil', String())
    mobile = Column('mobile', String())
    delivery_address = Column('delivery_address', String())
    position_type = Column('position_type', String())
    registers = relationship('Registration', backref="participant")


class Registration(db.Model):
    __tablename__ = 'registrations'
    id = Column('id', Integer, primary_key=True, autoincrement=True)
    registered_at = Column('registered_at', DateTime())
    participant_id = Column('participant_id', ForeignKey('participants.id'))
    checked_at = Column('checked_at', DateTime())

