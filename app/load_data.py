from datetime import datetime
from pandas import read_excel
from .models import Participant, Registration, Role
from .main import db

def load(inputfile, sheetname=None):
    df = read_excel(inputfile)
    # deal with participants with no email addresses.
    df = df.fillna('')

    for ix, row in df[['user_email', 'Timestamp', 'firstname',
                       'lastname', 'delivery_address', 'mobile', 'name_title',
                       'faculty', 'original_affiliation_institute',
                       'department', 'officephone', 'fax', 'profession', 'position',
                       'badge', 'attend_as',
                       ]].iterrows():
        participant = Participant(
            title=row['name_title'],
            firstname=row['firstname'],
            lastname=row['lastname'],
            delivery_address=row['delivery_address'],
            mobile=row['mobile'],
            email=row['user_email'],
            faculty=row['faculty'],
            profession=row['profession'],
            position_type=row['position'],
            affiliation=row['original_affiliation_institute'],
            department=row['department'],
            officephone=row['officephone'],
            attend_as=row['attend_as'],
            fax=row['fax'],
        )
        role = Role.query.filter_by(desc=row['badge'].strip()).first()
        participant.role = role
        db.session.add(participant)
        reg = Registration(
            # registered_at=datetime.strptime(row['Timestamp'], '%Y-%m-%d %H:%M:%S'),
            registered_at=row['Timestamp'],
            badge=row['badge'],
        )
        db.session.add(reg)
        participant.registers.append(reg)
        db.session.commit()
