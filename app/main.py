# -*- coding: utf-8 -*-

import os
import datetime
import click
from sys import stderr
import barcode
import pandas as pd
import numpy as np
import pytz
from barcode.writer import ImageWriter
from flask import (Flask, jsonify, render_template,
                    send_file, request, url_for, redirect)
from flask_mail import Message, Mail
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_admin import Admin
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, BooleanField

bnk = pytz.timezone('Asia/Bangkok')
YEAR = 2019
SENDER = 'likit.pre@mahidol.edu'

mail = Mail()
admin = Admin()

basedir =  os.path.dirname(os.path.abspath(__file__))
qrimage_dir = os.path.join(basedir, 'static/barcodes')

app = Flask(__name__)
app.config['MAIL_DEBUG'] = True
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_USERNAME'] = SENDER
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_PORT'] = 587
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres+psycopg2://postgres@pg/anhperf_dev'
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
mail.init_app(app)
admin.init_app(app)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

from .models import *

from flask_admin.contrib.sqla import ModelView

admin.add_view(ModelView(Participant,db.session))
admin.add_view(ModelView(Registration,db.session))
admin.add_view(ModelView(CheckIn, db.session))
admin.add_view(ModelView(Role, db.session))


def timezoned(value):
    return value.astimezone(pytz.timezone('Asia/Bangkok')).strftime('%d %b %Y, %H:%M:%S')

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

@app.route('/register/list')
def list():
    participants = Participant.query.all()
    return render_template('list.html', plist=participants, year=YEAR)


@app.route('/register/scan')
def scan():
    rid = request.args.get('rid', None)
    status = request.args.get('status', None)
    if rid:
        register = Registration.query.filter_by(id=int(rid)).first()
    else:
        register = None
    return render_template('barcode.html', register=register, status=status)


@app.route('/')
@app.route('/register')
def show_register():
    checkins = CheckIn.query.all()
    all_regs_count = Registration.query.count()
    data = []
    for chk in checkins:
        data.append([
            chk.registration.participant.id,
            chk.registration.participant.role.desc,
            chk.checked_at.date(),
        ])

    df = pd.DataFrame(data, columns=['pid', 'role', 'checkin_date'])
    df = df.drop_duplicates('pid')
    summary = df.groupby('role').checkin_date.count()
    summary = summary.apply(int)
    if checkins:
        last_checkin = checkins[-1]
    else:
        last_checkin = None
    print(summary)
    return render_template('index.html',
                           checkins=checkins,
                           summary=summary,
                           last_checkin=last_checkin,
                           all_regs_count=all_regs_count,
                           )


@app.route('/register/mail')
def send_mail(rid=None, recp_mail=None):
    if rid is None:
        rid = request.args.get('rid')
        recp_mail = request.args.get('email')

    msg = Message('Welcome to ANHPERF conference.',
                  sender="likit.pre@mahidol.edu",
                  recipients=[recp_mail])

    if not os.path.exists(os.path.join(qrimage_dir, '{}.png'.format(rid))):
        get_barcode(rid)

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
@click.argument('rid')
def send_mail_barcode(rid=None,role=None):
    if rid:
        reg = Registration.query.filter_by(id=rid).first()
        participants = [reg.participant]
    else:
        role = 'invitee'
        participants = []

        for p in Participant.query.all():
            if p.role.desc == role and p.email:
                print(p.id, p.email, p.title, p.firstname, p.lastname, p.registers[-1].id, p.role.desc)
                participants.append(p)

    errors = []

    with mail.connect() as conn:
        for recp in participants:
            with app.open_resource("templates/message.txt") as template_fp:
                content = template_fp.read().decode('utf-8')

            msg = Message(subject='Welcome to the 6th Annual Health National Professional Reform Forum (ANHPERF {})'.format(YEAR),
                          sender="healthprofessionals21@gmail.com",
                          body=content,
                          recipients=['likit.pre@mahidol.edu'],
                          #recipients=[recp.email],
                          cc=['likit.pre@mahidol.edu'])
            rid = recp.registers[-1].id
            with app.open_resource("{}/{}.png".format(qrimage_dir, rid)) as fp:
                msg.attach("{}.png".format(rid), "image/png", fp.read())
                msg.html = render_template('message.html', register=recp.registers[-1])
            try:
                conn.send(msg)
            except:
                errors.append(recp)
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
            msg = Message(subject='Registration information for the 5th Annual Health National Professional Reform Forum (ANHPERF {})'.format(YEAR),
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
    register = Registration.query.filter(Registration.id==rid).first()
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
        register = Registration.query.filter(Registration.id==trim_id).first()
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
        return redirect(url_for('scan',rid=register.id, status=status))
    return redirect(url_for('scan'))


def get_barcode(rid):
    if not os.path.exists(qrimage_dir):
        os.mkdir(qrimage_dir)

    EAN = barcode.get_barcode_class('code128')
    ean = EAN(u'{}{:05}'.format(YEAR, int(rid)), writer=ImageWriter())
    imgname = ean.save('{}/{}'.format(qrimage_dir, rid))
    fp = open('{}'.format(imgname), 'wb')
    ean.write(fp)
    fp.close()


from .load_data import load

@app.cli.command()
@click.argument('inputfile')
def load_data(inputfile):
    load(inputfile)


@app.cli.command()
@click.argument('id', required=False)
def gen_barcode(id=None):
    if id is None:
        for reg in Registration.query.all():
            get_barcode(reg.id)
            print('Barcode for {} has been generated...'.format(reg.id))
    else:
        get_barcode(id)


if __name__ == '__main__':
    app.run()
