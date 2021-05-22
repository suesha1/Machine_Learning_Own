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





sampleaudio_path = 'http://127.0.0.1:8000/spectrogram'
# sound = AudioSegment.from_wav(train_files[0])
# sound.export(file, format='wav', parameters=["-ac","2","-ar",sample_rate])
file = train_files[0]
tarbz2contents = bz2.compress(open(file, 'rb').read(), 9)
#dumping the comressed content into bz2 files
f = bz2.open("temp1.bz2", "wb") #opening the file
f.write(tarbz2contents)#writing content into file
f.close()#closing file
bz2_file = open("temp1.bz2",'rb')
url = 'http://127.0.0.1:8000/spectrogram'
response = requests.request("POST", url, headers={}, data = {}, files = [('files',bz2_file)])
#print(response.file)
#response.content
file = open("sample_image.png", "wb")
file.write(response.content)
file.close()
import cv2
import matplotlib.pyplot as plt
img = cv2.imread("sample_image.png")
plt.imshow(img)
plt.grid(False)






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
files = ['/media/mrc/Data/Usman_dev/Sound Anomaly Detection/Anomaly Detection Api/00000002.wav']
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
#url = 'http://18.141.173.166:5000/getAnomaly'
url = "http://127.0.0.1:8000/getAnomaly2/?"
payload = '2.0'
url = url + 'threshold=' + payload
response = requests.request("POST", url, headers={}, data = {}, files = send_files_list)
json.loads(response.json())
#print(response.json())


