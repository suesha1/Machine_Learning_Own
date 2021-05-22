from typing import List
import os
from fastapi import FastAPI, File, UploadFile,status,HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import shutil
import hmac
import json
import time
import hashlib
from io import BytesIO
import bz2
from pydub import AudioSegment
import mysql.connector
from datetime import datetime
import librosa as lr
import math
import struct
import wave
from ..dependencies import MachineStatus_Db
from .machineStatus_configuration import Db_credentials,machineStatus_params
db_creds = Db_credentials()

#update_file_transfer_status("False")
sql_db = MachineStatus_Db(db_creds.host,db_creds.user,
	db_creds.password,db_creds.database,db_creds.auth_plugin)


ms_config = machineStatus_params()

threshhold_machine_on_off=ms_config.threshhold_machine_on_off #thresh hold for machine RMS score per second
threshhold_sec=ms_config.threshhold_sec #threshhold for number of seconds it is up
authentication_queue=ms_config.authentication_queue
time_frame_for_each_rpi=ms_config.time_frame_for_each_rpi
frame_rate_compressed=ms_config.frame_rate_compressed


sec_key = b'5ibO5CxZ4Mdg8Ooc3c2KCNS4OZBm0IWmmzphGrA6'

def rms(frame,swidth): # formula for rms score

    sum_squares = 0.0
    for n in frame: 
        sum_squares += n*n
    # compute the rms 
    rms = math.pow(sum_squares/swidth,0.5);
    return rms * 1000

def validate_sec_key(obj,api_key): # function to validate secret key hmac
	payload = json.dumps(obj,separators=(',', ':'))
	sign = hmac.new(sec_key, json.dumps(payload,separators=(',', ':')).encode('utf-8'), hashlib.sha512).hexdigest()
	if sign != api_key:

		obj['status'] = "Failed:API key Invalid"
		# Record logs to database

		raise HTTPException(
	        status_code=status.HTTP_401_UNAUTHORIZED,
	        detail="Invalid API Key",
	    )
		return -1
	else:
		return 0
def get_file_transfer_status():
	sql_db.connect_db()
	db = sql_db.get_db_obj()

	cursor=db.cursor()
	cursor.execute("SELECT status FROM file_transfer_state WHERE id=1") #query to get file transfer state
	result = cursor.fetchall()
	for x in result:
		status=x[0]
		break
	db.close()
	return status #returning status
def update_file_transfer_status(value): #function to update file transfer state for scheduling
	
	sql_db.connect_db()
	db = sql_db.get_db_obj()
	
	cursor=db.cursor()
	sql="UPDATE file_transfer_state SET status =%s WHERE id= %s" # updating the status value to true and false
	val=(value,1)
	cursor.execute(sql, val)
	db.commit() # commiting the transaction
	db.close()
def add_log(date_time, mac_address,filename):#function to log the recocrds to database
	sql_db.connect_db()
	db = sql_db.get_db_obj()
	cursor=db.cursor()
	sql = "INSERT INTO sound_api_log (Date_Time, MAC_address,Filename) VALUES (%s, %s,%s)" #inserting logs to database
	val = (date_time, mac_address,filename)
	cursor.execute(sql, val)
	db.commit() # commiting the transaction
	db.close()
def update_rms_score(mac,time_stamp,rms_score): #function to update rms score to table
	
	sql_db.connect_db()
	db = sql_db.get_db_obj()
	
	cursor=db.cursor()
	sql = "INSERT INTO sound_api_rms_score ( MAC_address,Time_Stamp,RMS_Score) VALUES (%s, %s,%s)" #inserting rms score to database
	val = (mac,time_stamp,rms_score)
	cursor.execute(sql, val)
	db.commit() # commiting the transaction
	db.close()


def get_rms_score(mac,from_time,to_time): # function to get rms score for mac
	
	sql_db.connect_db()
	db = sql_db.get_db_obj()
	cursor=db.cursor()
	sql = "SELECT RMS_Score FROM sound_api_rms_score WHERE MAC_address={} AND Time_Stamp >{} AND Time_Stamp <{} ;".format(mac,from_time,to_time) #query to get rms score
	cursor.execute(sql) 
	result = cursor.fetchall()
	res=[]
	for x in result:
		res.append(x[0]) #appending the data
	db.close()
	return res
def get_machine_status(mac): # get last updated machine status of a machine 
	
	sql_db.connect_db()
	db = sql_db.get_db_obj()
	
	cursor=db.cursor()
	sql="SELECT status from sound_api_machine_status where MAC_address={} AND Time_Stamp = (SELECT max(Time_Stamp) FROM sound_api_machine_status where MAC_address={})".format(mac,mac) #query to get machine status
	cursor.execute(sql) 
	result = cursor.fetchall()
	res=None
	if len(result)==0:
		return False #return flase if there is no response
	else:
		for x in result:
			res=x[0]
			break;
	db.close()
	return res
def update_machine_status(mac,time_stamp,status): #function to update the machine status
	
	sql_db.connect_db()
	db = sql_db.get_db_obj()
	
	cursor=db.cursor()
	sql = "INSERT INTO sound_api_machine_status ( MAC_address,Time_Stamp,status,last_updated) VALUES (%s, %s,%s,%s)" #inserting logs to database
	val = (mac,time_stamp,status,int(time.time()))
	cursor.execute(sql, val)
	db.commit() # commiting the transaction
	db.close()

def get_machine_status_score(mac,from_time,to_time):#function to get machine statuses within the time frame
	sql_db.connect_db()
	db = sql_db.get_db_obj()
	cursor=db.cursor()
	#query to get machine statuses within the time frame
	sql="SELECT Time_Stamp,status from sound_api_machine_status  WHERE MAC_address={} AND Time_Stamp >={} AND Time_Stamp <={} ORDER BY Time_Stamp ASC ;".format(mac,from_time,to_time)
	cursor.execute(sql) 
	result = cursor.fetchall()
	res=[]
	for i in result:
		res.append(i)
	db.close()
	return res
def update_last_updated(mac,status,time_stamp):#function to update last updated column in machine_status
	sql_db.connect_db()
	db = sql_db.get_db_obj()	
	#print(mac,status,time_stamp)
	cursor=db.cursor()
	max_id_sql="SELECT max(Time_Stamp) FROM sound_api_machine_status where MAC_address={} AND status =\"{}\"".format(mac,status) #query to get the Timestamp last record/status of the machine 
	cursor.execute(max_id_sql) 
	result = cursor.fetchall()
	for i in result:
		max_id=i[0]
	sql="UPDATE sound_api_machine_status SET last_updated = {} WHERE Time_Stamp = {} AND MAC_address={};".format(time_stamp,max_id,mac) #updating the last updated of the last known status of the mahine 
	cursor.execute(sql)
	db.commit() # commiting the transaction
	db.close()

def get_mac_ids_status():#function to get unique mac ids from sound_api_machine_status
	sql_db.connect_db()
	db = sql_db.get_db_obj()
	cursor=db.cursor()
	sql="SELECT DISTINCT MAC_address From sound_api_machine_status;"
	cursor.execute(sql) 
	result = cursor.fetchall()
	res=[]
	for i in result:
		res.append(i[0])
	db.close()
	return res

def get_no_of_records_machine(mac):#function to get number of records in the database
	sql_db.connect_db()
	db = sql_db.get_db_obj()
	cursor=db.cursor()
	sql="SELECT count(*) from sound_api_machine_status where MAC_address=\"{}\"".format(mac) #query to get number of records are there in the table for a given mac
	cursor.execute(sql) 
	result = cursor.fetchall()
	for i in result:
		res=i[0]
		break
	db.close()
	return res
def get_all_rpis():#function to get all registered rpis
	sql_db.connect_db()
	db = sql_db.get_db_obj()
	cursor=db.cursor()
	sql="SELECT DISTINCT MAC_address FROM sound_api_rpi_status;" #query to get distinct macids from sound_api_rpi_status
	cursor.execute(sql) 
	result = cursor.fetchall()
	res=[]
	for i in result:
		res.append(i[0])
	db.close()
	return res

def update_rpi_status(mac):#function to update rpi status
	rpis=get_all_rpis()
	sql_db.connect_db()
	db = sql_db.get_db_obj()
	cursor=db.cursor()
	if mac in rpis:
		sql="UPDATE sound_api_rpi_status SET last_pinged={} where MAC_address=\"{}\"".format(int(time.time()),mac) #updating rpi status if it already registered
		cursor.execute(sql)
	else:
		sql="INSERT INTO sound_api_rpi_status (MAC_address,last_pinged) VALUES (%s, %s)"#inserting rpis to database for the first time
		val = (mac,int(time.time()))
		cursor.execute(sql,val)
	db.commit() # commiting the transaction
	db.close()