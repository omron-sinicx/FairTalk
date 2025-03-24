# FairTalk: Visualizing User's Willingness to Speak

## Overview

FairTalk is a system that aims to enhance the balance of speaking opportunities during video conferences by predicting a user's intention to speak and visualizing it through webcam enhancements. This project consists of two main components: model training and application. The model training part is for those who want to experiment with model improvements, while the application uses the pre-trained model for real-time video conferencing.

## Table of Contents

- [FairTalk: Visualizing User's Willingness to Speak](#fairtalk-visualizing-users-willingness-to-speak)
  - [Overview](#overview)
  - [Table of Contents](#table-of-contents)
  - [Getting Started](#getting-started)
    - [Cloning the Repository](#cloning-the-repository)
  - [Model Training](#model-training)
    - [Environment Setup for Model Training](#environment-setup-for-model-training)
    - [Video Download](#video-download)
    - [Active Speaker Detection (ASD)](#active-speaker-detection-asd)
    - [Feature Extraction with OpenFace](#feature-extraction-with-openface)
    - [Data Preprocessing](#data-preprocessing)
    - [Model Training Process](#model-training-process)
  - [Application Usage](#application-usage)
    - [Environment Setup for Application](#environment-setup-for-application)
    - [Building OpenFace](#building-openface)
    - [Starting the Application](#starting-the-application)
  - [License](#license)

## Getting Started

### Cloning the Repository

To get started, first clone the repository with all its submodules. Open a terminal and run:

```bash
git clone --recursive git@github.com:omron-sinicx/FairTalk.git
cd FairTalk
```

## Model Training

### Environment Setup for Model Training

Ensure you have Python >= 3.7.9. It is highly recommended to use a virtual environment to manage dependencies. Navigate to the `model_training` directory and set up your environment:

```bash
cd model_training
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Video Download

To download video files from Vimeo and YouTube, navigate to `model_training/scripts` and execute the following command for Linux or Windows:

Linux:
```bash
bash download_videos.sh
```

Windows:
```bash
python download_videos.py
```

### Active Speaker Detection (ASD)

We use TalkNet for ASD. First, initialize the TalkNet submodule and set it up by running:

```bash
cd TalkNet-ASD
pip install -r requirement.txt
```

You might need to manually install `pandas` and ensure compatibility of PyTorch with your CUDA version. For Windows, modify line 217 of `./demoTalkNet.py` to use the correct path separator.

Apply ASD using:

Linux:
```bash
bash ../scripts/apply_asd.sh
```

Windows:
```bash
python ../scripts/apply_asd.py
```

### Feature Extraction with OpenFace

To extract features from videos using OpenFace, ensure OpenFace is properly set up as described in the Application section. Apply OpenFace using:

```bash
bash ./scripts/apply_openface.sh
```

### Data Preprocessing

Combine ASD result and OpenFace result by running:

Linux:
```bash
bash ./scripts/combine_openface_asd.sh
```

Windows:
```bash
python ./scripts/combine_openface_asd.py
```

### Model Training Process

Run data preprocessing through the Jupyter notebook:

```bash
jupyter notebook ./code/preprocessing.ipynb
```

To train the model, execute the Jupyter notebook that handles training:

```bash
jupyter notebook ./code/LSTM_server_curri.ipynb
```

## Application Usage

### Environment Setup for Application

Make sure your Python environment is set up correctly for the application by navigating to `application/python_scripts` and installing the dependencies:

```bash
cd application/python_scripts
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

pyvirtualcam can be installed from source as it currently fails to install via pip (See this [reference page](https://github.com/letmaik/pyvirtualcam#build-from-source)):

```bash
git clone https://github.com/letmaik/pyvirtualcam --recursive
cd pyvirtualcam
pip install .
```

### Building OpenFace

Ensure OpenFace is built correctly. First, make sure all required dependencies are installed:

```bash
brew update
brew install gcc --HEAD
brew install boost
brew install tbb
brew install openblas
brew install --build-from-source dlib
brew install wget
brew install opencv
brew install ffmpeg
brew install portaudio
```

Compile OpenFace by navigating to the `OpenFace` directory:

```bash
cd ../../OpenFace
sh download_models.sh
mkdir build
cd build
cmake -D CMAKE_BUILD_TYPE=RELEASE ..
make
```

When the build is successful, you're ready to use OpenFace. For more information about OpenFace features, refer to the OpenFace Wiki.

If OpenFace runs slowly (below 3 FPS), reduce thread usage:

```bash
export OMP_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1
```

### Starting the Application

Copy and edit `config_sample.yml` as `config.yml` to set camera and audio devices:

```bash
cd application/python_scripts
cp ./config_sample.yml ./config.yml
```

You can find camera and audio device numbers by running:

```bash
python get_device_number_and_name.py
```

A sample output would look like:

```
Camera Devices:
 [0] FaceTime HD Camera
 [1] OBS Virtual Camera
 [2] HD Pro Webcam C920
Audio Devices:
 [0] BlackHole 2ch
 [1] MacBook Pro Microphone
 [2] HD Pro Webcam C920
 [3] Microsoft Teams Audio
 [4] ZoomAudioDevice
```

Install [OBS](https://obsproject.com/) and start virtual camera.

- Start OBS.
- Click "Start Virtual Camera" at the bottom right, then click "Stop Virtual Camera".
- Close OBS.

Execute the following command to start the virtual camera and enter standby for communication.
The `-c` option sets the camera mode: 1 for standard, 2 for implicit visualization, and 3 for explicit visualization.

```bash
python virtual_camera.py -c 2
```

In the terminal, open a new tab and run the command below to start OpenFace.

Note: if you specify the same camera device number with the `-device` option as the Python program, you might encounter an error. It's recommended to use the built-in camera for the Python program and an external camera for OpenFace program.

```
./build/bin/myFeatureExtraction -device 1
```

## License

This project is licensed under the terms of the MIT license. See `LICENSE` for more details.
