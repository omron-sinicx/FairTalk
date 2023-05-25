#!/usr/bin/env python
# coding: utf-8

# # Combine the .csv files of TalkNet and OpenFace into one file

# In[ ]:


import pandas as pd
import numpy as np
from scipy.optimize import linear_sum_assignment


# In[2]:


# parameters
file_openface = "./zoom_meeting_720p.csv"
file_talknet = "./out.csv"
file_output = "./combined.csv"
threshold=0.1 # min IOU to determine a combination


# In[ ]:


face = pd.read_csv(file_openface) # OpenFace
asd = pd.read_csv(file_talknet) # TalkNet


# calculate bounding boxes for OpenFace

# In[3]:


# the index of 2d-landmarks
x1,x2,y1,y2=face.columns.get_loc("x_0"),face.columns.get_loc("x_67"),face.columns.get_loc("y_0"),face.columns.get_loc("y_67")
xmin,xmax,ymin,ymax=np.min(face.iloc[:,x1:x2],axis=1),np.max(face.iloc[:,x1:x2],axis=1),np.min(face.iloc[:,y1:y2],axis=1),np.max(face.iloc[:,y1:y2],axis=1)
face['xmin'], face['ymin'], face['xmax'], face['ymax'] = [xmin,ymin,xmax,ymax]


# In[4]:


def bb_intersection_over_union(boxA, boxB, evalCol = False):
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


# combining

# In[46]:


maxframe = max(face["frame"].max(),asd["frame"].max())
temp=[]
asd_dummy = [np.NaN]*len(asd.columns)
face_dummy = [np.NaN]*len(face.columns)

# for i in range(11):
for i in range(maxframe+1):
    df_face = face.loc[face['frame']==i]
    df_asd = asd.loc[asd['frame']==i]
    if (not df_face.empty) and (not df_asd.empty):
        # combine df_face and df_asd
        IOU = np.empty((len(df_face)*2,len(df_asd)*2)); IOU.fill(threshold)
        bboxA = df_face[['xmin', 'ymin', 'xmax', 'ymax']]
        bboxB = df_asd[['bbox_xmin', 'bbox_ymin', 'bbox_xmax', 'bbox_ymax']]
        for j in range(len(df_face)): # row
            for k in range(len(df_asd)): # col
                # calculate IOU
                IOU[j][k]=bb_intersection_over_union(list(bboxA.iloc[j]), list(bboxB.iloc[k]))
        row_ind, col_ind = linear_sum_assignment(-IOU)
        # combine df_face and df_asd by row_ind, col_ind
        idx=0
        asd_dummy[0]=i
        face_dummy[0]=i    
        for j in range(max(len(df_asd),len(df_face))):
            if col_ind[idx] < len(df_asd):
                left = list(df_asd.iloc[col_ind[idx]])
            else:
                left = asd_dummy
            if row_ind[idx] < len(df_face):
                right = list(df_face.iloc[row_ind[idx]])
            else:
                right = face_dummy
            temp.append(left + right[1:])            
            idx+=1
result = temp


# In[47]:


columns = list(asd.columns)+list(face.columns)[1:]
out = pd.DataFrame(result, columns =columns)
out.to_csv(file_output,index=False)


# In[ ]:


# show rows with NaN (face_id and track_id not paired)
is_NaN = df. isnull()
row_has_NaN = is_NaN. any(axis=1)
rows_with_NaN = df[row_has_NaN]
print(rows_with_NaN)

