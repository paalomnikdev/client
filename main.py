from flask import Flask
import requests

app = Flask(__name__)
app.config.from_pyfile('settings.py')

requests.post(
    'http://{master_node}/register'.format(master_node=app.config['MASTER_NODE_ADDRESS']),
    data={
        'name': app.config['IDENTITY_FOR_SERVER'],
        'secret': app.config['SECRET_TOKEN'],
        'command_ip': '{host}:{port}'.format(host=app.config['HOST'], port=app.config['PORT'])
    }
)


@app.route('/command/<command>', defaults={'command': None})
def command(command):
    pass


if __name__ == '__main__':
    app.run(host=app.config['HOST'], port=app.config['PORT'])
