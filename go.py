#!/usr/bin/python3

import time
import os
import requests
import shutil
import schedule
import datetime

IP = os.environ.get("espcamip", "192.168.1.111")
REQUEST_FORMAT = "http://{}/{}".format(IP, "{}")
TIMELAPSE_INTERVAL_MIN = 5
PATH_PREFIX = os.environ.get("pathprefix", "")
QUALITY = os.environ.get("quality", "17")
SIZE = os.environ.get("size", "9")

def get_frame():
    filename = "{}{}.jpg".format(PATH_PREFIX, datetime.datetime.now().isoformat())
    # Thanks, windows.
    filename = filename.replace(":",".")
    try:
        r = requests.get(REQUEST_FORMAT.format("control?var=quality&val={}".format(QUALITY)))
        r = requests.get(REQUEST_FORMAT.format("control?var=framesize&val={}".format(SIZE)))
        r = requests.get(REQUEST_FORMAT.format("capture"), stream=True)
        if r.status_code == 200:
            with open(filename, 'wb') as f:
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, f)
                print("Saved image to {}".format(filename))
    except Exception as e:
        print("Failed to save image: {}".format(e))

def main():
    startup_log = "Timelapsing from IP:{}, PATH_PREFIX:{}, QUALITY:{}, SIZE:{}".format(IP, PATH_PREFIX, QUALITY, SIZE)
    print(startup_log)
    with open(PATH_PREFIX+"debug.txt", "w") as f:
        f.write(startup_log)
    get_frame()
    schedule.every(TIMELAPSE_INTERVAL_MIN).minutes.do(get_frame)
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == '__main__':
    main()