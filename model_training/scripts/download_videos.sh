#!/bin/bash

SCRIPT_DIR=$(cd $(dirname $0); pwd)
CONFIG_DIR="$SCRIPT_DIR/../config"
DEST_DIR="$SCRIPT_DIR/../data"

# download from vimeo
for subset in "train" "val" "test"; do
   dat="${CONFIG_DIR}/vimeo_list_${subset}.dat"
   echo download ${dat}
   yt-dlp --batch-file ${dat} --output  "${DEST_DIR}/${subset}/${subset}_vimeo_%(id)09d.mp4"    
done

# add youtube videos to train
dat="${CONFIG_DIR}/youtube_list_train.dat"
echo download ${dat}
yt-dlp --batch-file ${dat} --output  "${DEST_DIR}/train/train_youtube_%(display_id)s.%(ext)s" --format "bestvideo+bestaudio/best"