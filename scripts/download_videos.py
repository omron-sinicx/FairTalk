#!/usr/bin/env python

import os
import subprocess

# Get the directory where the script is located
script_dir = os.path.dirname(os.path.realpath(__file__))
config_dir = os.path.join(script_dir, '..', 'config')
dest_dir = os.path.join(script_dir, '..', 'data')

# Iterate over the "train", "val", and "test" subsets
for subset in ["train", "val", "test"]:
    dat = os.path.join(config_dir, f'video_list_{subset}.dat')

    print(f'download {dat}')

    # Construct the yt-dlp command as a list of strings
    cmd = [
        'yt-dlp',
        '--batch-file', dat,
        '--output', os.path.join(dest_dir, f'{subset}/{subset}_vimeo_%(id)09d.mp4')
    ]

    # Run the command
    subprocess.run(cmd, check=True)
