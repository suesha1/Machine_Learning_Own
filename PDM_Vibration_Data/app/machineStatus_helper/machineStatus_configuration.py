class Db_credentials():
	host = "localhost"
	user = "root"
	password = "password"
	database = "sound_api"
	auth_plugin = "mysql_native_password"

class machineStatus_params():
	threshhold_machine_on_off=1.4 #thresh hold for machine RMS score per second
	threshhold_sec=3 #threshhold for number of seconds it is up
	authentication_queue=dict()
	time_frame_for_each_rpi=110
	frame_rate_compressed=12000