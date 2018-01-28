from flask import Flask, jsonify
import requests
import time
from py3nvml.py3nvml import *
from pprint import pprint


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
    nvmlInit()
    total_gpu = nvmlDeviceGetCount()
    device_info = {}
    for i in range(0, total_gpu):
        try:
            handle = nvmlDeviceGetHandleByIndex(i)
            device_info[str(i)] = {}
            device_info[str(i)]['name'] = nvmlDeviceGetName(handle)
            device_info[str(i)]['fan_speed'] = nvmlDeviceGetFanSpeed(handle)
            device_info[str(i)]['temperature'] = nvmlDeviceGetTemperature(handle, NVML_TEMPERATURE_GPU)
        except NVMLError:
            print('A')

    return jsonify({
        'total_gpu': total_gpu,
        'device_info': device_info
    })


@app.route('/gpu-control/<f>')
def execute_command_query(f):
    pprint(f)
    if f == 'fullinfo':
        return full_info()
    elif f == 'test':
        pass
    else:
        return jsonify({})


@app.route('/check-alive')
def check_alive():
    return jsonify({'alive': 'yes'})


if __name__ == '__main__':
    app.run(host=app.config['HOST'], port=app.config['PORT'])
