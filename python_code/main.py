from Jpeg import Jpeg

if __name__ == '__main__':
    print('gal')
    pic = Jpeg(r'..\imgs\FPEI6055.JPG')
    print(pic._exists_eoi)
    pic.parse()
    print(pic._exists_eoi)
