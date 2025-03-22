#!/bin/bash

OPENFACE_BIN_DIR=$1

echo "Please be sure to modify .exe/FaceLandmarkVidMulti/FaceLandmarkVidMulti.cpp L160 before compile OpenFace bin files."
echo "https://github.com/TadasBaltrusaitis/OpenFace/blob/3d4b5cf8d96138be42bed229447f36cbb09a5a29/exe/FaceLandmarkVidMulti/FaceLandmarkVidMulti.cpp#L160"
echo "before: int num_faces_max = 4;"
echo "after: int num_faces_max = 25;"


echo "You can also download the results from http://TBA ."
read -p "Did you surely modify the source code before build OpenFace? (y/N): " yn; case "$yn" in [yY]*) echo hello;; *) echo "abort";; esac

SCRIPT_DIR=$(cd $(dirname $0); pwd)
SRC_DIR="$SCRIPT_DIR/../data"
OPENFACE_EXE="$OPENFACE_BIN_DIR/FaceLandmarkVidMulti"

#openface_dir=$SRC_DIR/openface_features/train/
openface_dir=/mnt/ssd2/remote-meeting-dataset/openface_features/train/

for video in $(ls -1 $SRC_DIR/train/* | grep youtube); do
    dir=$(dirname $video)
    ext=".${video##*.}"
    ddir=$(dirname $dir)
    base=$(basename $video "$ext")
    echo $dir $base $ext
    completion_check=${openface_dir}/${base}/.completed
    if [ -e $completion_check ]; then
        echo "skip (already completed)"
    else
        mkdir -p $openface_dir/$base/
        $OPENFACE_EXE -f $video -out_dir $openface_dir/$base/ && touch $completion_check
    fi 
done
exit


subsets=("train" "val" "test")

for subset in "train" "val" "test"; do
    openface_dir=$SRC_DIR/openface_features/$subset/
    mkdir -p openface_dir
    for video in $(ls -1 $SRC_DIR/$subset/*.mp4); do
        dir=$(dirname $video)
        ddir=$(dirname $dir)
        base=$(basename $video ".mp4")
        echo $dir $base
        completion_check=$openface_dir/$base/.completed
        if [ -e $completion_check ]; then
            echo "skip (already completed)"
        else
            mkdir -p $openface_dir/$base/
            $OPENFACE_EXE -f $video -out_dir $openface_dir/$base/ && touch $completion_check
        fi
    done
done