from typing import List
from fastapi import APIRouter,FastAPI, File, Form,UploadFile
from fastapi.responses import HTMLResponse,FileResponse
from ..anomaly_helper import utils,sound_tools
from ..anomaly_helper.configuration import audio_parameters
from ..anomaly_helper.anomaly_helper_functions import get_spectrogram,get_model_anomaly_rate
import bz2,requests,time,glob,hashlib,json,os
from pydub import AudioSegment
from io import BytesIO
import librosa as lr
import json
import hmac
from pydantic import BaseModel

#initializing important parameters class instance to access the important parameter values
conf = audio_parameters()



# FastAPI router
router = APIRouter(
    prefix="/anomaly",
    tags=["anomaly"],
    # dependencies=[Depends(verify_token_header)],
    responses={401: {"description": "Not found"}},
)


'''This post request receives the audio file in compressed format 
and returns the simple spectogram of that file'''
@router.post("/spectrogram/")
async def post_spectrogram(files: List[UploadFile] = File(...), summary = 
    'Audio spectrogram API, Return the spectrogram upon receiving audio file.',
    description = 'Input: Audio file , Format SpooledTemporaryFile '+
    'Output: PNG bytes response'):
	spec_img_return = get_spectrogram(files)
	return FileResponse(spec_img_return)


'''This post requests gets the  list of audio files and return anomaly scores of each audio file
This function calls the ***get_model_anomaly function which decompressed the file 
and return anomaly health score''' 
@router.post("/getAnomaly/")
async def post_anomaly_score(threshold: str,files: List[UploadFile] = File(...), summary = 
    'Anomaly score API, Send back anomaly score of list of audio files.',
    description = 'Receive list of audio files assuming each of 10 seconds and also threshold. Return the anomaly scores '+
    'along with MSE error score and status if the audio contains anomaly or it is normal. - (Anomalous,Normal)'+
    '\n Input: threshold str - (0.0 or float value) if 0.0 means use default threshold to decide based on MSE value'):
	
	#return {"th1",threshold}
	json_string = json.dumps(get_model_anomaly_rate(files,threshold))
	return json_string

