import pickle
from pathlib import Path
import pandas as pd
import numpy as np
import argparse
from scipy.optimize import linear_sum_assignment
import joblib
from timer import Timer

parser = argparse.ArgumentParser(description='combine outputs by TalkNet-ASD and OpenFace into scene-wise files')


parser.add_argument('-a', '--asd_dir', type=str, default="./data/train/train_vimeo_410316487",
                    help='Set the directory where a result of active speaker detection (ASD) is.')
parser.add_argument('-f', '--openface_dir', type=str, default="./data/openface_features/train/train_vimeo_410316487",
                    help='Set the directory where the OpenFace features are. OpenFace feature file should be the same name as its folder.')
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
        
#     def get(self): # this function is replaced by a faster one with the same name, but I kept this for its readability
#         d,df=[],[]
#         scene_count=-1
#         for i in range(len(self.tracks)):
#             # if the start frame of a track == the start frame of a scene, the scene_id+=1
#             #print("track:", i, "start frame:",self.tracks[i]['track']['frame'][0])
#             while scene_count+1 < len(self.scene_ids) and self.tracks[i]['track']['frame'][0] >= self.scene_ids[scene_count+1]:
#                 scene_count+=1
#                 #print("scene is now", scene_count)
#             d.append({'frame':self.tracks[i]['track']['frame'], 
#                       'scene_id':scene_count,
#                       'track_id':i,
#                       'ASDscore':np.append(0, self.scores[i]).round(decimals=1), # len(scoredata) = len(data)-1, so add 0 at the head
#                       'bbox_xmin':self.tracks[i]['track']['bbox'][:,0].astype(int), 
#                       'bbox_ymin':self.tracks[i]['track']['bbox'][:,1].astype(int), 
#                       'bbox_xmax':self.tracks[i]['track']['bbox'][:,2].astype(int),
#                       'bbox_ymax':self.tracks[i]['track']['bbox'][:,3].astype(int)})

#             df.append(pd.DataFrame(data=d[i]))
#         result = pd.concat(df)
#         return result.sort_values(by=["frame", "track_id"])   
    
    def get(self):
        scene_ids = self.scene_ids
        tracks = self.tracks
        
        track_frames = np.array([track['track']['frame'][0] for track in tracks])
        scene_count = np.searchsorted(scene_ids, track_frames, side='right') - 1

        d = {
            'frame': np.concatenate([track['track']['frame'] for track in tracks]),
            'scene_id': np.repeat(scene_count, [len(track['track']['frame']) for track in tracks]),
            'track_id': np.arange(len(tracks)).repeat([len(track['track']['frame']) for track in tracks]),
            'ASDscore': np.concatenate([np.append(0, score).round(decimals=1) for score in self.scores]),
            'bbox_xmin': np.concatenate([track['track']['bbox'][:, 0].astype(int) for track in tracks]),
            'bbox_ymin': np.concatenate([track['track']['bbox'][:, 1].astype(int) for track in tracks]),
            'bbox_xmax': np.concatenate([track['track']['bbox'][:, 2].astype(int) for track in tracks]),
            'bbox_ymax': np.concatenate([track['track']['bbox'][:, 3].astype(int) for track in tracks]),
        }

        result = pd.DataFrame(data=d)
        result.sort_values(by=["frame", "track_id"], inplace=True)
        result.reset_index(drop=True, inplace=True)
        return result
   
    
class BBMatcher():
    def __init__(self, asd_data, openface_data, threshold=0.1):
        self.asd_data = asd_data
        self.openface_data = openface_data
        self.threshold = threshold # min IOU to determine a combination
    
        xmin, xmax, ymin, ymax = self.get_of_minmax()
        # the index of 2d-landmarks
        self.openface_data['xmin'] = xmin
        self.openface_data['ymin'] = ymin
        self.openface_data['xmax'] = xmax
        self.openface_data['ymax'] = ymax
            
    
    @staticmethod
    def calc_iou(boxA, boxB):
        # CPU: IOU Function to calculate overlap between two image
        assert boxA[2] >= boxA[0]
        assert boxA[3] >= boxA[1]
        assert boxB[2] >= boxB[0]
        assert boxB[3] >= boxB[1]
        
        xA = max(boxA[0], boxB[0]) # xmin
        yA = max(boxA[1], boxB[1]) # ymin
        xB = min(boxA[2], boxB[2]) # xmax
        yB = min(boxA[3], boxB[3]) # ymax
        interArea = max(0, xB - xA + 1) * max(0, yB - yA + 1)
        boxAArea = (boxA[2] - boxA[0] + 1) * (boxA[3] - boxA[1] + 1)
        boxBArea = (boxB[2] - boxB[0] + 1) * (boxB[3] - boxB[1] + 1)
        
        iou = interArea / float(boxAArea + boxBArea - interArea)
        assert iou >= 0.0
        assert iou <= 1.0
        return iou    
    
    def get_of_minmax(self):
        x1 = self.openface_data.columns.get_loc("x_0")
        x2 = self.openface_data.columns.get_loc("x_67")
        y1 = self.openface_data.columns.get_loc("y_0")
        y2 = self.openface_data.columns.get_loc("y_67")
        return np.min(self.openface_data.iloc[:,x1:x2+1],axis=1), np.max(self.openface_data.iloc[:,x1:x2+1],axis=1),  \
                np.min(self.openface_data.iloc[:,y1:y2+1],axis=1), np.max(self.openface_data.iloc[:,y1:y2+1],axis=1)

    @staticmethod
    def _match_inner_inner(i:int, idx:int, col_ind, df_asd, row_ind, df_face, asd_dummy, face_dummy):
            if idx < len(col_ind) and col_ind[idx] < len(df_asd):
                left = list(df_asd.iloc[col_ind[idx]])
            else:
                left = asd_dummy
            if idx < len(row_ind) and row_ind[idx] < len(df_face):
                right = list(df_face.iloc[row_ind[idx]])
            else:
                right = face_dummy
            return left + right[1:]
        
    @staticmethod
    def _match_inner(i, df_face, df_asd, asd_dummy, face_dummy, threshold):
        if df_face.empty or df_asd.empty:
            return None
        IOU = np.empty((len(df_face)*2,len(df_asd)*2));
        IOU.fill(threshold)
        bboxA = df_face[['xmin', 'ymin', 'xmax', 'ymax']]
        bboxB = df_asd[['bbox_xmin', 'bbox_ymin', 'bbox_xmax', 'bbox_ymax']]
        
        IOU[:len(df_face), :len(df_asd)] = [[BBMatcher.calc_iou(list(bboxA.iloc[j]), list(bboxB.iloc[k])) for k in range(len(df_asd))] for j in range(len(df_face))]
        row_ind, col_ind = linear_sum_assignment(-IOU)
        # combine df_face and df_asd by row_ind, col_ind
        asd_dummy[0]=i
        face_dummy[0]=i
        return [BBMatcher._match_inner_inner(i,j, col_ind, df_asd, row_ind, df_face, asd_dummy, face_dummy) for j in range(max(len(df_asd),len(df_face)))]
    
    @staticmethod
    def flatten(matrix):
        return [x for row in matrix for x in row]

    def match(self):
        maxframe = max(self.openface_data["frame"].max(),self.asd_data["frame"].max())
        asd_dummy = [np.NaN]*len(self.asd_data.columns)
        face_dummy = [np.NaN]*len(self.openface_data.columns)
        
        #print(maxframe)
        result = joblib.Parallel(n_jobs=-1)(joblib.delayed(self._match_inner)(
            i,
            self.openface_data.loc[self.openface_data['frame']==i],
            self.asd_data.loc[self.asd_data['frame']==i],
            asd_dummy,
            face_dummy,
            self.threshold
        ) for i in range(maxframe+1))
        result = filter(lambda x: x!=None, result)
        result = self.flatten(result)
        #print(len(result), len(result[0]))

        return result
    
    def match_slow(self):
        maxframe = max(self.openface_data["frame"].max(),self.asd_data["frame"].max())
        temp=[]
        asd_dummy = [np.NaN]*len(self.asd_data.columns)
        face_dummy = [np.NaN]*len(self.openface_data.columns)

        #print(maxframe)
        for i in range(maxframe+1):
            df_face = self.openface_data.loc[self.openface_data['frame']==i]
            df_asd = self.asd_data.loc[self.asd_data['frame']==i]
            if (not df_face.empty) and (not df_asd.empty):
                # combine df_face and df_asd
                IOU = np.empty((len(df_face)*2,len(df_asd)*2)); IOU.fill(self.threshold)
                bboxA = df_face[['xmin', 'ymin', 'xmax', 'ymax']]
                bboxB = df_asd[['bbox_xmin', 'bbox_ymin', 'bbox_xmax', 'bbox_ymax']]
                IOU[:len(df_face), :len(df_asd)] = [[self.calc_iou(list(bboxA.iloc[j]), list(bboxB.iloc[k])) for k in range(len(df_asd))] for j in range(len(df_face))]
                row_ind, col_ind = linear_sum_assignment(-IOU)
                # combine df_face and df_asd by row_ind, col_ind
                idx=0
                asd_dummy[0]=i
                face_dummy[0]=i    
                for j in range(max(len(df_asd),len(df_face))): # loop for the times of max number of face in df_asd and df_face
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
        #print(len(temp), len(temp[0]))
        return temp

    
def main(args):
    t = Timer()
    asd_data = ASDData(args.asd_dir).get()    
    t.check("asd_data get")
    args.openface_dir = Path(args.openface_dir)
    openface_data = pd.read_csv(args.openface_dir/(args.openface_dir.name+".csv"))
    t.check("openface_data get")

    bb_matcher = BBMatcher(asd_data, openface_data)
    t.check("bb_matcher construction get")
    match = bb_matcher.match()
    t.check("match get")
    match_check = bb_matcher.match_slow()
    t.check("match_slow? get")
    
    for i in range(len(match)):
        for j in range(len(match[0])):
            if match[i][j]!=match_check[i][j]:
                print("error at ({},{}): {} != {}".format(i,j,match[i][j], match_check[i][j]))                      
                      
    # assert(match==match_check) this assertion does not work since nan==nan always false.
    
    # output
    args.output_dir = Path(args.output_dir)
    
    columns = list(asd_data.columns)+list(openface_data.columns)[1:]
    t.check("concat columns")
    out = pd.DataFrame(match, columns =columns)    
    t.check("convert to pandas data frame")
    out.to_csv(args.output_dir/"openface_asd_pairs.csv", index=False)
    t.check("save")
    
if __name__ == '__main__':
    main(parser.parse_args())