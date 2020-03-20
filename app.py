from flask import Flask, request
import json
import tripService
import os

app = Flask(__name__)
os.environ['SETTINGS_PATH'] = './instance/settings.cfg'
app.config.from_object('config.DefaultConfig')
app.config.from_envvar('SETTINGS_PATH')
file_save_path = '/tmp'


@app.route('/itinerary-parser', methods=['GET', 'POST'])
def get_trip_data():
    output_type = request.form.get('output_type', default='csv')
    pdf_file_path = request.form.get('pdf_file_path')
    trip_data = []
    code = 0
    message = 'success'
    try:
        # get pdf file data
        trip_data = tripService.read_trip(pdf_file_path, output_type, file_save_path)
    except Exception as e:
        code = 1
        message = e.__str__()
    response = {
        'code': code,
        'message': message,
        'data': trip_data
    }
    return json.dumps(response, ensure_ascii=False)


@app.route('/', methods=['GET', 'POST'])
def index():
    return 'hello world'


if __name__ == '__main__':
    app.run()
