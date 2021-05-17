from fastapi import FastAPI,WebSocket
from fastapi.responses import HTMLResponse
import boto3
import cv2
import os
import natsort
import time
import botocore
import numpy as np
import matplotlib.pyplot as plt
#import requests
import asyncio
import requests


fc_count=1

   

def compare_faces(sourceFile, targetFile):
    global fc_count
    client=boto3.client('rekognition')
    try:
         imageSource=open(sourceFile,'rb')
         imageTarget=open(targetFile,'rb')
         response=client.compare_faces(SimilarityThreshold=0.1,
                                  SourceImage={'Bytes': imageSource.read()},
                                  TargetImage={'Bytes': imageTarget.read()})

    except botocore.exceptions.ClientError as error:
        pass
        return 0
    

  
    srcimg=cv2.imread(sourceFile)
   
    img=cv2.imread(targetFile)
    #print(img.shape)
    imgHeight, imgWidth,n=srcimg.shape
    #sourceimg and targetimg must be of same shape
    img=cv2.resize(img, (imgWidth, imgHeight),interpolation = cv2.INTER_NEAREST)
    #print(imgWidth)
    #print(imgHeight)
  
    face_matched_count=0
    face_notmatched_count=0
    for faceMatch in response['FaceMatches']:

        if len(response['FaceMatches'])>0:
            position = faceMatch['Face']['BoundingBox']
            similarity=str(int(faceMatch['Similarity']))
            #similarity = str(faceMatch['Similarity'])
        
            width=int(position['Width']*imgWidth)
            height=int(position['Height']*imgHeight)
            top=int(position['Top']*imgHeight)
            left=int(position['Left']*imgWidth)
         
            cv2.rectangle(img,(left,top),(left + width, top + height),(255,255,255),3)
            print('The face at ' +
                   str(position['Left']) + ' ' +
                   str(position['Top']) +
                   ' matches with ' + similarity + '% confidence')
   
            text1="Similar: {}%".format(similarity)
            cv2.putText(img,text1,(left,top-3),cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 4)
            text="Target_Img:"
            cv2.putText(img,text,(6,44),cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 0), 3)
          
            face_matched_count=face_matched_count+1
            #print(face_matched_count)
            #print(face_notmatched_count)
            h_img = cv2.hconcat([srcimg, img])
            text2="Source_Image:"
            cv2.putText(h_img,text2,(6,44),cv2.FONT_HERSHEY_SIMPLEX,2, (255, 255,0 ), 3)  
            
            cv2.imwrite("data\\output_frame\\frame_%d.jpg" % fc_count,h_img)
            imageSource.close()
            imageTarget.close()
            return len(response['FaceMatches']),h_img   
       
            
               
    
        


    




source_file="data\\my_photo.jpeg"

def main():

    global fc_count
    frame_list=[]
    fc_match=0
    cap = cv2.VideoCapture("data\\my_video.mp4")
    fps = cap.get(cv2.CAP_PROP_FPS)
    print(fps)
    #cap.set(cv2.CAP_PROP_FPS, int(112))
    #fps = cap.get(cv2.CAP_PROP_FPS)
    #print(fps)
    length = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(length)
    
    FrameSize=(960,540)
    fourcc = cv2.VideoWriter_fourcc(*'XVID')

    out = cv2.VideoWriter('data\\output.mp4', fourcc, fps, FrameSize)

    while(cap.isOpened()):
        # Capture frame-by-frame
        ret, frame = cap.read()
        
        if not ret: break
        
        
        if fc_count%1==0:
            
            #save each frame as image 
            frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
            cv2.imwrite("data\\temp.jpg",frame)
            target_file="data\\temp.jpg"
            fc_match,out_frame=compare_faces(source_file,target_file)
            height,width,n=out_frame.shape
            if  out_frame is None:
                 break
            new_frame=cv2.resize(out_frame,(960,540))
            out.write(new_frame)
	   
           
        fc_count=fc_count+1         
        if cv2.waitKey(5) & 0xFF == ord('q'):
            break
    cap.release()
    out.release()
    cv2.destroyAllWindows()
    
if __name__ == "__main__":
    main()
  

   

    
        
        

    
        
    




