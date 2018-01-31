from flask import Flask, jsonify, request
import requests
import time
from py3nvml.py3nvml import *
from pprint import pprint
import os


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
        device_info[str(i)]['memory_overclock'] = os.popen(
            'nvidia-settings -q [gpu:{gpu_num}]/GPUMemoryTransferRateOffset -t'.format(gpu_num=str(i))
        ).read()
        device_info[str(i)]['core_overclock'] = os.popen(
            'nvidia-settings -q [gpu:{gpu_num}]/GPUGraphicsClockOffset -t'.format(gpu_num=str(i))
        ).read()

    return jsonify({
        'total_gpu': total_gpu,
        'device_info': device_info
    })


def set_config(params):
    pprint(params)
    if 'id' not in params:
        return jsonify({'success': False})
    success = True
    message = ''
    try:
        os.popen('nvidia-smi -i {i} -pm 1'.format(i=params['id']))
        if 'power_limit' in params:
            os.popen(
                'sudo nvidia-smi -i {i} -pl {v}'.format(i=params['id'], v=params['power_limit'])
            )

        if 'memory_clock' in params:
            os.popen(
                'nvidia-settings -a [gpu:{i}]/GPUMemoryTransferRateOffset[3]={v}'.format(
                    i=params['id'],
                    v=params['memory_clock']
                )
            )
            os.popen(
                'nvidia-settings -a [gpu:{i}]/GPUMemoryTransferRateOffset[2]={v}'.format(
                    i=params['id'],
                    v=params['memory_clock']
                )
            )

        if 'gpu_clock' in params:
            os.popen(
                'nvidia-settings -a [gpu:{i}]/GPUGraphicsClockOffset[3]={v}'.format(
                    i=params['id'],
                    v=params['gpu_clock']
                )
            )
            os.popen(
                'nvidia-settings -a [gpu:{i}]/GPUGraphicsClockOffset[2]={v}'.format(
                    i=params['id'],
                    v=params['gpu_clock']
                )
            )

        if 'fan_speed' in params:
            os.popen(
                'nvidia-settings -a [gpu:{i}]/GPUFanControlState=1'.format(i=params['id'])
            )
            os.popen(
                'nvidia-settings -a [fan:{i}]/GPUTargetFanSpeed={v}'.format(
                    i=params['id'],
                    v=params['fan_speed']
                )
            )
    except:
        success = False
        message = 'Something went wrong. Please check rig\'s log.'

    return jsonify({
        'success': success,
        'message': message
    })


@app.route('/gpu-control/<f>', methods=['POST', 'GET'])
def execute_command_query(f):
    if f == 'fullinfo':
        return full_info()
    elif f == 'set-config':
        return set_config(request.form)
    else:
        return jsonify({})


@app.route('/check-alive')
def check_alive():
    return jsonify({'alive': 'yes'})


if __name__ == '__main__':
    app.run(host=app.config['HOST'], port=app.config['PORT'])
