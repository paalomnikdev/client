from flask import Flask, jsonify
import requests
import time
from py3nvml.py3nvml import nvmlDeviceGetCount, nvmlInit


nvmlInit()
app = Flask(__name__)
app.config.from_pyfile('settings.py')


for x in range(0, 10):
    try:
        requests.post(
            'http://{master_node}/register'.format(master_node=app.config['MASTER_NODE_ADDRESS']),
            data={
                'name': app.config['IDENTITY_FOR_SERVER'],
                'secret': app.config['SECRET_TOKEN']
            }
        )
        break
    except:
        time.sleep(20)
        continue


def full_info():
    total_gpu = nvmlDeviceGetCount()

    return jsonify({
        'total_gpu': total_gpu
    })


@app.route('/gpu-control/<f>')
def execute_command_query(f):
    if f is 'fullinfo':
        return full_info()
    elif f is 'test':
        pass
    else:
        return jsonify({})


@app.route('/check-alive')
def check_alive():
    return jsonify({'alive': 'yes'})


if __name__ == '__main__':
    app.run(host=app.config['HOST'], port=app.config['PORT'])
