from jpeg import Jpeg
if __name__ == '__main__':
    HUFF_SIMPLE_PATH = r'..\imgs\huff_simple0.jpg'
    # pic = Jpeg(r'..\imgs\huff_simple0.jpg')
    pic = Jpeg(r'..\imgs\smaller.JPG')
    # pic = Jpeg(r'..\imgs\drorer.JPG')
    pic.parse()

