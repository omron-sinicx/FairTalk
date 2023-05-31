#!/bin/bash

cpu_num=1
if [ $# -gt 0 ]; then
    cpu_num=$1
fi
    
MAX_CONCURRENT_JOBS=4 
running_jobs_count() {
  jobs -r | wc -l
}

SCRIPT_DIR=$(cd $(dirname $0); pwd)
SRC_DIR="$SCRIPT_DIR/../data"
PYTHON_SCRIPT="$SCRIPT_DIR/combine.py"

# apply to youtube training dataset
openface_dir=$SRC_DIR/openface_features/train/
asd_dir=$SRC_DIR/train
for video in $(find $SRC_DIR/train/train_youtube* -maxdepth 0 -type f); do
    while (( $(running_jobs_count) >= MAX_CONCURRENT_JOBS )); do
      sleep 5
    done
    dir=$(dirname $video)
    base=$(basename $video ".mp4")

    completion_check=$dir/$base/.combined
    if [ -e $completion_check ]; then
        echo "skip (already completed)"
    else
        python3 $PYTHON_SCRIPT -f $openface_dir/$base -a $dir/$base -o $dir/$base && touch $completion_check
    fi
done
exit

for subset in "train" "val" "test"; do
    openface_dir=$SRC_DIR/openface_features/$subset/
    asd_dir=$SRC_DIR/$subset
    for video in $(ls -1 $SRC_DIR/$subset/*.mp4); do
        while (( $(running_jobs_count) >= MAX_CONCURRENT_JOBS )); do
          sleep 5
        done
        dir=$(dirname $video)
        base=$(basename $video ".mp4")
        
        completion_check=$dir/$base/.combined
        if [ -e $completion_check ]; then
            echo "skip (already completed)"
        else
            python3 $PYTHON_SCRIPT -f $openface_dir/$base -a $dir/$base -o $dir/$base && touch $completion_check
        fi
    done
done
