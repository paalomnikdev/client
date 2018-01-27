from flask import Flask, jsonify
import requests
import time

app = Flask(__name__)
app.config.from_pyfile('settings.py')


for x in range(0, 10):
    try:
        requests.post(
            'http://{master_node}/register'.format(master_node=app.config['MASTER_NODE_ADDRESS']),
            data={
                'name': app.config['IDENTITY_FOR_SERVER'],
                'secret': app.config['SECRET_TOKEN'],
                'command_ip': '{host}:{port}'.format(host=app.config['HOST'], port=app.config['PORT'])
            }
        )
        break
    except:
        time.sleep(20)
        continue


@app.route('/command/<command>', defaults={'command': None})
def command(command):
    pass


@app.route('/check-alive')
def check_alive():
    return jsonify({'alive': 'yes'})


if __name__ == '__main__':
    app.run(host=app.config['HOST'], port=app.config['PORT'])
