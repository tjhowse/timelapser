#!/usr/bin/python3

import time
import os
import requests
import shutil
import schedule
import datetime
import logging

IP = os.environ.get("espcamip", "192.168.1.111")
REQUEST_FORMAT = "http://{}/{}".format(IP, "{}")
TIMELAPSE_INTERVAL_SEC = int(os.environ.get("interval_sec", 5*60))
PATH_PREFIX = os.environ.get("pathprefix", "")
# This is the starting quality. It will ramp up, reducing the quality,
# until the images from the camera are consistently less than MAX_SIZE_BYTES, because
# that's the absolute maximum image size an esp32cam without PSRAM can produce.
# If the file size goes below MIN_SIZE_BYTES, still save the image but increase
# the quality a bit so the next image is higher quality.
QUALITY_START = int(os.environ.get("quality_start", "25"))
SIZE = os.environ.get("size", "8")
# If an image is this big it is almost certainly truncated
MAX_SIZE_BYTES = 60000
# If an image is this small we can probably afford to increase the quality
MIN_SIZE_BYTES = 40000
logging.basicConfig(level=logging.INFO)
MIN_QUALITY = 63
MAX_QUALITY = 10

class timelapser():
    def __init__(self, quality):
        self.quality = quality

    def get_frame(self):
        time_string = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=10))).strftime("%Y-%m-%dT%H.%M.%S")
        filename = "{}{}_{}.jpg".format(PATH_PREFIX, time_string, self.quality)
        try:
            r = requests.get(REQUEST_FORMAT.format("control?var=hmirror&val={}".format(0)))
            time.sleep(1)
            r = requests.get(REQUEST_FORMAT.format("control?var=vflip&val={}".format(0)))
            time.sleep(1)
            r = requests.get(REQUEST_FORMAT.format("control?var=quality&val={}".format(self.quality)))
            time.sleep(1)
            r = requests.get(REQUEST_FORMAT.format("control?var=framesize&val={}".format(SIZE)))
            time.sleep(1)
            r = requests.get(REQUEST_FORMAT.format("capture"), stream=True)
            if r.status_code == 200:
                image = r.content
                size = len(image)
                if size >= MAX_SIZE_BYTES:
                    self.quality += 1
                    if self.quality > MIN_QUALITY:
                        self.quality = MIN_QUALITY
                    logging.info("Got a max-size image. Reducing quality to {} to compensate.".format(self.quality))
                    time.sleep(1)
                    # Free up this RAM for the recursion. There's no point keeping it around.
                    del image
                    self.get_frame()
                elif size == 0:
                    raise Exception("Zero-byte image from camera")
                else:
                    if size <= MIN_SIZE_BYTES:
                        self.quality -= 1
                        if self.quality < MAX_QUALITY:
                            self.quality = MAX_QUALITY
                        logging.info("Got a min-size image. increasing quality to {} for the next image.".format(self.quality))
                    with open(filename, 'wb') as f:
                        written = f.write(image)
                        logging.info("Saved image to {}, {} bytes".format(filename, written))
        except Exception as e:
            logging.error("Failed to save image: {}".format(e))

    def main(self):
        logging.info("Timelapsing from IP:{}, PATH_PREFIX:{}, QUALITY_START:{}, SIZE:{}".format(IP, PATH_PREFIX, QUALITY_START, SIZE))
        self.get_frame()
        schedule.every(TIMELAPSE_INTERVAL_SEC).seconds.do(self.get_frame)
        while True:
            schedule.run_pending()
            time.sleep(1)


if __name__ == '__main__':
    t = timelapser(QUALITY_START)
    t.main()
