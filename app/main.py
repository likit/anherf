import os
import gspread
import qrcode
import cStringIO
from oauth2client.service_account import ServiceAccountCredentials
from flask import Flask, url_for, jsonify, send_file

basedir =  os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)

def get_credential():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    json_file = os.environ.get("GOOGLE_CREDENTIAL_FILE")
    credential = ServiceAccountCredentials.from_json_keyfile_name(json_file, scope)
    return credential

def random_qr(url):
    qr = qrcode.QRCode(version=1,
                       error_correction=qrcode.constants.ERROR_CORRECT_L,
                       box_size=10,
                       border=4)

    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image()
    return img


@app.route('/register/list')
def showlist():
    print('loading data..')
    gc = gspread.authorize(get_credential())
    wks = gc.open_by_url(
        'https://docs.google.com/spreadsheets/d/'
        '1U50uAjGNPHAZ4zGIpqN2B5AnISntaMFtt11LYOl8VLk/edit#gid=0').sheet1
    values = wks.get_all_values()
    return jsonify(values)


@app.route('/get_qrimg/<int:rid>')
def get_qrimg(rid):
    qrimage_dir = os.path.join(basedir, 'qrimages')
    img = random_qr(url='www.python.org')
    img.save('{}/{}.png'.format(qrimage_dir, rid), 'png')
    return 'success!'


if __name__ == '__main__':
    app.run()
