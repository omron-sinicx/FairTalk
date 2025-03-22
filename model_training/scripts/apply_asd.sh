#!/bin/bash


SCRIPT_DIR=$(cd $(dirname $0); pwd)
SRC_DIR="$SCRIPT_DIR/../data"
ASD_DIR="$SCRIPT_DIR/../TalkNet-ASD"
ASD_SCRIPT="demoTalkNet.py"
subsets=("train" "val" "test")

cd $ASD_DIR

MAX_CONCURRENT_JOBS=4 
NUM_GPUs=2 
running_jobs_count() {
  jobs -r | wc -l
}

run_exe(){
  echo rsync -a $3/$5.* $4
  rsync -a $3/$5.* $4
  
  echo CUDA_VISIBLE_DEVICES=$1 python $2 --videoFolder $4 --videoName $5
  CUDA_VISIBLE_DEVICES=$1 python $2 --videoFolder $4 --videoName $5 && touch $6
}

i=0
for video in $(find $SRC_DIR/train/train_youtube* -maxdepth 0 -type f); do
    while (( $(running_jobs_count) >= MAX_CONCURRENT_JOBS )); do
      sleep 5
    done
    dir=$(dirname $video)
    tardir=${dir/"/scripts/../data"/""}

    tardir=${tardir/"/home/hashimoto/git"/"/mnt/ssd2"}
    ext=".${video##*.}"
    base=$(basename $video "$ext")
    echo $dir $base $ext
    completion_check=${tardir}/${base}/.completed
    if [ -e $completion_check ]; then
        echo "skip (already completed)"
    else
        gpu_id=$(expr $i % $NUM_GPUs )
        run_exe ${gpu_id} $ASD_SCRIPT ${dir} ${tardir} ${base} ${completion_check}&
        #echo CUDA_VISIBLE_DEVICES="${i%2}" python $ASD_SCRIPT --videoFolder ${dir} --videoName ${base} && touch $completion_check 
        i=`expr $i + 1`
    fi
done

wait
exit

for subset in "train" "val" "test"; do
    for video in $(ls -1 $SRC_DIR/$subset/*.mp4); do
        while (( $(running_jobs_count) >= MAX_CONCURRENT_JOBS )); do
          sleep 5
        done
        dir=$(dirname $video)
        base=$(basename $video ".mp4")
        echo $dir $base
        completion_check=${dir}/${base}/.completed
        if [ -e $completion_check ]; then
            echo "skip (already completed)"
        else
            python $ASD_SCRIPT --videoFolder ${dir} --videoName ${base}&& touch $completion_check
        fi
    done
done