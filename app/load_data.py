from datetime import datetime
from pandas import read_excel
from .models import Participant, Registration
from .main import db

def load(inputfile):
    df = read_excel(inputfile)

    for ix, row in df[['ID', 'user_email', 'user_registered', 'first_name',
                'last_name', 'delivery_address', 'mobile', 'name_title',
                'faculty', 'university', 'original_affiliation_institute']].iterrows():
        participant = Participant(
            id=int(row['ID']),
            title=row['name_title'],
            firstname=row['first_name'],
            lastname=row['last_name'],
            delivery_address=row['delivery_address'],
            mobile=row['mobile'],
            email=row['user_email'],
            faculty=row['faculty'],
            affiliation=row['original_affiliation_institute'],
        )
        db.session.add(participant)
        reg = Registration(
            registered_at=datetime.strptime(row['user_registered'], '%Y-%m-%d %H:%M:%S'),
            checked_at=None,
        )
        db.session.add(reg)
        participant.registers.append(reg)
        db.session.commit()
