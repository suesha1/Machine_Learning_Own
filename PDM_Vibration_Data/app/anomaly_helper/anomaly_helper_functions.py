import app.anomaly_helper.utils as utils
import app.anomaly_helper.sound_tools as sound_tools
from .configuration import audio_parameters
import bz2,requests,time,glob,hashlib,json,os
from pydub import AudioSegment
from io import BytesIO
import librosa as lr
import cv2
import matplotlib.pyplot as plt
from .anomaly_model import load_model_anomaly
from .vibration_autoencoder_model import load_model_vibration

import numpy as np
import json
import pandas as pd
import csv
import codecs
import datetime as dt
from keras.models import model_from_json
from sklearn import preprocessing
from sklearn.decomposition import PCA

#Loading important model parameters configurations
config = audio_parameters()

#Loading model to get anomaly MSE score
model = load_model_anomaly(config.input_dims)
vibration_model=load_model_vibration()



'''Funnction to get spectrograms of audio file'''
def get_spectrogram(fileobject1):

	for file1 in fileobject1:
		contents = file1.file.read()
		#recovering the extracted data using pydub module
		sound = AudioSegment.from_raw(BytesIO(contents),sample_width=2,frame_rate=16000,channels=8)
		#upload_folder.close()
		path=os.path.join("app","anomaly_helper","temp_audios","decompress_audio_output.wav")
		#saving the file to the dir using pydub module
		sound.export(path,format="wav")
		y,sr=lr.load(path)
		S = lr.feature.melspectrogram(y, sr=sr, n_mels=config.n_mels)
		log_S = lr.amplitude_to_db(S)
		plt.figure(figsize=(12,4))
		lr.display.specshow(log_S, sr=sr, x_axis='time', y_axis='mel')
		plt.title('Anomaly signal mel power spectrogram: mse 69.0')
		plt.colorbar(format='%+02.0f dB')
		plt.tight_layout()
		path_spec ='temp_spectrogram.png'
		plt.savefig(path_spec)
		# img = cv2.imread(path_spec)
		# img = cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
		break 
	return path_spec


def MahalanobisDist(inv_cov_matrix, mean_distr, data, verbose=False):
    inv_covariance_matrix = inv_cov_matrix
    vars_mean = mean_distr
    diff = data - vars_mean
    md = []
    for i in range(len(diff)):
        md.append(np.sqrt(diff[i].dot(inv_covariance_matrix).dot(diff[i])))
    return md

def MD_threshold(dist, extreme=False, verbose=False):
    k = 3. if extreme else 2.
    threshold = np.mean(dist) * k
    return threshold

'''Function to draw vibration degradation charts from the data using pca model'''
def get_vibration_chart_pca(fileobject1):
	#code
	for file in fileobject1:
		csv_reader = csv.reader(codecs.iterdecode(file.file,'utf-8'))
		rows=[]
		for row in csv_reader:
			rows.append(row)
		df=pd.DataFrame(rows)
		header_row=0
		df.columns = df.iloc[header_row]
		df = df.drop(header_row)
		df['timestamp'] = pd.to_datetime(df[''])
		df = df.set_index(df.columns[5])
		df=df.drop([''], axis = 1)
		scaler = preprocessing.MinMaxScaler()
		X_test = pd.DataFrame(scaler.fit_transform(df),columns=df.columns,index=df.index)
		#df.Mob dist=pd.to_numeric(df.Mob dist)
		pca = PCA(n_components=2, svd_solver= 'full')
		X_test_PCA = pca.fit_transform(X_test)
		X_test_PCA = pd.DataFrame(X_test_PCA)
		X_test_PCA.index = X_test.index
		data_test = np.array(X_test_PCA.values)
		threshold=0.38
		inv_cov_matrix=np.load(os.path.join('.','app','anomaly_helper','vibration_autoencoder_model','inv_cov_matrix.npy'))
		mean_distr=np.load(os.path.join('.','app','anomaly_helper','vibration_autoencoder_model','mean_distr.npy'))
		dist_test = MahalanobisDist(inv_cov_matrix, mean_distr, data_test, verbose=False)
		anomaly = pd.DataFrame()
		anomaly['Mob dist']= dist_test
		anomaly['Thresh'] = threshold
		# If Mob dist above threshold: Flag as anomaly
		anomaly['Anomaly'] = anomaly['Mob dist'] > anomaly['Thresh']
		anomaly.index = X_test_PCA.index
		#print(anomaly.head())
		plt.figure(figsize=(10,6))
        #pf.plot.scatter(x='id',y='age')
		fig=anomaly.plot(logy=True, figsize = (10,6), ylim = [1e-1,1e3], color = ['green','red'],xlabel="Timestamp",ylabel="Mahalanobis_dist").get_figure()
		path_out="vibration_chart.png"
		fig.savefig(path_out)
	return path_out

'''Function to draw vibration degradation charts from the data using autoencoder model'''
def get_vibration_chart_autoencoder(fileobject1):
	for file in fileobject1:
		csv_reader = csv.reader(codecs.iterdecode(file.file,'utf-8'))
		rows=[]
		for row in csv_reader:
			rows.append(row)
		df=pd.DataFrame(rows)
		header_row=0
		#df['timestamp'] = pd.to_datetime(df['0'])
		df.columns = df.iloc[header_row]
		df = df.drop(header_row)
		df['timestamp'] = pd.to_datetime(df[''])
		df = df.set_index(df.columns[5])
		df=df.drop([''], axis = 1)

		scaler = preprocessing.MinMaxScaler()
		X_test = pd.DataFrame(scaler.fit_transform(df),columns=df.columns,index=df.index)
		X_pred = vibration_model.predict(np.array(X_test))
		X_pred = pd.DataFrame(X_pred, 
							  columns=X_test.columns)
		X_pred.index = X_test.index

		scored = pd.DataFrame(index=X_test.index)
		scored['Loss_mae'] = np.mean(np.abs(X_pred-X_test), axis = 1)
		scored['Threshold'] = 0.14
		scored['Anomaly'] = scored['Loss_mae'] > scored['Threshold']
		fig_1=scored.plot(logy=True,  figsize = (10,6), ylim = [1e-2,1e2], color = ['blue','red'],xlabel="Timestamp",ylabel="Loss_mae").get_figure()
		path_out="vibration_chart_autoencoder.png"
		fig_1.savefig(path_out)
		break
	return path_out
		
		
		

'''Function to get model score of audio file features'''
def get_model_prediction(eval_features):

    # Get predictions from our autoencoder:
    prediction = model(eval_features)#.predict(eval_features)['predictions']
    
    # Estimate the reconstruction error:
    mse = np.mean(np.mean(np.square(eval_features - prediction), axis=1))
    return mse





def get_model_anomaly_rate(fileobject1,threshold1):
	mse_list = []
	threshold1 = float(threshold1)
	if threshold1 == 0.0:
		check_threshold = config.default_threshold
	else:
		check_threshold = threshold1


	for file1 in fileobject1:
		contents = file1.file.read()
		sound = AudioSegment.from_raw(BytesIO(contents),sample_width=2,frame_rate=16000,channels=8)
		
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
			anomaly_score = round((reminder1/check_threshold)*100,2)
			if anomaly_score > 100.0:
				mse_list.append({"Anomaly Score": str(100),
					'MSE score':str(round(mse1,2)),
					'status':'Anomalous'})
			else:
				mse_list.append({"Anomaly Score": str(anomaly_score),
					'MSE score':str(round(mse1,2)),
					'status':'Anomalous'})
		else:
			mse_list.append({"Anomaly Score": str(0.0),
				'MSE score':str(round(mse1,2)),
				'status':'Normal'})
	return mse_list
