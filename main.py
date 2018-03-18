from flask import Flask, jsonify, request
import requests
import time
from py3nvml.py3nvml import *
from pprint import pprint
import os
import subprocess
import json
import getpass


nvmlInit()
app = Flask(__name__)
app.config.from_pyfile('settings.py')


def reboot():
    command = "/usr/bin/sudo /sbin/shutdown -r now"
    import subprocess
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    process.communicate()


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
            temperature = int(nvmlDeviceGetTemperature(handle, NVML_TEMPERATURE_GPU))
            if temperature > app.config['TEMP_LIMIT']:
                reboot()
            device_info[str(i)]['temperature'] = temperature
            memory_overclock = os.popen(
                'nvidia-settings -q [gpu:{gpu_num}]/GPUMemoryTransferRateOffset -t'.format(gpu_num=str(i))
            ).read().strip()
            if len(memory_overclock) > 10:
                raise Exception('Card is down')
            else:
                device_info[str(i)]['memory_overclock'] = memory_overclock
            core_overclock = os.popen(
                'nvidia-settings -q [gpu:{gpu_num}]/GPUGraphicsClockOffset -t'.format(gpu_num=str(i))
            ).read().strip()
            if len(core_overclock) > 10:
                raise Exception('Card is down')
            else:
                device_info[str(i)]['core_overclock'] = core_overclock
        except:
            reboot()
            raise Exception('Card is down')

    return device_info


for x in range(0, 10):
    try:
        response = requests.post(
            'http://{master_node}/api/register-rig'.format(master_node=app.config['MASTER_NODE_ADDRESS']),
            data={
                'name': app.config['IDENTITY_FOR_SERVER'],
                'stats': json.dumps(full_info())
            }
        )
        json_data = json.loads(response.text)
        if 'temp_limit' in json_data:
            app.config['TEMP_LIMIT'] = int(json_data['temp_limit'])
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
        return jsonify({
            'success': False,
            'message': message
        })

    return jsonify({
        'success': True,
        'message': message
    })


@app.route('/miner', methods=['POST'])
def set_miner():
    params = request.form
    if 'command' in params and 'miner_path' in params:
        with open('miner.conf', 'r') as conf_template:
            conf = conf_template.read()
            conf.replace('{command}', 'miner')
            conf.replace('{miner_path}', 'path')
            conf.replace('{user}', getpass.getuser())
            os.popen('echo "{conf}" | sudo tee /etc/supervisor/conf.d/miner.conf'.format(conf=conf))


@app.route('/gpu-control/<f>', methods=['POST', 'GET'])
def execute_command_query(f):
    if f == 'set-config':
        return set_config(request.form)
    elif f == 'reboot':
        reboot()

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
