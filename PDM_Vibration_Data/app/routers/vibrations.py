from typing import List
from fastapi import APIRouter,FastAPI, File, Form,UploadFile
from fastapi.responses import HTMLResponse,FileResponse
from ..anomaly_helper import utils,sound_tools
from ..anomaly_helper.anomaly_helper_functions import get_vibration_chart_pca,get_vibration_chart_autoencoder
import bz2,requests,time,glob,hashlib,json,os
from io import BytesIO
import librosa as lr
import json
import hmac
from pydantic import BaseModel



# FastAPI router
router = APIRouter(
    prefix="/vibrations",
    tags=["vibrations"],
    # dependencies=[Depends(verify_token_header)],
    responses={401: {"description": "Not found"}},
)

#Get Vibration Chart PCA
'''This post request receives the vibration signals data file in csv format 
and returns the vibration degradation chart of that file based on PCA model'''
@router.post("/getVibrationChartPca/")
async def get_vibration_chart_Pca(files: List[UploadFile] = File(...),summary = 
    'Vibration Degradation Chart API for anomaly detection, Return the vibration chart upon receiving vibartion signals file based on PCA model.',
    description = 'Input: Vibration Signal CSV file , Format SpooledTemporaryFile '+
    'Output: PNG bytes response'):
	vib_img_return = get_vibration_chart_pca(files)
	return FileResponse(vib_img_return)

'''This post request receives the vibration signals data file in csv format 
and returns the vibration degradation chart of that file based on autoencoder model'''
@router.post("/getVibrationChartAutoencoder/")
async def get_vibration_chart_Autoencoder(files: List[UploadFile] = File(...),summary = 
    'Vibration Degradation Chart API for anomaly detection, Return the vibration chart upon receiving vibartion signals file based on autoencoder model.',
    description = 'Input: Vibration Signal CSV file , Format SpooledTemporaryFile '+
    'Output: PNG bytes response'):
	vib_img_return = get_vibration_chart_autoencoder(files)
	return FileResponse(vib_img_return)
   


