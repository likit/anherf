import os
import qrcode
import datetime
from flask import (Flask, jsonify, render_template,
                    send_file, request, url_for)
from flask_mail import Message, Mail
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

mail = Mail()

basedir =  os.path.dirname(os.path.abspath(__file__))
qrimage_dir = os.path.join(basedir, 'qrimages')

app = Flask(__name__)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_USERNAME'] = 'likit.pre@mahidol.edu'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_PORT'] = 587
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres+psycopg2://postgres@pg/anherf'
mail.init_app(app)

db = SQLAlchemy(app)
migrate = Migrate(app, db)


def random_qr(url):
    qr = qrcode.QRCode(version=1,
                       error_correction=qrcode.constants.ERROR_CORRECT_L,
                       box_size=10,
                       border=4)

    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image()
    return img


@app.route('/api/register/list')
def get_list_api():
    values = []
    return jsonify(values)


@app.route('/register')
def show_register():
    values = []
    return render_template('list.html', plist=values)


@app.route('/register/mail')
def send_mail():
    rid = request.args.get('rid')
    recp_mail = request.args.get('email')

    msg = Message('Welcome to ANHERF conference.',
                  sender="likit.pre@mahidol.edu",
                  recipients=[recp_mail])

    if not os.path.exists(os.path.join(qrimage_dir, '{}.png'.format(rid))):
        get_qrimg(rid)

    with app.open_resource("qrimages/{}.png".format(rid)) as fp:
        msg.attach("{}.png".format(rid), "image/png", fp.read())

    mail.send(msg)
    return 'The mail has been sent.'


@app.route('/api/checkin/<rid>')
@app.route('/api/checkin')
def checkin(rid=None):
    if not rid:
        return jsonify({'message': 'No account ID specified'})
    else:
        gc = gspread.authorize(get_credential())
        wks = gc.open_by_url(googlesheet_url).sheet1
        chckwks = gc.open_by_url(googlesheet_checkin_url).sheet1
        cell = wks.find(rid)
        data = wks.row_values(cell.row)

        if chckwks.cell(cell.row, 8).value and chckwks.cell(cell.row, 9).value:
            return jsonify({'message': 'Already checked in.'})

        checkin_date = datetime.datetime.now().strftime('%m/%d/%Y')
        checkin_time = datetime.datetime.now().strftime('%H:%M:%S')
        chckwks.update_cell(cell.row, 1, rid)
        chckwks.update_cell(cell.row, 2, data[52])
        chckwks.update_cell(cell.row, 3, data[9])
        chckwks.update_cell(cell.row, 4, data[10])
        chckwks.update_cell(cell.row, 5, data[3])
        chckwks.update_cell(cell.row, 6, data[48])
        chckwks.update_cell(cell.row, 7, data[5])
        chckwks.update_cell(cell.row, 8, checkin_date)
        chckwks.update_cell(cell.row, 9, checkin_time)

        return jsonify({'message': 'Checked in at %s %s.' % (checkin_date, checkin_time), 'rid': cell.row})


def get_qrimg(rid):
    img = random_qr(url=url_for('checkin', rid=rid, _external=True))
    img.save('{}/{}.png'.format(qrimage_dir, rid), 'png')


if __name__ == '__main__':
    app.run()