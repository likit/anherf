# -*- coding: utf-8 -*-

import os
import click
import barcode
from barcode.writer import ImageWriter
import datetime
from flask import (Flask, jsonify, render_template,
                    send_file, request, url_for, redirect)
from flask_mail import Message, Mail
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

mail = Mail()

basedir =  os.path.dirname(os.path.abspath(__file__))
qrimage_dir = os.path.join(basedir, 'qrimages')

app = Flask(__name__)
app.config['MAIL_DEBUG'] = True
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_USERNAME'] = 'likit.pre@mahidol.edu'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_PORT'] = 587
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres+psycopg2://postgres@pg/anherf'
mail.init_app(app)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

from .models import *


@app.route('/api/register/list')
def get_list_api():
    participants = Participant.query.all()[:30]
    return jsonify(participants)


@app.route('/register')
def show_register():
    participants = Participant.query.all()
    return render_template('list.html', plist=participants)


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


def send_mail_payment_reminder(recp_mail=None):
    with app.open_resource("templates/participant_mail.html") as template_fp:
        content = template_fp.read().decode('utf-8')

    # mail_subject = 'ยินดีต้อนรับเข้าสู่งานประชุมวิขาการประจำปีระดับชาติ การพัฒนาการศึกษาสำหรับบุคลากรสุขภาพ ครั้งที่ 5'
    msg = Message(subject='Registration information for the 5th Annual Health National Professional Reform Forum (ANHPERF 2018)',
                    sender="likit.pre@mahidol.edu",
                    body=content,
                    recipients=[recp_mail],
                    cc=['likit.pre@mahidol.edu'],
                  )
    try:
        mail.send(msg)
    except Exception as e:
        raise(e)
        return 'An error has occurred.'
    else:
        return 'The mail has been sent.'


@app.route('/register/mail/test')
def test_mail():
    response = send_mail_payment_reminder(recp_mail='manuschonk@gmail.com')
    return response


@app.route('/paid/<rid>')
def pay(rid=None):
    if not rid:
        return jsonify({'message': 'No account ID specified'})
    register = Registration.query.rilter(Registration.id==rid).first()
    # participant can only check in a single time
    if register.checked_at is None:
        register.pay_status = True
        register.checked_at = datetime.datetime.utcnow()
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
        register = Registration.query.filter(Registration.participant_id==trim_id).first()
        # participant can only check in a single time
        if register.checked_at is None:
            register.checked_at = datetime.datetime.utcnow()
        db.session.add(register)
        db.session.commit()
        return redirect(request.referrer)


def get_barcode(rid):
    EAN = barcode.get_barcode_class('code128')
    ean = EAN(u'2018{:05}'.format(int(rid)), writer=ImageWriter())
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
@click.argument('id')
def gen_barcode(id):
    get_barcode(id)


if __name__ == '__main__':
    app.run()
