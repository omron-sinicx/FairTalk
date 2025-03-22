#!/usr/bin/env python

import os
import subprocess
import glob

# Get the directory where the script is located
script_dir = os.path.dirname(os.path.realpath(__file__))
src_dir = os.path.join(script_dir, '..', 'data')
asd_dir = os.path.join(script_dir, '..', 'TalkNet-ASD')
asd_script = "demoTalkNet.py"

# Change the working directory to ASD_DIR
os.chdir(asd_dir)

# Iterate over the "train", "val", and "test" subsets
for subset in ["train", "val", "test"]:
    # Iterate over all .mp4 files in the subset directory
    for video in glob.glob(os.path.join(src_dir, subset, '*.mp4')):
        dir = os.path.dirname(video)
        base = os.path.splitext(os.path.basename(video))[0]

        print(dir, base)

        completion_check = os.path.join(dir, base, '.completed')

        # Check if the completion_check file exists
        if os.path.exists(completion_check):
            print("skip (already completed)")
        else:
            # Construct the python command as a list of strings
            cmd = [
                'python',
                asd_script,
                '--videoFolder', dir,
                '--videoName', base
            ]

            # Run the command
            subprocess.run(cmd, check=True)

            # Create the completion_check file
            open(completion_check, 'a').close()
