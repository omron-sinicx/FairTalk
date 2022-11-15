import pickle
from pathlib import Path
import pandas as pd
import numpy as np
import argparse
from scipy.optimize import linear_sum_assignment
import joblib

parser = argparse.ArgumentParser(description='combine outputs by TalkNet-ASD and OpenFace into scene-wise files')


parser.add_argument('-a', '--asd_dir', type=str, default="./data/train/train_vimeo_410316487",
                    help='Set the directory where a result of active speaker detection (ASD) is.')
parser.add_argument('-f', '--openface_dir', type=str, default="./data/openface_features/train/train_vimeo_410316487",
                    help='Set the directory where the OpenFace features are.')
parser.add_argument('-o', '--output_dir', type=str, default="./data/train/train_vimeo_410316487",
                    help='Set the directore where the combined scene files will be stored.')
                

class ASDData():
    def __init__(self, path):
        self.dir = Path(path) / 'pywork'
        
        self.load()
        self.scene_ids=[int(str(self.scene[i]).split(",")[0].split("=")[-1]) 
                       for i in range(len(self.scene))]
        
        
    def _load(self, key):
        with open(self.dir / (key +".pckl"), 'rb') as f:
            return pickle.load(f)
                         
    def load(self):
        self.tracks = self._load('tracks')
        self.scores = self._load('scores')
        self.scene = self._load('scene')
        
    def get(self):
        d,df=[],[]
        scene_count=-1
        for i in range(len(self.tracks)):
            # if the start frame of a track == the start frame of a scene, the scene_id+=1
            #print("track:", i, "start frame:",self.tracks[i]['track']['frame'][0])
            if scene_count+1 < len(self.scene_ids):
                #   print(self.scene_ids[scene+1])
                if self.tracks[i]['track']['frame'][0] > self.scene_ids[scene_count+1]:
                    scene_count+=1
                    #print("scene is now", scene_count)

            d.append({'frame':self.tracks[i]['track']['frame'], 
                      'scene_id':scene_count,
                      'track_id':i,
                      'ASDscore':np.append(0, self.scores[i]), # len(scoredata) = len(data)-1, so add 0 at the head
                      'bbox_xmin':self.tracks[i]['track']['bbox'][:,0], 
                      'bbox_ymin':self.tracks[i]['track']['bbox'][:,1], 
                      'bbox_xmax':self.tracks[i]['track']['bbox'][:,2],
                      'bbox_ymax':self.tracks[i]['track']['bbox'][:,3]})

            df.append(pd.DataFrame(data=d[i]))
        result = pd.concat(df)
        return result.sort_values(by=["frame", "track_id"])

class BBMatcher():
    def __init__(self, asd_data, openface_data, threshold=0.1):
        self.asd_data = asd_data
        self.openface_data = openface_data
        self.threshold = threshold # min IOU to determine a combination
    
        xmin, ymin, xmax, ymax = self.get_of_minmax()
        # the index of 2d-landmarks
        self.openface_data['xmin'] = xmin
        self.openface_data['ymin'] = ymin
        self.openface_data['xmax'] = xmin
        self.openface_data['ymax'] = ymax
            
    
    @staticmethod
    def calc_iou(boxA, boxB, evalCol = False):
        # CPU: IOU Function to calculate overlap between two image
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2])
        yB = min(boxA[3], boxB[3])
        interArea = max(0, xB - xA) * max(0, yB - yA)
        boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
        boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
        if evalCol == True:
            iou = interArea / float(boxAArea)
        else:
            iou = interArea / float(boxAArea + boxBArea - interArea)
        return iou    
    
    def get_of_minmax(self):
        x1 = self.openface_data.columns.get_loc("x_0")
        x2 = self.openface_data.columns.get_loc("x_67")
        y1 = self.openface_data.columns.get_loc("y_0")
        y2 = self.openface_data.columns.get_loc("y_67")
        return np.min(self.openface_data.iloc[:,x1:x2],axis=1), np.max(self.openface_data.iloc[:,x1:x2],axis=1),  \
                np.min(self.openface_data.iloc[:,y1:y2],axis=1), np.max(self.openface_data.iloc[:,y1:y2],axis=1)


    def match(self):
        maxframe = max(self.openface_data["frame"].max(),self.asd_data["frame"].max())
        temp=[]
        asd_dummy = [np.NaN]*len(self.asd_data.columns)
        face_dummy = [np.NaN]*len(self.openface_data.columns)

        # for i in range(11):
        for i in range(maxframe+1):
            df_face = self.openface_data.loc[self.openface_data['frame']==i]
            df_asd = self.asd_data.loc[self.asd_data['frame']==i]
            if (not df_face.empty) and (not df_asd.empty):
                # combine df_face and df_asd
                IOU = np.empty((len(df_face)*2,len(df_asd)*2)); IOU.fill(self.threshold)
                bboxA = df_face[['xmin', 'ymin', 'xmax', 'ymax']]
                bboxB = df_asd[['bbox_xmin', 'bbox_ymin', 'bbox_xmax', 'bbox_ymax']]
                for j in range(len(df_face)): # row
                    IOU[j][:len(df_asd)] = [self.calc_iou(list(bboxA.iloc[j]), list(bboxB.iloc[k])) for k in range(len(df_asd))]
                    '''
                    for k in range(len(df_asd)): # col
                        # calculate IOU
                        IOU[j][k]=self.calc_iou(list(bboxA.iloc[j]), list(bboxB.iloc[k]))
                    '''
                row_ind, col_ind = linear_sum_assignment(-IOU)
                # combine df_face and df_asd by row_ind, col_ind
                idx=0
                asd_dummy[0]=i
                face_dummy[0]=i    
                for j in range(max(len(df_asd),len(df_face))):
                    if idx < len(col_ind) and col_ind[idx] < len(df_asd):
                        left = list(df_asd.iloc[col_ind[idx]])
                    else:
                        left = asd_dummy
                    if idx < len(row_ind) and row_ind[idx] < len(df_face):
                        right = list(df_face.iloc[row_ind[idx]])
                    else:
                        right = face_dummy
                    temp.append(left + right[1:])            
                    idx+=1
        return temp

    
def main(args):
    asd_data = ASDData(args.asd_dir).get()
    
    args.openface_dir = Path(args.openface_dir)
    openface_data = pd.read_csv(args.openface_dir/(args.openface_dir.name+".csv"))
    print(openface_data[:3])
    #print(asd_data)
    
    # cut off the sequence for debug.
    #asd_data = asd_data[:100]
    #openface_data = openface_data[:100]

    bb_matcher = BBMatcher(asd_data, openface_data)
    match = bb_matcher.match()
    
    # output
    
    args.output_dir = Path(args.output_dir)
    
    columns = list(asd_data.columns)+list(openface_data.columns)[1:]
    out = pd.DataFrame(match, columns =columns)    
    out.to_csv(args.output_dir/"openface_asd_pairs.csv", index=False)
    
if __name__ == '__main__':
    main(parser.parse_args())