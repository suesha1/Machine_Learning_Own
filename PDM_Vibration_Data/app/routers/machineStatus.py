from typing import List
import os
from fastapi import FastAPI,APIRouter, File, UploadFile,status,HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from ..machineStatus_helper.status_helper import *
from ..model import query_item
from ..dependencies import MachineStatus_Db
from ..machineStatus_helper.machineStatus_configuration import Db_credentials,machineStatus_params
import shutil,hmac,json,time,hashlib
from io import BytesIO
import bz2,math,struct,wave,librosa as lr
from pydub import AudioSegment
import mysql.connector
from datetime import datetime

db_creds = Db_credentials()

#update_file_transfer_status("False")
sql_db = MachineStatus_Db(db_creds.host,db_creds.user,
	db_creds.password,db_creds.database,db_creds.auth_plugin)

router = APIRouter(
    prefix="/machineStatus",
    tags=["machineStatus"],
    #dependencies=[Depends(verify_token_header)],
    responses={401: {"description": "Not found"}},
)


@router.post("/authenticate/")
def authenticate(mac: str):
	global authentication_queue
	update_rpi_status(mac)
	state=get_file_transfer_status()
	time_stamp=time.time()
	# checking proceed condition
	if mac in authentication_queue.keys() and time_stamp-authentication_queue[mac]>=time_frame_for_each_rpi and  state=="False":
		del authentication_queue[mac]
		return "Proceed"
	#updating if the mac is already in the queue
	elif mac in authentication_queue.keys():
		if time_stamp<authentication_queue[mac]:
			authentication_queue[mac]=time_stamp
		print(authentication_queue)
		return "wait"
	# this is entry of mac into the queue
	else:
		authentication_queue[mac]=time_stamp
		print(authentication_queue)
		return "wait"

@router.post("/uploadfiles/")
async def create_upload_files(api_key : str,mac: str,no_files: int,timestamp: int,files: List[UploadFile] = File(...)):
	global threshhold_machine_on_off
	obj = {
		"mac" : mac,
		"no_files" : no_files,
		"timestamp" : timestamp
	}
	if (validate_sec_key(obj,api_key)) != 0:
		return 0
	if not os.path.isdir('/root/data_sound/' + str(mac)):
		os.makedirs('/root/data_sound/' + str(mac))
	try:
		update_file_transfer_status("True")
		state=get_file_transfer_status()#getting file_transfer_state
		for file in files:
			#opening file using bz2
			f=bz2.open(file.file, "rb")
			#reading the contents
			data=f.read()
			#decompressing the data
			audio_file= bz2.decompress(data)
			upload_folder = '/root/data_sound/' + str(mac)
			#file_object = file.file
			fname = str(mac) + "_" + str(int(time.time())) + '___'
			#recovering the extracted data using pydub module
			sound = AudioSegment.from_raw(BytesIO(audio_file),sample_width=2,frame_rate=frame_rate_compressed,channels=1)
			#upload_folder.close()
			path=os.path.join(upload_folder, fname + file.filename[:-4])
			#saving the file to the dir using pydub module
			sound.export(path+".wav", format="wav")
			print("saved file {}".format(path+".wav"))
			date_time=str(datetime.now())
			file_name=fname +file.filename[:-4]+".wav"
			time_stamp=int(file_name.split("_")[5].split(".")[0]) #getting the timestamp from the filename
			audio_file,sfreq=lr.load(path+".wav") #getting vibrations using librosa module
			rms_score_list=[]
			for i in range(0,len(audio_file),sfreq):
				rms_score=rms(audio_file[i:i+sfreq],sfreq)  #computing the rms score
				rms_score_list.append(rms_score)
				#code to store rms score for every 10 seconds
				if i%(10*sfreq)==0:
					update_rms_score(mac,time_stamp,rms_score) #updating rmsscore for every 10 seconds into the DB
					time_stamp=time_stamp+10
			res_thresh=[i >= threshhold_machine_on_off for i in rms_score_list]
			for i in range(0,len(res_thresh)-threshhold_sec):
				machine_status=get_machine_status(mac)
				threshhold_sec_list_on=[j for j in res_thresh[i:i+threshhold_sec]]
				threshhold_sec_list_off=[not j for j in threshhold_sec_list_on]
				if all(threshhold_sec_list_on) and machine_status in ["OFF",False] : #condition to check machine is ON and previous state is OFF
					status="ON"
					update_machine_status(mac,time_stamp+i,status)
				elif all(threshhold_sec_list_on) and machine_status =="ON": #condition to check machine is ON and update last updated
					update_last_updated(mac,"ON",int(time.time()))
				elif all(threshhold_sec_list_off) and machine_status in ["ON",False] : #condition to check machine is OFF and previous state is ON
					status="OFF"
					update_machine_status(mac,time_stamp+i,status)
				elif all(threshhold_sec_list_off) and machine_status =="OFF":#condition to check machine is OFF and update last updated
					update_last_updated(mac,"OFF",int(time.time()))
			add_log(date_time, str(mac),file_name)
		update_file_transfer_status("False")
	except Exception as ex:
		update_file_transfer_status("False")
		print("exception is {}".format(ex))
	finally:
		update_file_transfer_status("False")
	return {"status": "accepted","filenames": [file.filename[:-4] for file in files]} #sending response as json



@router.post("/get_machine_uptime/")
async def get_machine_uptime(mac: str,from_time: int,to_time: int):
	res=get_machine_status_score(mac,from_time,to_time) #getting all statuses of the given mac along with timestamp in the given from time and to time
	status_dict=dict(res)
	status_dict_keys=list(status_dict.keys())
	#print(status_dict_keys)
	start_time=0
	uptime=0
	if to_time-from_time<0:
		print("{In valid from_time and to_time}")
		return "{In valid from_time and to_time}"
	if len(status_dict_keys)==0: #condition for no records in the database
		print("{Details Not Found}")
		return "{Details Not Found}"
	elif len(status_dict_keys)==1: #conditon for if it has only one record
		if status_dict[status_dict_keys[0]]=="ON": #if that record is ON
			if status_dict_keys[0]>from_time:
				start_time=status_dict_keys[0]
			else:
				start_time=from_time
		elif status_dict[status_dict_keys[0]]=="OFF":# if that record iS OFF
			if get_no_of_records_machine(mac)>1 and from_time<status_dict_keys[0]: #if it has > 1 record of that machine then we consider it turned OFF before state is ON
				uptime= status_dict_keys[0] - from_time
				return {"uptime":uptime}
			else:
				return {"uptime":uptime}
		uptime=to_time-start_time
	elif len(status_dict_keys)>1:#condition if it has more than one record (it will consider many states)
		for i in status_dict_keys:
			if status_dict[i]=="OFF" and start_time==0: # Condition for OFF state
				#if status_dict_keys.index(i)==0:#if that record is first record
				#	uptime=i-from_time
				#else:
				continue
			if start_time!=0 and status_dict[i]=="ON":#conditon if come across OFF
					start_time=i
			if start_time==0 and status_dict[i]=="ON":#condition if it is FIrst ON
				if i<from_time:
					start_time=i
				elif i>from_time and i<to_time:
					start_time=i
				else:
					start_time=from_time
			if start_time!=0 and status_dict[i]=="OFF":# when we come across OFF
				uptime = uptime + i - start_time
			elif start_time!=0 and status_dict[i]=="ON" and status_dict_keys.index(i)==len(status_dict_keys)-1: #if it is the last record ON
				uptime = uptime + to_time - start_time
	print(mac,uptime)
	resp={"uptime":uptime} #structuring the response as json
	return resp



@router.get("/get_machine_status_details")
def get_machine_status_details(req: query_item):
	mac=req.mac
	size=req.size
	sql_db.connect_db()
	db = sql_db.get_db_obj()
	if mac not in get_mac_ids_status():
		return {"we couldnt found this mac_id {}".format(mac)}
	cursor=db.cursor()
	sql="select * from sound_api_machine_status where MAC_address=\"{}\" LIMIT {};".format(mac,size) #query to get all the records from sound_api_machine_status
	cursor.execute(sql) 
	result = cursor.fetchall()
	res=[]
	for i in result:
		row={"time_stamp":i[2],"status":i[3],"last_updated":i[4]}# structuring the response as json
		res.append(row)
	db.close()
	response={"mac_id":mac,"machine_status_details":res} #structuring the response as json
	return response
@router.get("/get_mac_ids/")
def get_mac_ids():
	mac_ids=get_mac_ids_status()
	return {"mac_ids":mac_ids}
@router.get("/get_rpi_live/")
def get_rpi_live():
	sql_db.connect_db()
	db = sql_db.get_db_obj()
	cursor=db.cursor()
	sql="SELECT MAC_address , last_pinged FROM sound_api_rpi_status;"# query to get details from sound_api_rpi_status
	cursor.execute(sql) 
	result = cursor.fetchall()
	res=[]
	for i in result:
		time_now=int(time.time())
		if abs(time_now-i[1])>300: #checking if the last known time_stamp is more than 300 seconds
			row={"rpi_mac_id":i[0],"status":"OFF"}
		else:
			row={"rpi_mac_id":i[0],"status":"ON"}
		res.append(row)
	return res

@router.post("/report/")
async def report(api_key: str, mac: str,timestamp: int,report: str):
	obj = {
		"mac" : mac,
		"timestamp" : timestamp
	}
	if (validate_sec_key(obj,api_key)) != 0:
		return 0
	# Add here about saving all reports to database(report is mainly while checking card ids)
	sql_db.connect_db()
	db = sql_db.get_db_obj()
	cursor=db.cursor()
	sql = "INSERT INTO sound_api_report_errors ( MAC_address,Time_Stamp,report) VALUES (%s, %s,%s)" #inserting reports to database
	val = (mac,time_stamp,report)
	cursor.execute(sql, val)
	db.commit() # commiting the transaction
	db.close()
	return {"status": "accepted"}