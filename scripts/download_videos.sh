#!/bin/bash


SCRIPT_DIR=$(cd $(dirname $0); pwd)
CONFIG_DIR="$SCRIPT_DIR/../config"
DEST_DIR="$SCRIPT_DIR/../data"
for subset in "train" "val" "test"; do
    dat="$CONFIG_DIR/video_list_$subset.dat"
    echo download $dat
    yt-dlp --batch-file $dat --output  "$DEST_DIR/$subset/$subset_vimeo_%(id)09d.mp4"
done