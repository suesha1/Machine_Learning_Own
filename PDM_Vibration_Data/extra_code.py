

Request code
========================


import requests
import time
import hmac
from uuid import getnode as get_mac
import glob
import hashlib
import json
import os
import bz2
from pydub import AudioSegment


#sampleaudio_path = 'http://127.0.0.1:8000/getAnomaly'
# sound = AudioSegment.from_wav(train_files[0])
# sound.export(file, format='wav', parameters=["-ac","2","-ar",sample_rate])
#files = ['E:\\Code\\MRC Ventures\\Predictive maintenance\\ANOMALY DETECTION API\\Air compressor 1.wav']
#files = ['/media/mrc/Data/Usman_dev/Sound Anomaly Detection/Anomaly Detection Api/00000002.wav']
files = ['E:\\Code\\MRC Ventures\\Predictive maintenance\\ANOMALY DETECTION API\\Air compressor 1.wav']
#tn_files[:5]
send_files_list = []
#send_file = open(file, 'rb')#.read()
counter=0
for file1 in files:
    #print(file1)
    tarbz2contents = bz2.compress(open(file1, 'rb').read(), 9)
    filepath1 = str(counter)+"temp.bz2"
    #dumping the comressed content into bz2 files
    f = bz2.open(filepath1, "wb") #opening the file
    f.write(tarbz2contents)#writing content into file
    f.close()#closing file
    bz2_file = open(filepath1,'rb')
    send_files_list.append(('files',bz2_file))
    counter+=1
url = 'http://18.141.173.166:5000/anomaly/anomaly/getAnomaly/?'
#url = "http://127.0.0.1:8000/anomaly/anomaly/getAnomaly/?"
payload = '2.0'
url = url + 'threshold=' + payload
response = requests.request("POST", url, headers={}, data = {}, files = send_files_list)
json.loads(response.json())
#print(response.json())




Receiveing code
==========================

'''This function gets audio file objects, threshold and return status of audio clip''' 
def get_model_anomaly_rate(fileobject1,threshold1):
	mse_list = []
	threshold1 = float(threshold1)
	if threshold1 == 0.0:
		check_threshold = config.default_threshold
	else:
		check_threshold = threshold1


	for file1 in fileobject1:

		f=bz2.open(file1.file, "rb")
		print(file1.filename)
		#reading the contents
		data=f.read()
		#decompressing the data
		audio_file= bz2.decompress(data)
		#recovering the extracted data using pydub module
		sound = AudioSegment.from_raw(BytesIO(audio_file),sample_width=2,frame_rate=16000,channels=8)
		print(len(sound))
		sound = sound[:16000*10]
		#upload_folder.close()
		path=os.path.join("app","anomaly_helper","temp_audios","decompress_audio_output_for_model.wav")
		#saving the file to the dir using pydub module
		sound.export(path,format="wav")

		signal, sr = sound_tools.load_sound_file(path)
		eval_features=sound_tools.extract_signal_features(signal,sr,frames=config.n_frames,n_fft=config.n_fft,hop_length=config.hop_length)
		mse1 = get_model_prediction(eval_features)
 
		if mse1 >= check_threshold:
			reminder1 = mse1 - check_threshold
			anomalys_score = round((reminder1/check_threshold)*100,2)
			mse_list.append({file1.filename: str(anomalys_score),
				'MSE score':str(round(mse1,2)),
				'status':'Anomalous'})
		else:
			mse_list.append({file1.filename: str(0.0),
				'MSE score':str(round(mse1,2)),
				'status':'Normal'})
	return mse_list
