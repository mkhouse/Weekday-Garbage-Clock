"""
GARBAGE CLOCK for Adafruit Matrix Portal displays current time, date, day of
week, garbage alert, and countdown to garbage day.
Requires WiFi internet access.
GARBAGE CLOCK written by Melissa House is derived from:

MOON PHASE CLOCK for Adafruit Matrix Portal: displays current time, lunar
phase and time of next moonrise or moonset. Requires WiFi internet access.
Original MOON PHASE CLOCK Written by Phil 'PaintYourDragon' Burgess for
Adafruit Industries.
MIT license, all text above must be included in any redistribution.

BDF fonts from the X.Org project.
"""

# pylint: disable=import-error
import gc
import time
import math
import random
import json
import board
import busio
import displayio
import terminalio
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

# CONFIGURABLE SETTINGS ----------------------------------------------------

TWELVE_HOUR = True  # If set, use 12-hour time vs 24-hour (e.g. 3:00 vs 15:00)
BITPLANES = 6       # Ideally 6, but can set lower if RAM is tight
DEMO = False        # Enable / Disable demo mode to scroll through each day

# SOME UTILITY FUNCTIONS AND CLASSES ---------------------------------------

def parse_time(timestring, is_dst=-1):
    """ Given a string of the format YYYY-MM-DDTHH:MM:SS.SS-HH:MM (and
        optionally a DST flag), convert to and return an equivalent
        time.struct_time (strptime() isn't available here). Calling function
        can use time.mktime() on result if epoch seconds is needed instead.
        Time string is assumed local time; UTC offset is ignored. If seconds
        value includes a decimal fraction it's ignored.
    """
    date_time = timestring.split('T')        # Separate into date and time
    year_month_day = date_time[0].split('-') # Separate time into Y/M/D
    hour_minute_second = date_time[1].split('+')[0].split('-')[0].split(':')
    return time.struct_time(int(year_month_day[0]),
                            int(year_month_day[1]),
                            int(year_month_day[2]),
                            int(hour_minute_second[0]),
                            int(hour_minute_second[1]),
                            int(hour_minute_second[2].split('.')[0]),
                            -1, -1, is_dst)


def update_time(timezone=None, demo_num=0, demo_hour="7"):
    """ Update system date/time from WorldTimeAPI public server;
        no account required. Pass in time zone string
        (http://worldtimeapi.org/api/timezone for list)
        or None to use IP geolocation. Returns current local time as a
        time.struct_time and UTC offset as string. This may throw an
        exception on fetch_data() - it is NOT CAUGHT HERE, should be
        handled in the calling code because different behaviors may be
        needed in different situations (e.g. reschedule for later).
    """
    if timezone: # Use timezone api
        time_url = 'http://worldtimeapi.org/api/timezone/' + timezone
    else: # Use IP geolocation
        time_url = 'http://worldtimeapi.org/api/ip'

    if DEMO == False:
        time_data = NETWORK.fetch_data(time_url,
                                       json_path=[['datetime'], ['dst'],
                                                  ['utc_offset'], ['day_of_week']])
    else:
        month = str(random.randint(1,12))
        day = str(random.randint(1,28))
        if demo_hour:
            hour = demo_hour
        else:
            hour = str(random.randint(6,20))
            # hour = str(random.randint(0,23)) # will occasionally show night mode
        minute = str(random.randint(10,59))
        demoDateTime = '2020-' + month + '-' + day + 'T' + hour + ':' + minute + ':15.813019-08:00'
        # time data JSON example: ['2020-11-28T20:45:15.813019-08:00', False, '-08:00', 6]
        time_data = [demoDateTime, False, '-08:00', demo_num]

    print("time_data: ", time_data)

    time_struct = parse_time(time_data[0], time_data[1])
    if time_data[3] == 0: # Sunday
        weekday = "SUN"
        garbage = "3 days"
        color = "green"
        hcolor = 0x33CC33
    elif time_data[3] == 1: # Monday
        weekday = "MON"
        garbage = "2 days"
        color = "green"
        hcolor = 0x33CC33
    elif time_data[3] == 2 and time_struct.tm_hour < 19: # Tuesday before 7pm
        weekday = "TUE"
        garbage = "2nite"
        color = "yellow"
        hcolor = 0xFFFF00
    elif time_data[3] == 2 and time_struct.tm_hour >= 19: # Tuesday after 7pm
        weekday = "TUE"
        garbage = "NOW"
        color = "red"
        hcolor = 0xFF0000
    elif time_data[3] == 3 and time_struct.tm_hour <= 7 and time_struct.tm_min <= 59: # Wednesday 5am - 7:59am
        weekday = "WED"
        garbage = "NOW"
        color = "red"
        hcolor = 0xFF0000
    elif time_data[3] == 3 and time_struct.tm_hour >= 8 : # Wednesday after 9am
        weekday = "WED"
        garbage = "done"
        color = "green"
        hcolor = 0x33CC33
    elif time_data[3] == 4: # Thursday
        weekday = "THU"
        garbage = "6 days"
        color = "green"
        hcolor = 0x33CC33
    elif time_data[3] == 5: # Friday
        weekday = "FRI"
        garbage = "5 days"
        color = "green"
        hcolor = 0x33CC33
    elif time_data[3] == 6: # Saturday
        weekday = "SAT"
        garbage = "4 days"
        color = "green"
        hcolor = 0x33CC33

    RTC().datetime = time_struct
    print("update_time")
    print("time_struct: ", time_struct)
    print("utc_offset: ", time_data[2])
    print("weekday: ", weekday)
    print("garbage: ", garbage)
    return time_struct, time_data[2], weekday, garbage, color, hcolor


def hh_mm(time_struct):
    """ Given a time.struct_time, return a string as H:MM or HH:MM, either
        12- or 24-hour style depending on global TWELVE_HOUR setting.
    """
    if TWELVE_HOUR:
        if time_struct.tm_hour > 12:
            hour_string = str(time_struct.tm_hour - 12) # 13-23 -> 1-11 (pm)
        elif time_struct.tm_hour > 0:
            hour_string = str(time_struct.tm_hour) # 1-12
        else:
            hour_string = '12' # 0 -> 12 (am)
    else:
        hour_string = '{0:0>2}'.format(time_struct.tm_hour)
    return hour_string + ':' + '{0:0>2}'.format(time_struct.tm_min)


# ONE-TIME INITIALIZATION --------------------------------------------------
# set up the display
MATRIX = Matrix(bit_depth=BITPLANES)
DISPLAY = MATRIX.display

#set up the buttons - not currently working
pin_down = DigitalInOut(board.BUTTON_DOWN)
pin_down.switch_to_input(pull=Pull.UP)
button_down = Debouncer(pin_down)
pin_up = DigitalInOut(board.BUTTON_UP)
pin_up.switch_to_input(pull=Pull.UP)
button_up = Debouncer(pin_up)

ACCEL = adafruit_lis3dh.LIS3DH_I2C(busio.I2C(board.SCL, board.SDA),
                                   address=0x19)
_ = ACCEL.acceleration # Dummy reading to blow out any startup residue
time.sleep(0.1)
DISPLAY.rotation = (int(((math.atan2(-ACCEL.acceleration.y,
                                     -ACCEL.acceleration.x) + math.pi) /
                         (math.pi * 2) + 0.875) * 4) % 4) * 90

LARGE_FONT = bitmap_font.load_font('/fonts/helvB12.bdf')
SMALL_FONT = bitmap_font.load_font('/fonts/helvR10.bdf')
LARGE_FONT.load_glyphs('0123456789:')
SMALL_FONT.load_glyphs('0123456789:/.%')

# Display group is set up once, then we just shuffle items around later.
# Order of creation here determines their stacking order.
GROUP = displayio.Group(max_size=10)

# sets empty_group for night mode
empty_group = displayio.Group()

# Element 0 is a stand-in item, later replaced with the garbage can bitmap
# pylint: disable=bare-except
try:
    FILENAME = 'bmps/garbage-start-' + str(DISPLAY.rotation) + '.bmp'
    BITMAP = displayio.OnDiskBitmap(open(FILENAME, 'rb'))
    TILE_GRID = displayio.TileGrid(BITMAP, pixel_shader=displayio.ColorConverter(),)
    GROUP.append(TILE_GRID)
except:
    GROUP.append(adafruit_display_text.label.Label(SMALL_FONT, color=0xFF0000,
                                                   text='OOPS'))
    GROUP[0].x = (DISPLAY.width - GROUP[0].bounding_box[2] + 1) // 2
    GROUP[0].y = DISPLAY.height // 2 - 1
# Elements 1-4 are an outline around the moon percentage -- text labels
# offset by 1 pixel up/down/left/right. Initial position is off the matrix,
# updated on first refresh. Initial text value must be long enough for
# longest anticipated string later.
for i in range(4):
    GROUP.append(adafruit_display_text.label.Label(SMALL_FONT, color=0,
                                                   text='99.9%', y=-99))
# Element 5 is days until garbage out (on top of the outline labels)
GROUP.append(adafruit_display_text.label.Label(SMALL_FONT, color=0xFFFF00,
                                               text='99.9%', y=-99))
# Element 6 is the current time
GROUP.append(adafruit_display_text.label.Label(LARGE_FONT, color=0x808080,
                                               text='12:00', y=-99))
# Element 7 is the current date
GROUP.append(adafruit_display_text.label.Label(SMALL_FONT, color=0x808080,
                                               text='12/31', y=-99))
# Element 8 is the time of (or time to) next rise/set event
GROUP.append(adafruit_display_text.label.Label(SMALL_FONT, color=0x00FF00,
                                               text='12:00', y=-99))
DISPLAY.show(GROUP)

NETWORK = Network(status_neopixel=board.NEOPIXEL, debug=False)
NETWORK.connect()

# TIMEZONE is set up once, constant over app lifetime
# Load time zone string from secrets.py, else IP geolocation for this too
# (http://worldtimeapi.org/api/timezone for list).
try:
    TIMEZONE = secrets['timezone'] # e.g. 'America/New_York'
except:
    TIMEZONE = None # IP geolocation

# Set initial clock time, also fetch initial UTC offset while
# here (NOT stored in secrets.py as it may change with DST).
# pylint: disable=bare-except
demo_num = 0
LAST_SYNC = 0
demo_hour = str(random.randint(6,20))
repeatDayCount = 0

# MAIN LOOP ----------------------------------------------------------------

while True:
    gc.collect()
    NOW = time.time() # Current epoch time in seconds
    LOCALNOW = time.localtime() # local time

    #--DOES NOT WORK BELOW--
    #button_down.update()
    #button_up.update()
    #if button_up.fell:
    #    print("button up pressed")
    #--DOES NOT WORK ABOVE--

    # Sync with time server every ~5 minutes - the clock drifts if left too long
    if DEMO == False:
        if LAST_SYNC == 0:
            print("Initialize")
            try:
                DATETIME, UTC_OFFSET, WEEKDAY, GARBAGEDAY, COLOR, HCOLOR = update_time(TIMEZONE)
            except:
                DATETIME, UTC_OFFSET, WEEKDAY, GARBAGEDAY, COLOR, HCOLOR = time.localtime(), '+00:00', "???", "???", "grey", 0x66666
            LAST_SYNC = time.mktime(DATETIME)
            print("Datetime: ", DATETIME)
            print ("Last sync: ", LAST_SYNC)
            print("Garbage Day: ", GARBAGEDAY)
            print("Day Color: ", COLOR)
            print("Datetime hour: ", DATETIME.tm_hour)
        # elif NOW - LAST_SYNC > 60*5:
        elif NOW - LAST_SYNC > 60:
            try:
                DATETIME, UTC_OFFSET, WEEKDAY, GARBAGEDAY, COLOR, HCOLOR = update_time(TIMEZONE)
                print("")
                print("TIME REFRESH DEMO FALSE")
                print("Weekday: ", WEEKDAY)
                print("")
                LAST_SYNC = time.mktime(DATETIME)
                continue # Time may have changed; refresh NOW value
            except:
                # update_time() can throw an exception if time server doesn't
                # respond. That's OK, keep running with our current time, and
                # push sync time ahead to retry in 30 minutes (don't overwhelm
                # the server with repeated queries).
                print("")
                print("TIME REFRESH EXCEPTION")
                print("")
                # LAST_SYNC += 60 * 5 # 5 minutes
                LAST_SYNC += 60 # 1 minute
                continue
    elif DEMO == True:
        # normal demo mode start
        if NOW - LAST_SYNC > 5 or LAST_SYNC == 0: #increment every 10 seconds
            if demo_num == 2 or demo_num == 3: # on Tuesday and Wednesday
                if repeatDayCount == 0:
                    demo_hour="7" #set demo hour to 7AM to show first half of the day
                    repeatDayCount += 1 #will repeat the day
                elif repeatDayCount == 1:
                    demo_hour="19" #set demo hour to 7PM to show second half of the day
                    repeatDayCount = 0 #reset repeatDayCount to 0 to move to next day
        # normal demo mode end
        #
        # special time demo mode start
        # uncomment this and comment normal demo move (above)to test night mode
        # or to test other states requiring specific times
        # if NOW - LAST_SYNC > 5 or LAST_SYNC == 0: #increment every 10 seconds
        #     if demo_hour == "7":
        #         demo_hour = "22"
        #     elif demo_hour == "22":
        #         demo_hour = "7"
        # special time demo mode end
        # uncomment to here
        #
            print("")
            print("Tue / Wed demo_hour: ", demo_hour)
            print("repeatDayCount: ", repeatDayCount)
            print("")
            DATETIME, UTC_OFFSET, WEEKDAY, GARBAGEDAY, COLOR, HCOLOR = update_time(TIMEZONE, demo_num, demo_hour)
            if repeatDayCount == 0: # increment the day if it's not repeating
                if demo_num < 6:
                    demo_num += 1
                else:
                    demo_num = 0
            # demo_hour = str(random.randint(6,20)) # will not show night mode
            demo_hour = str(random.randint(0,23)) # will occasionally show night mode
            print("")
            print("TIME REFRESH DEMO TRUE")
            print("demo_num: ", demo_num)
            print("Weekday: ", WEEKDAY)
            print("")
            # LAST_SYNC = time.mktime(DATETIME)
            continue # Time may have changed; refresh NOW value

    print()
    print("Datetime: ", DATETIME)
    print("Last Sync: ", LAST_SYNC)
    print("Now: ", NOW)
    print("NOW - LAST_SYNC: ", NOW - LAST_SYNC)

    # Don't draw anything from 10pm to 6am (this thing is BRIGHT)
    # if (DATETIME.tm_hour >= 22 and DATETIME.tm_min >= 0) or (DATETIME.tm_hour <= 6):
    if (DATETIME.tm_hour >= 22 and DATETIME.tm_min >= 0) or (DATETIME.tm_hour <=5 and DATETIME.tm_min >= 0):
        print("Night Mode On")
        DISPLAY.show(empty_group)
    # If it's not night, use normal daytime colors
    else:
        print("Night Mode Off")
        # Sets the display orientation based on whether the board is horizontal or vertical
        if DISPLAY.rotation in (0, 180): # Horizontal 'landscape' orientation
            CENTER_X = 48  # Text along right
            TRASH_Y = 0     # Garbage at left
            TIME_Y = 6     # Time at top right
            EVENT_Y = 26   # Day of week at bottom right
        else:              # Vertical 'portrait' orientation
            CENTER_X = 16  # Text down center
            TIME_Y = 6     # Time/date at top
            EVENT_Y = 26   # Day of week in middle
            TRASH_Y = 32    # Garbage at bottom
        DISPLAY.show(GROUP)
        # Update trash can image (GROUP[0])
        FILENAME = 'bmps/garbage_can_' + COLOR + '.bmp'
        BITMAP = displayio.OnDiskBitmap(open(FILENAME, 'rb'))
        TILE_GRID = displayio.TileGrid(BITMAP,
                                       pixel_shader=displayio.ColorConverter(),)
        TILE_GRID.x = 0
        TILE_GRID.y = TRASH_Y

        GROUP[0] = TILE_GRID

        # Set element 5 first, use its size and position for setting others
        #GROUP[5].text is the text over the image
        GROUP[5].text = GARBAGEDAY
        GROUP[5].color = HCOLOR
        GROUP[5].x = 16 - GROUP[5].bounding_box[2] // 2
        GROUP[5].y = TRASH_Y + 16
        for _ in range(1, 5):
            GROUP[_].text = GROUP[5].text
        GROUP[1].x, GROUP[1].y = GROUP[5].x, GROUP[5].y - 1 # Up 1 pixel
        GROUP[2].x, GROUP[2].y = GROUP[5].x - 1, GROUP[5].y # Left
        GROUP[3].x, GROUP[3].y = GROUP[5].x + 1, GROUP[5].y # Right
        GROUP[4].x, GROUP[4].y = GROUP[5].x, GROUP[5].y + 1 # Down

        # GROUP[8] is day of week
        GROUP[8].text = WEEKDAY + "   "
        XPOS = CENTER_X - (GROUP[8].bounding_box[2] + 6) // 2
        GROUP[8].x = XPOS + 6
        GROUP[8].y = EVENT_Y
        # Show weekday in color matching trash color
        GROUP[8].color = HCOLOR

        # Update time (GROUP[6]) and date (GROUP[7])
        # GROUP[6] is the time
        GROUP[6].text = hh_mm(LOCALNOW)
        # Show time in orange if AM, blue if PM
        GROUP[6].color = (0xFF6600 if DATETIME.tm_hour < 12 else 0x3300CC)
        GROUP[6].x = CENTER_X - GROUP[6].bounding_box[2] // 2
        GROUP[6].y = TIME_Y
        # GRYOUP[7] is the date
        GROUP[7].text = str(LOCALNOW.tm_mon) + '.' + str(LOCALNOW.tm_mday)
        GROUP[7].x = CENTER_X - GROUP[7].bounding_box[2] // 2
        GROUP[7].y = TIME_Y + 10

    DISPLAY.refresh() # Force full repaint (splash screen sometimes sticks)
    time.sleep(5)
