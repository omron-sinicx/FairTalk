#!/bin/bash


SCRIPT_DIR=$(cd $(dirname $0); pwd)
SRC_DIR="$SCRIPT_DIR/../data"
ASD_DIR="$SCRIPT_DIR/../TalkNet-ASD"
ASD_SCRIPT="demoTalkNet.py"
subsets=("train" "val" "test")

cd $ASD_DIR
for subset in "train" "val" "test"; do
    for video in $(ls -1 $SRC_DIR/$subset/*.mp4); do
        dir=$(dirname $video)
        base=$(basename $video ".mp4")
        echo $dir $base
        comletion_check=${dir}/${base}/.completed
        if [ -e $completion_check ]; then
            echo "skip (already completed)"
        else
            python $ASD_SCRIPT --videoFolder ${dir} --videoName ${base}&& touch $completion_check
        fi
    done
done