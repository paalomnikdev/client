from flask import Flask, jsonify
import requests
import time
from py3nvml.py3nvml import *
from pprint import pprint
import subprocess


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
        handle = nvmlDeviceGetHandleByIndex(i)
        device_info[str(i)] = {}
        device_info[str(i)]['name'] = nvmlDeviceGetName(handle)
        device_info[str(i)]['power_limit'] = (nvmlDeviceGetPowerManagementLimit(handle) / 1000.0)
        device_info[str(i)]['fan_speed'] = nvmlDeviceGetFanSpeed(handle)
        device_info[str(i)]['temperature'] = nvmlDeviceGetTemperature(handle, NVML_TEMPERATURE_GPU)
        device_info[str(i)]['memory_overclock'] = subprocess.check_output(
            'nvidia-settings -q [gpu:{gpu_num}]/GPUMemoryTransferRateOffset -t'.format(gpu_num=str(i)),
            shell=True
        )
        device_info[str(i)]['core_overclock'] = subprocess.check_output(
            'nvidia-settings -q [gpu:{gpu_num}]/GPUGraphicsClockOffset -t'.format(gpu_num=str(i)),
            shell=True
        )

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
