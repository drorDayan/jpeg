from jpeg import Jpeg
import time

from jpeg_common import zig_zag_index

if __name__ == '__main__':

    # img_path = r'..\imgs\lennag.JPG'
    img_path = r'..\imgs\lenna.JPG'
    # # Print num of components for debug
    # data = open(img_path, "rb").read()
    # for i in range(len(data)):
    #     if data[i] == 0xff and data[i+1] == 0xc0:
    #         print("num of components:", data[i+9])
    #         break

    print("time:", time.time())
    pic = Jpeg(img_path)
    pic.parse()
    print("time:", time.time())

