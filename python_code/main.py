from jpeg import Jpeg
import time

if __name__ == '__main__':
    print("time:", time.time())
    HUFF_SIMPLE_PATH = r'..\imgs\huff_simple0.jpg'
    # pic = Jpeg(HUFF_SIMPLE_PATH)
    # pic = Jpeg(r'..\imgs\FPEI6055.JPG')
    pic = Jpeg(r'..\imgs\smaller2.JPG')
    pic.parse()
    print("time:", time.time())

