# remote-meeting-dataset

# Dependencies
The repository assumes `python>=3.7.9`. We strongly recommend to use virtual env or docker to virtualize the environment.
````
% pip install -r requirement.txt
````

# How to run
## 1. Download video files  
To download video files from [vimeo](https://vimeo.com/), run
````
bash ./scripts/download_videos.sh   # for linux
python ./scripts/download_videos.py # for windows
````
The script that downloads video files from youtube is under preparation.

## 2. Apply active speaker detection (ASD) to video files  
We use [TalkNet](https://github.com/TaoRuijie/TalkNet-ASD/) to do ASD. Please refer to the link for the detail.  
You can download TalkNet from the above link, and put it into ./TalkNet-ASD, then setup it by
````
% cd TalkNet-ASD
% pip install -r requirement.txt
````
Then run
````
bash ./scripts/apply_asd.sh   # for linux
python ./scripts/apply_asd.py # for windows
````
Something to note
````
## ./TalkNet-ASD/requirement.txt does not include pandas which is needed. You may manually install pandas.
## ./TalkNet-ASD/requirement.txt does not ensure a pytorch version compatibale with your CUDA. You may manually install pytorch.
## If you are using windows, modify Line 217 of ./TalkNet-ASD/demoTalkNet.py to avoid an error due to path separator:
## Line 217: fileName, _ = os.path.splitext(os.path.basename(file))
````

## 3. Apply OpenFace to video files
We use [OpenFace](https://github.com/TadasBaltrusaitis/OpenFace) to extract features from videos. Please refer to the link for the detail.  
### (Need to add how to setup OpenFace here)
Then run ./scripts/apply_openface.sh

## 4. Convert the result .csv into 25fps (or 30fps) 
It is necessary to make sure that the above outputs from different videos have the same fps for the subsequent processing.  
25fps or 30fps is desirable.  
The script for conversion is under preparation.

## 5. Preprocessing, and combine ASD and OpenFace
Run ./code/ASD2csv_new.ipynb  
We will prepare a .py version later.

## 6. Train the model
Run ./code/LSTM_server_curri.ipynb  
We will prepare a .py version later.
