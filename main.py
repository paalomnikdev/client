from flask import Flask, jsonify, request
import requests
import time
from py3nvml.py3nvml import *
from pprint import pprint
import os
import json


nvmlInit()
app = Flask(__name__)
app.config.from_pyfile('settings.py')


def full_info():
    nvmlInit()
    total_gpu = nvmlDeviceGetCount()
    device_info = {}
    for i in range(0, total_gpu):
        try:
            handle = nvmlDeviceGetHandleByIndex(i)
            device_info[str(i)] = {}
            device_info[str(i)]['name'] = nvmlDeviceGetName(handle)
            device_info[str(i)]['power_limit'] = (nvmlDeviceGetPowerManagementLimit(handle) / 1000.0)
            device_info[str(i)]['fan_speed'] = nvmlDeviceGetFanSpeed(handle)
            device_info[str(i)]['temperature'] = nvmlDeviceGetTemperature(handle, NVML_TEMPERATURE_GPU)
            device_info[str(i)]['memory_overclock'] = os.popen(
                'nvidia-settings -q [gpu:{gpu_num}]/GPUMemoryTransferRateOffset -t'.format(gpu_num=str(i))
            ).read().strip()
            device_info[str(i)]['core_overclock'] = os.popen(
                'nvidia-settings -q [gpu:{gpu_num}]/GPUGraphicsClockOffset -t'.format(gpu_num=str(i))
            ).read().strip()
        except NVMLError:
            os.system('sudo shutdown -r now')
            raise Exception('Card is down')

    return device_info


for x in range(0, 10):
    try:
        requests.post(
            'http://{master_node}/api/register-rig'.format(master_node=app.config['MASTER_NODE_ADDRESS']),
            data={
                'name': app.config['IDENTITY_FOR_SERVER'],
                'stats': json.dumps(full_info())
            }
        )
        break
    except:
        time.sleep(20)
        continue


def set_config(params):
    if 'id' not in params:
        return jsonify({'success': False})
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
                    v=params['memory_overclock']
                )
            )
            os.popen(
                'nvidia-settings -a [gpu:{i}]/GPUMemoryTransferRateOffset[2]={v}'.format(
                    i=params['id'],
                    v=params['memory_overclock']
                )
            )

        if 'gpu_clock' in params:
            os.popen(
                'nvidia-settings -a [gpu:{i}]/GPUGraphicsClockOffset[3]={v}'.format(
                    i=params['id'],
                    v=params['core_overclock']
                )
            )
            os.popen(
                'nvidia-settings -a [gpu:{i}]/GPUGraphicsClockOffset[2]={v}'.format(
                    i=params['id'],
                    v=params['core_overclock']
                )
            )

        if 'fan_speed' in params:
            os.popen(
                'nvidia-settings -a [gpu:{i}]/GPUFanControlState=1'.format(i=params['id'])
            )
            os.popen(
                'nvidia-settings -a [fan-{i}]/GPUTargetFanSpeed={v}'.format(
                    i=params['id'],
                    v=params['fan_speed']
                )
            )
    except:
        message = 'Something went wrong. Please check rig\'s log.'
        os.system('sudo shutdown -r now')
        return jsonify({
            'success': False,
            'message': message
        })

    return jsonify({
        'success': True,
        'message': message
    })


@app.route('/gpu-control/<f>', methods=['POST', 'GET'])
def execute_command_query(f):
    if f == 'set-config':
        return set_config(request.form)
    else:
        return jsonify({})


@app.route('/check-alive')
def check_alive():
    result = {}
    try:
        result = full_info()
    except:
        return jsonify({
            'alive': False,
            'result': result
        })

    return jsonify({
        'alive': True,
        'result': result
    })


if __name__ == '__main__':
    app.run(host=app.config['HOST'])
