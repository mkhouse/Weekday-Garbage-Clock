import gc
import time
import math
import random
import json
import board
import busio
import displayio
import terminalio
import sys
from rtc import RTC
from adafruit_matrixportal.network import Network
from adafruit_matrixportal.matrix import Matrix
from digitalio import DigitalInOut, Pull
from adafruit_debouncer import Debouncer
#from adafruit_matrixportal.matrixportal import MatrixPortal
from adafruit_bitmap_font import bitmap_font
import adafruit_display_text.label
import adafruit_lis3dh

try:
    from secrets import secrets
except ImportError:
    print('WiFi secrets are kept in secrets.py, please add them there!')
    raise

network = Network(status_neopixel=board.NEOPIXEL, debug=False)
network.connect()

aio_username = secrets["aio_username"]
aio_key = secrets["aio_key"]
timezone = secrets["timezone"]
time_url='https://io.adafruit.com/api/v2/' + aio_username + '/integrations/time/struct/?x-aio-key=' + aio_key + '&tz=' + timezone
print("time_url:" + time_url)

#{"year":2021,"mon":1,"mday":2,"hour":17,"min":22,"sec":25,"wday":6,"yday":2,"isdst":0}

print("")
print("Start update_time function NETWORK.fetch_data")
time_data_str = network.fetch_data(time_url)

print("time_data_str: ", time_data_str)
print("time_data_str type: ", type(time_data_str))
time_data = json.loads(time_data_str)
print("time_data type: ", type(time_data))
print("time_data values: ", time_data.values())
print("time_data keys: ", time_data.keys())
print(time_data["year"], time_data["mon"], time_data["mday"], time_data["hour"],
        time_data["min"], time_data["sec"], time_data["wday"], time_data["yday"],
            time_data["isdst"])

#Successful test ended abocve
#new test items below
time_struct = time.struct_time(time_data["year"], time_data["mon"], time_data["mday"],
        time_data["hour"], time_data["min"], time_data["sec"], time_data["wday"],
            time_data["yday"], time_data["isdst"])
if time_data["wday"] == 0: # Sunday
    weekday = "SUN"
    garbage = "3 days"
    color = "green"
    hcolor = 0x33CC33
elif time_data["wday"] == 1: # Monday
    weekday = "MON"
    garbage = "2 days"
    color = "green"
    hcolor = 0x33CC33
elif time_data["wday"] == 2 and time_data["hour"] < 19: # Tuesday before 7pm
    weekday = "TUE"
    garbage = "2nite"
    color = "yellow"
    hcolor = 0xFFFF00
elif time_data["wday"] == 2 and time_data["hour"] >= 19: # Tuesday after 7pm
    weekday = "TUE"
    garbage = "NOW"
    color = "red"
    hcolor = 0xFF0000
elif time_data["wday"] == 3 and time_data["hour"] <= 7 and time_data["min"] <= 59: # Wednesday 5am - 7:59am
    weekday = "WED"
    garbage = "NOW"
    color = "red"
    hcolor = 0xFF0000
elif time_data["wday"] == 3 and time_data["hour"] >= 8 : # Wednesday after 9am
    weekday = "WED"
    garbage = "done"
    color = "green"
    hcolor = 0x33CC33
elif time_data["wday"] == 4: # Thursday
    weekday = "THU"
    garbage = "6 days"
    color = "green"
    hcolor = 0x33CC33
elif time_data["wday"] == 5: # Friday
    weekday = "FRI"
    garbage = "5 days"
    color = "green"
    hcolor = 0x33CC33
elif time_data["wday"] == 6: # Saturday
    weekday = "SAT"
    garbage = "4 days"
    color = "green"
    hcolor = 0x33CC33

RTC().datetime = time_struct
print("update_time complete")
print("time_struct: ", time_struct)
print("weekday: ", weekday)
print("garbage: ", garbage)
print("RTC().datetime: ", RTC().datetime)
print("")
