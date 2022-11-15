import cv2, os, glob, tqdm, pickle, subprocess, argparse
import numpy as np
import pandas as pd

# This script needs three inputs
# 1. the .csv file that includes both output of TalkNet and OpenFace
# 2. the frame-wise .jpg files output by TalkNet
# 3. the audio.wav output by TalkNet (optional, only if you need the final output to have sound)

parser = argparse.ArgumentParser(description = "Visualize TalkNet+OpenFace")

parser.add_argument('--nDataLoaderThread',     type=int,   default=10,                     help='Number of workers')
parser.add_argument('--pyframesPath',          type=str,   default='./demo/002/pyframes',  help='the folder of frame-wise .jpg files')
parser.add_argument('--csv_input',             type=str,   default='./combined.csv',       help='the path of .csv that combines TalkNet and OpenFace')
parser.add_argument('--pyaviPath',             type=str,   default='./demo/002/pyavi',     help='the folder of audio.wav, also the output files go here')

args = parser.parse_args()

def visualization(df, args):
    # CPU: visulize the result for video format
    flist = glob.glob(os.path.join(args.pyframesPath, '*.jpg')) # load frame-wise .jpg files
    flist.sort()
    faces = [[] for i in range(len(flist))]
    
    for i in range(len(df)):
        frame = int(df.iloc[i]['frame'])
        if not np.isnan(df.iloc[i]['track_id']) and (not np.isnan(df.iloc[i]['face_id'])):            
            scene_id = int(df.iloc[i]['scene_id'])
            track_id = int(df.iloc[i]['track_id'])
            score = float(df.iloc[i]['ASDscore'])
            bbox_asd = [df.iloc[i]['bbox_xmin'],df.iloc[i]['bbox_ymin'],df.iloc[i]['bbox_xmax'],df.iloc[i]['bbox_ymax']]
            bbox_face = [df.iloc[i]['xmin'],df.iloc[i]['ymin'],df.iloc[i]['xmax'],df.iloc[i]['ymax']]
            faces[frame].append({'scene':scene_id, 'track':track_id, 'score':score, 'bbox_asd':bbox_asd, 'bbox_face':bbox_face})
    
    firstImage = cv2.imread(flist[0]) # read first image
    fw = firstImage.shape[1] # width
    fh = firstImage.shape[0] # height
    vOut = cv2.VideoWriter(os.path.join(args.pyaviPath, 'combined_video_only.avi'), cv2.VideoWriter_fourcc(*'XVID'), 25, (fw,fh)) # output file
    colorDict = {0: 0, 1: 255}
    for fidx, fname in tqdm.tqdm(enumerate(flist), total = len(flist)): # loop reading image
        image = cv2.imread(fname)
        for face in faces[fidx]:
            clr = colorDict[int((face['score'] >= 0))]
            txt = "id:"+str(face['track'])+" "+str(round(face['score'], 1))
            txt2 = "scene:"+str(face['scene'])
            cv2.rectangle(image, (int(face['bbox_asd'][0]), int(face['bbox_asd'][1])), (int(face['bbox_asd'][2]), int(face['bbox_asd'][3])),(0,clr,255-clr),5) # create rectangle
            cv2.rectangle(image, (int(face['bbox_face'][0]), int(face['bbox_face'][1])), (int(face['bbox_face'][2]), int(face['bbox_face'][3])),(255,0,0),5) # create rectangle
            cv2.putText(image,'%s'%(txt), (int(face['bbox_asd'][0]), int(face['bbox_asd'][1])-5), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,clr,255-clr),2) # create score text
            cv2.putText(image,'%s'%(txt2), (5, 20), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255),2) # create scene_id text
            # color is (BGR)
        vOut.write(image)
    vOut.release()
    
    command = ("ffmpeg -y -i %s -i %s -threads %d -c:v copy -c:a copy %s -loglevel panic" % \
        (os.path.join(args.pyaviPath, 'combined_video_only.avi'), os.path.join(args.pyaviPath, 'audio.wav'), \
        args.nDataLoaderThread, os.path.join(args.pyaviPath,'combined_video_out.avi'))) 
    output = subprocess.call(command, shell=True, stdout=None)
    
def visualization2(df, args): # adding visualization for IOU<0.1 case
    # CPU: visulize the result for video format
    flist = glob.glob(os.path.join(args.pyframesPath, '*.jpg')) # load frame-wise .jpg files
    flist.sort()
    faces = [[] for i in range(len(flist))]
    
    for i in range(len(df)):
        frame = int(df.iloc[i]['frame'])
#         if not np.isnan(df.iloc[i]['track_id']):
        scene_id = df.iloc[i]['scene_id']
        track_id = df.iloc[i]['track_id']
        score = df.iloc[i]['ASDscore']
        bbox_asd = [df.iloc[i]['bbox_xmin'],df.iloc[i]['bbox_ymin'],df.iloc[i]['bbox_xmax'],df.iloc[i]['bbox_ymax']]
#         else:
#             scene_id, track_id, score, bbox_asd = [],[],[],[[],[],[],[]]
#         if not np.isnan(df.iloc[i]['face_id']):
        bbox_face = [df.iloc[i]['xmin'],df.iloc[i]['ymin'],df.iloc[i]['xmax'],df.iloc[i]['ymax']]
#         else:
#             bbox_face = [[],[],[],[]]
        faces[frame].append({'scene':scene_id, 'track':track_id, 'score':score, 'bbox_asd':bbox_asd, 'bbox_face':bbox_face})
    with open("test2", "wb") as fp:
        pickle.dump(faces,fp)
    
    firstImage = cv2.imread(flist[0]) # read first image
    fw = firstImage.shape[1] # width
    fh = firstImage.shape[0] # height
    vOut = cv2.VideoWriter(os.path.join(args.pyaviPath, 'combined_video_only.avi'), cv2.VideoWriter_fourcc(*'XVID'), 25, (fw,fh)) # output file
    colorDict = {0: 0, 1: 255}
    for fidx, fname in tqdm.tqdm(enumerate(flist), total = len(flist)): # loop reading image
        image = cv2.imread(fname)
        for face in faces[fidx]:
            if not np.isnan(face['track']):                              
                clr = colorDict[int((face['score'] >= 0))] # color is (BGR)
                txt = "id:"+str(int(face['track']))+" score:"+str(round(face['score'], 1))
                txt2 = "scene:"+str(int(face['scene']))
                if not np.isnan(face['bbox_face'][0]):
                    cv2.rectangle(image, (int(face['bbox_asd'][0]), int(face['bbox_asd'][1])), (int(face['bbox_asd'][2]), int(face['bbox_asd'][3])),(0,clr,255-clr),5) # create rectangle
                    cv2.rectangle(image, (int(face['bbox_face'][0]), int(face['bbox_face'][1])), (int(face['bbox_face'][2]), int(face['bbox_face'][3])),(255,0,0),5) # create rectangle
                else:
                    cv2.rectangle(image, (int(face['bbox_asd'][0]), int(face['bbox_asd'][1])), (int(face['bbox_asd'][2]), int(face['bbox_asd'][3])),(100,100,100),5) # create rectangle
                cv2.putText(image,'%s'%(txt), (int(face['bbox_asd'][0]), int(face['bbox_asd'][1])-5), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,clr,255-clr),2) # create score text
                cv2.putText(image,'%s'%(txt2), (5, 20), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255),2) # create scene_id text
            else:
#                 print(fidx,face['bbox_face'])
                cv2.rectangle(image, (int(face['bbox_face'][0]), int(face['bbox_face'][1])), (int(face['bbox_face'][2]), int(face['bbox_face'][3])),(150,150,150),5) # create rectangle           
        vOut.write(image)
    vOut.release()
    
    command = ("ffmpeg -y -i %s -i %s -threads %d -c:v copy -c:a copy %s -loglevel panic" % \
        (os.path.join(args.pyaviPath, 'combined_video_only.avi'), os.path.join(args.pyaviPath, 'audio.wav'), \
        args.nDataLoaderThread, os.path.join(args.pyaviPath,'combined_video_out.avi'))) 
    output = subprocess.call(command, shell=True, stdout=None)
    
# Main function
def main():
    df = pd.read_csv(args.csv_input)
    visualization2(df, args)

if __name__ == '__main__':
    main()