#!/usr/bin/env python3

import os
import sys
import subprocess

# cpu_num = 1
# if len(sys.argv) > 1:
#     cpu_num = int(sys.argv[1])

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
SRC_DIR = os.path.join(SCRIPT_DIR, "..", "data")
PYTHON_SCRIPT = os.path.join(SCRIPT_DIR, "combine.py")
subsets = ["train", "val", "test"]
print(os.path.normpath(SCRIPT_DIR))

# def open_sem(tokens):
#     subprocess.run(["mkfifo", "pipe-$$"])
#     semaphore = open("pipe-$$", "w+")
#     os.remove("pipe-$$")
#     for _ in range(tokens):
#         semaphore.write("000\n")
#     semaphore.flush()
#     return semaphore


# def run_with_lock(command, semaphore):
#     x = semaphore.read(3)
#     if x != "000":
#         exit(int(x))
#     subprocess.Popen(command, shell=True).wait()
#     return_code = str(subprocess.CompletedProcess.returncode)
#     semaphore.write(return_code.zfill(3) + "\n")
#     semaphore.flush()

# semaphore = open_sem(cpu_num)



for subset in subsets:
    openface_dir = os.path.join(SRC_DIR, "openface_features", subset)
    asd_dir = os.path.join(SRC_DIR, subset)
    videos = [f for f in os.listdir(os.path.join(SRC_DIR, subset)) if (not f.startswith('.')) and (os.path.isfile(os.path.join(SRC_DIR, subset, f)))]
    for video in videos:
        video_path = os.path.join(SRC_DIR, subset, video)
        directory = os.path.dirname(video_path)
        base = os.path.splitext(video)[0]

        completion_check = os.path.join(directory, base, ".combined")
        if os.path.exists(completion_check):
            print(f"skip (already completed) {base}")
        else:
            command = f"python {PYTHON_SCRIPT} -f {openface_dir}/{base} -a {directory}/{base} -o {directory}/{base}"
            subprocess.run(command, check=True)
            with open(completion_check, 'w') as file:
                pass

