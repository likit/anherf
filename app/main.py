# -*- coding: utf-8 -*-

import os
import datetime
import uuid

import gspread
import arrow
import click
import time
import pandas as pd
from sys import stderr
# import barcode
import pytz
import requests
# from barcode.writer import ImageWriter
from flask import (Flask, jsonify, render_template,
                   send_file, request, url_for, redirect, flash, make_response)
from flask_mail import Message, Mail
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_admin import Admin
from flask_wtf import FlaskForm
from sqlalchemy import or_, func
from wtforms import StringField, SubmitField, SelectField, BooleanField
from dotenv import load_dotenv

load_dotenv()

bangkok = pytz.timezone('Asia/Bangkok')
YEAR = arrow.now(tz=bangkok).date()
SENDER = 'likit.pre@mahidol.edu'

mail = Mail()
admin = Admin()

basedir = os.path.dirname(os.path.abspath(__file__))
qrimage_dir = os.path.join(basedir, 'static/barcodes')

app = Flask(__name__, static_url_path='/static')
# app.config['MAIL_DEBUG'] = True
# app.config['MAIL_SERVER'] = 'smtp.gmail.com'
# app.config['MAIL_USERNAME'] = SENDER
# app.config['MAIL_USE_TLS'] = True
# app.config['MAIL_PORT'] = 587
# app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL').replace('://', 'ql://', 1)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
mail.init_app(app)
admin.init_app(app)

db = SQLAlchemy(app)
migrate = Migrate(app, db, directory='app/migrations')

from .models import *

from flask_admin.contrib.sqla import ModelView

admin.add_view(ModelView(Participant, db.session))
admin.add_view(ModelView(Registration, db.session))
admin.add_view(ModelView(CheckIn, db.session))
admin.add_view(ModelView(Role, db.session))

credentials = requests.get(os.environ.get('GOOGLE_JSON_KEYFILE')).json()
gc = gspread.service_account_from_dict(credentials)


def timezoned(value):
    return value.astimezone(bangkok).strftime('%d %b %Y, %H:%M:%S')


app.jinja_env.filters['timezoned'] = timezoned


class ParticipantForm(FlaskForm):
    email = StringField('Email')
    title = StringField('Title')
    firstname = StringField('First name')
    lastname = StringField('Last name')
    role = SelectField('Role', default="6")
    affiliation = StringField('Affiliation/Institute/University')
    faculty = StringField('Faculty/Department')
    mobile = StringField('Mobile')
    address = StringField('Address')
    payment_required = BooleanField()
    pay_status = BooleanField('Paid')
    submit = SubmitField('Submit')


@app.route('/api/register/list')
def get_list_api():
    participants = Participant.query.all()[:30]
    return jsonify(participants)


@app.route('/participant/add', methods=['GET', 'POST'])
def add_participant():
    form = ParticipantForm()
    roles = [(str(role.id), role.desc) for role in Role.query.all()]
    form.role.choices = roles
    if form.validate_on_submit():
        title = form.title.data
        firstname = form.firstname.data
        lastname = form.lastname.data
        email = form.email.data.lower()
        mobile = form.mobile.data
        faculty = form.faculty.data
        affiliation = form.affiliation.data
        address = form.address.data
        role = Role.query.filter_by(id=int(form.role.data)).first()
        pay_status = True if 'pay_status' in request.form else False
        payment_required = True if 'payment_required' in request.form else False
        print(request.form)
        registration = Registration(registered_at=datetime.datetime.utcnow(),
                                    payment_required=payment_required,
                                    pay_status=pay_status)
        participant = Participant(title=title, firstname=firstname, lastname=lastname,
                                  email=email, faculty=faculty, affiliation=affiliation,
                                  delivery_address=address, role=role, mobile=mobile)
        registration.participant = participant
        db.session.add(participant)
        db.session.add(registration)
        db.session.commit()
        return render_template('new_participant_added.html', participant=participant,
                               registration=registration)
    print(form.errors)
    return render_template('new_participant.html', form=form)


@app.route('/register/registrants')
def list_registrants():
    participants = Participant.query.all()
    return render_template('list.html', plist=participants, year=YEAR)


@app.route('/register/registrants/reload')
def reload_registrants():
    sheet = gc.open_by_key(os.environ.get('GOOGLE_SHEET_ID'))
    worksheet = sheet.worksheet('Form Responses 1')
    new_registrants = 0
    for rec in worksheet.get_all_records():
        registrant = Participant.query.filter_by(firstname=rec['4. ชื่อ'], lastname=rec['6. นามสกุล\n']).first()
        if not registrant:
            new_registrant = Participant(firstname=rec['4. ชื่อ'],
                                         lastname=rec['6. นามสกุล\n'],
                                         title=rec['1. คำนำหน้านาม'],
                                         email=rec['11. E-mail '],
                                         mobile=rec['12. โทรศัพท์สำนักงาน '],
                                         faculty=rec['13. หน่วยงานต้นสังกัด / สถาบันการศึกษา / โรงพยาบาล'],
                                         profession=rec['8. วิชาชีพสุขภาพ'],
                                         )
            new_registration = Registration(regcode=str(uuid.uuid4())[:8],
                                            registered_at=rec['Timestamp'])
            db.session.add(new_registration)
            db.session.commit()
            new_registration.generate_regcode()
            new_registrant.registers.append(new_registration)
            db.session.add(new_registrant)
            db.session.commit()
            new_registrants += 1
    flash(f'{new_registrants} new registrants added.', 'success')
    resp = make_response()
    resp.headers['HX-Refresh'] = 'true'
    return resp


@app.route('/registrants/name-search', methods=['POST'])
def search_registrant_name():
    name = request.form.get('name')
    template = '<table class="table is-fullwidth">' \
               '<thead>' \
               '<th>Firstname</th>' \
               '<th>Lastname</th>' \
               '<th>Email</th>' \
               '<th>Phone</th>' \
               '<th>Affiliation</th>' \
               '<th>Last Seen</th>' \
               '<th></th>' \
               '</thead>' \
               '<tbody>'
    if name:
        for p in Participant.query.filter(or_(Participant.firstname.ilike(f'%{name}%'),
                                                (Participant.lastname.ilike(f'%{name}%')))):
            template += '<tr>' \
                        '<td>{}</td>' \
                        '<td>{}</td>' \
                        '<td>{}</td>' \
                        '<td>{}</td>' \
                        '<td>{}</td>' \
                        '<td>{}</td>' \
                        '<td><a class="button is-outlined is-info" hx-post="{}" hx-target="#registrant-table" ' \
                        'hx-swap="innerHTML">Check In</a></td>' \
                        '</tr>'.format(p.firstname,
                                       p.lastname,
                                       p.email,
                                       p.mobile,
                                       p.faculty,
                                       p.last_checkin.checked_at.astimezone(bangkok).strftime('%d/%m/%Y %H:%M:%S') if p.last_checkin else '',
                                       url_for('check_in_registrant', participant_id=p.id))
    template += '</tbody></table>'
    resp = make_response(template)
    return resp


@app.route('/register/registrants/<int:participant_id>', methods=['POST'])
def check_in_registrant(participant_id):
    # register = Registration.query.filter_by(regcode=regcode)
    template = ''
    regis = Registration.query.filter_by(participant_id=participant_id).first()
    if regis:
        if regis.payment_required and not regis.pay_status:
            resp = make_response()
            resp.headers['HX-Refresh'] = 'true'
            flash('Payment is required.', 'danger')
            return resp
        checkin = CheckIn.query.filter_by(registration=regis).filter(func.DATE(func.timezone('Asia/Bangkok', CheckIn.checked_at)) == arrow.now('Asia/Bangkok').date()).first()
        if checkin:
            template = '<table class="table is-bordered is-fullwidth"><tr><td class="has-text-success">The participant already checked in today at {}.</td></tr></table>'\
                .format(checkin.checked_at.astimezone(bangkok).strftime('%H:%M'))
            resp = make_response(template)
            return resp
        checkin = CheckIn(registration=regis, checked_at=arrow.now('Asia/Bangkok').datetime)
        db.session.add(checkin)
        db.session.commit()
        total_registrants = Registration.query.count()
        total_check_ins = CheckIn.query.filter(func.DATE(func.timezone('Asia/Bangkok', CheckIn.checked_at)) == arrow.now('Asia/Bangkok').date()).count()
        template = f'''
        <table class="table" id="stat" hx-swap-oob="true" hx-swap="outerHTML">
            <tbody>
            <tr>
                <td><strong>Total Registrants</strong></td>
                <td>{ total_registrants }</td>
            </tr>
            <tr>
                <td><strong>Checked In { arrow.now('Asia/Bangkok').date() }</strong></td>
                <td>{ total_check_ins } ({ round(total_check_ins/total_registrants*100.0, 2) }%)</td>
            </tr>
            </tbody>
        </table>
        <div class="column has-text-centered">
            <span class="icon is-large">
                <i class="fas fa-check-circle has-text-success fa-3x"></i>
            </span><br>
            <span class="subtitle">Succeeded!</span>
        </div>
        <table class="table is-fullwidth">
            <thead>
            <th>Code</th>
            <th>Firstname</th>
            <th>Lastname</th>
            <th>Email</th>
            <th>Phone</th>
            <th>Latest Check In</th>
            <th></th>
            </thead>
            <tbody>
                <tr>
                <td>{regis.regcode}</td>
                <td>{regis.participant.firstname}</td>
                <td>{regis.participant.lastname}</td>
                <td>{regis.participant.email}</td>
                <td>{regis.participant.mobile}</td>
                <td>{checkin.checked_at.astimezone(bangkok).strftime('%d/%m/%Y %H:%M:%S')}</td>
                <td>
                    <a class="button is-danger" href="{url_for('cancel_checkin', checkin_id=checkin.id)}">Cancel</a>
                </td>
                </tr>
            </tbody>
        </table>
        '''
    resp = make_response(template)
    return resp


@app.route('/cancel-checkin/<int:checkin_id>')
def cancel_checkin(checkin_id):
    checkin = CheckIn.query.get(checkin_id)
    db.session.delete(checkin)
    db.session.commit()
    flash('Check-in has been cancelled.', 'danger')
    return redirect(url_for('scan'))


@app.route('/')
@app.route('/register/scan')
def scan():
    rid = request.args.get('rid', None)
    status = request.args.get('status', None)
    if rid:
        register = Registration.query.filter_by(id=int(rid)).first()
    else:
        register = None
    total_registrants = Registration.query.count()
    total_check_ins = CheckIn.query.filter(func.DATE(func.timezone('Asia/Bangkok', CheckIn.checked_at)) == datetime.date.today()).count()
    return render_template('barcode.html',
                           register=register,
                           status=status,
                           total_registrants=total_registrants,
                           total_check_ins=total_check_ins,
                           today=datetime.date.today()
                           )


@app.route('/register/mail')
def send_mail(rid=None, recp_mail=None):
    if rid is None:
        rid = request.args.get('rid')
        recp_mail = request.args.get('email')

    msg = Message('Welcome to ANHPERF conference.',
                  sender=SENDER,
                  recipients=[recp_mail])

    # if not os.path.exists(os.path.join(qrimage_dir, '{}.png'.format(rid))):
    #     get_barcode(rid)

    with app.open_resource("{}/{}.png".format(qrimage_dir, rid)) as fp:
        msg.attach("{}.png".format(rid), "image/png", fp.read())

    try:
        mail.send(msg)
    except:
        return 'An error has occurred.'
    else:
        return 'The mail has been sent.'


@app.route('/html/message/<int:rid>')
def display_html_message(rid):
    register = Registration.query.get(rid)
    return render_template('message.html', register=register)


@app.cli.command()
@click.argument('rid', required=False)
def send_mail_barcode(rid=None, role=None):
    if rid:
        reg = Registration.query.filter_by(id=rid).first()
        participants = [reg.participant]
    else:
        participants = [p for p in Participant.query.all() if p.email != '']
    '''
    else:
        role = 'invitee'
        participants = []

        for p in Participant.query.all():
            if p.role.desc == role and p.email:
                print(p.id, p.email, p.title, p.firstname, p.lastname, p.registers[-1].id, p.role.desc)
                participants.append(p)
    '''
    errors = []

    with mail.connect() as conn:
        for recp in participants:
            with app.open_resource("templates/message.txt") as template_fp:
                content = template_fp.read().decode('utf-8')

            msg = Message(
                subject='Welcome to the 6th Annual Health National Professional Reform Forum (ANHPERF {})'.format(YEAR),
                sender=SENDER,
                body=content,
                # recipients=['likit.pre@mahidol.edu'],
                recipients=[recp.email],
                cc=['likit.pre@mahidol.edu'])
            rid = recp.registers[-1].id
            with app.open_resource("{}/{}.png".format(qrimage_dir, rid)) as fp:
                msg.attach("{}.png".format(rid), "image/png", fp.read())
                msg.html = render_template('message.html', register=recp.registers[-1])
            try:
                conn.send(msg)
            except:
                errors.append(recp)
            else:
                print('Sent to {}, {}, {}'.format(
                    recp.email, recp.fullname, recp.id))
            time.sleep(2)
    if errors:
        print('==========>Failed to send to the following:')
        for e in errors:
            print(e.email, e.firstname, e.lastname, e.id)


@app.cli.command()
def send_mail_payment_reminder():
    regs = Registration.query.filter_by(payment_required=True,
                                        pay_status=False)
    recp_mails = []
    for r in regs:
        recp_mails.append(r.participant.email)

    with app.open_resource("templates/participant_mail.html") as template_fp:
        content = template_fp.read().decode('utf-8')

    with mail.connect() as conn:
        for recp in recp_mails[1:]:
            msg = Message(
                subject='Registration information for the 5th Annual Health National Professional Reform Forum (ANHPERF {})'.format(
                    YEAR),
                sender=SENDER,
                body=content,
                recipients=[recp],
                cc=['likit.pre@mahidol.edu'])
            try:
                conn.send(msg)
            except Exception:
                print(recp, file=stderr)


@app.route('/paid/<rid>')
def pay(rid=None):
    if not rid:
        return jsonify({'message': 'No account ID specified'})
    register = Registration.query.filter(Registration.id == rid).first()
    # participant can only check in a single time
    if register:
        register.pay_status = True
        db.session.add(register)
        db.session.commit()
    return redirect(request.referrer)


@app.route('/checkin/<rid>')
@app.route('/checkin')
def checkin(rid=None):
    if not rid:
        return jsonify({'message': 'No account ID specified'})
    else:
        if len(rid) == 9:
            trim_id = int(rid[4:])
        else:
            trim_id = rid
        register = Registration.query.filter(Registration.id == trim_id).first()
        if (register.payment_required and register.pay_status) or \
                (not register.payment_required):
            new_checked_date = datetime.datetime.now(pytz.utc)
            checkin = CheckIn(checked_at=new_checked_date)
            checkin.registration = register
            db.session.add(checkin)
            db.session.commit()
            status = 'success'
        else:
            status = 'unpaid'
        return redirect(url_for('scan', rid=register.id, status=status))
    return redirect(url_for('scan'))


# def get_barcode(rid):
#     if not os.path.exists(qrimage_dir):
#         os.mkdir(qrimage_dir)
#
#     EAN = barcode.get_barcode_class('code128')
#     ean = EAN(u'{}{:05}'.format(YEAR, int(rid)), writer=ImageWriter())
#     imgname = ean.save('{}/{}'.format(qrimage_dir, rid))
#     fp = open('{}'.format(imgname), 'wb')
#     ean.write(fp)
#     fp.close()


# from .load_data import load

# @app.cli.command()
# @click.argument('inputfile')
# def load_data(inputfile):
#     load(inputfile)


# @app.cli.command()
# @click.argument('id', required=False)
# def gen_barcode(id=None):
#     if id is None:
#         for reg in Registration.query.all():
#             get_barcode(reg.id)
#             print('Barcode for {} has been generated...'.format(reg.id))
#     else:
#         get_barcode(id)


if __name__ == '__main__':
    app.run()
