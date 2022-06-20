#!/bin/bash

video_dir=$1

SCRIPT_DIR=$(cd $(dirname $0); pwd)
CONFIG_DIR="$SCRIPT_DIR/../config"
DEST_DIR="$SCRIPT_DIR/../data"
subsets=("train" "val" "test")
for subset in "train" "val" "test"; do
    dat="$CONFIG_DIR/video_list_$subset.dat"
    echo $dat
    yt-dlp　-a $dat --output  "$DEST_DIR/$subset/train_vimeo_%(id)09d.mp4"
done