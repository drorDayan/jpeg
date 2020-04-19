from python_code.Jpeg import Jpeg

if __name__ == '__main__':
    print('gal')
    pic = Jpeg(r'C:\Users\galls2\Desktop\work_from_home\jpeg_d\gal.jpg')
    print(pic._exists_eoi)
    pic.parse()
    print(pic._exists_eoi)