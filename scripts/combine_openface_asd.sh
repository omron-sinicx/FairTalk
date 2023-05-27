#!/bin/bash

cpu_num=1
if [ $# -gt 0 ]; then
    cpu_num=$1
fi
    

SCRIPT_DIR=$(cd $(dirname $0); pwd)
SRC_DIR="$SCRIPT_DIR/../data"
PYTHON_SCRIPT="$SCRIPT_DIR/combine.py"
subsets=("train" "val" "test")

# parallelize for loop in a smart way!
# https://unix.stackexchange.com/questions/103920/parallelize-a-bash-for-loop
# initialize a semaphore with a given number of tokens
open_sem(){
    mkfifo pipe-$$
    exec 3<>pipe-$$
    rm pipe-$$
    local i=$1
    for((;i>0;i--)); do
        printf %s 000 >&3
    done
}

# run the given command asynchronously and pop/push tokens
run_with_lock(){
    local x
    # this read waits until there is something to read
    read -u 3 -n 3 x && ((0==x)) || exit $x
    (
     ( "$@"; )
    # push the return code of the command to the semaphore
    printf '%.3d' $? >&3
    )&
}

open_sem $cpu_num

for subset in "train" "val" "test"; do
    openface_dir=$SRC_DIR/openface_features/$subset/
    asd_dir=$SRC_DIR/$subset
    for video in $(ls -1 $SRC_DIR/$subset/*.mp4); do
        dir=$(dirname $video)
        base=$(basename $video ".mp4")
        
        completion_check=$dir/$base/.combined
        if [ -e $completion_check ]; then
            echo "skip (already completed)"
        else
            run_with_lock python3 $PYTHON_SCRIPT -f $openface_dir/$base -a $dir/$base -o $dir/$base
        fi
    done
done
