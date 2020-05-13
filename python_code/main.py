from jpeg import Jpeg
import time

from jpeg_common import zig_zag_index

if __name__ == '__main__':
    print("time:", time.time())
    HUFF_SIMPLE_PATH = r'..\imgs\huff_simple0.jpg'
    # pic = Jpeg(HUFF_SIMPLE_PATH)
    pic = Jpeg(r'..\imgs\FPEI6055.JPG')
    #pic = Jpeg(r'..\imgs\smaller.JPG')
    pic.parse()
    print("time:", time.time())

    # data = open(r'..\imgs\lennag.JPG', "rb").read()
    # for i in range(len(data)):
    #     if data[i] == 0xff and data[i+1] == 0xc0:
    #         print(data[i+9])
    #         break
