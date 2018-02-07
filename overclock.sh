#!/bin/bash
read -d "\0" -a number_of_gpus < <(nvidia-smi --query-gpu=count --format=csv,noheader,nounits)
index=$(( number_of_gpus[0] - 1 ))
for i in $(seq 0 $index)
do
    nvidia-smi -i $i -pm 1
    nvidia-smi -i $i -pl 100
    nvidia-settings -a [gpu:${i}]/GPUMemoryTransferRateOffset[3]=500
    nvidia-settings -a [gpu:${i}]/GPUGraphicsClockOffset[3]=100
    nvidia-settings -a [gpu:${i}]/GPUMemoryTransferRateOffset[2]=500
    nvidia-settings -a [gpu:${i}]/GPUGraphicsClockOffset[2]=100
    nvidia-settings -a [gpu:${i}]/GPUFanControlState=1 -a [fan-${i}]/GPUTargetFanSpeed=100
done