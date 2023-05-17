# remote-meeting-dataset

# Dependencies
The repository assumes `python>=3.7.9`. We strongly recommend to use virtual env or docker to virtualize the environment.
````
% pip install -r requirement.txt
````

# How to run
## Download video files  
Run ./scripts/download_videos.sh to download video files from [vimeo](https://vimeo.com/).  
The script that downloads video files from youtube is under preparation.

## Convert the videos into 25fps  
It is necessary to make all the videos have the same fps for the subsequent processing.  
The script that convert videos into 25fps is under preparation.

## Apply active speaker detection (ASD) to video files  
We use [TalkNet](https://github.com/TaoRuijie/TalkNet-ASD/) to do ASD. Please refer to the link for the detail.  
The files have been included in this repository. You can setup TalkNet-ASD by
````
% cd TalkNet-ASD
% pip install -r requirement.txt
````
Then run ./scripts/apply_asd.sh

## Apply OpenFace to video files
We use [OpenFace](https://github.com/TadasBaltrusaitis/OpenFace) to extract features from videos. Please refer to the link for the detail.  
### (Need to add how to setup OpenFace here)
Then run ./scripts/apply_openface.sh

## Preprocessing, and combine ASD and OpenFace
Run ./code/ASD2csv_new.ipynb  
We will prepare a .py version later.

## Train the model
Run ./code/LSTM_server_curri.ipynb  
We will prepare a .py version later.
