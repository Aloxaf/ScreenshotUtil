#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
from tempfile import mktemp
from subprocess import Popen
from sys import argv, stderr
from PIL import Image, ImageOps
import zxing
import tesserocr


def thresholding(img, threshold):
    """二值化图片
    :param img: PIL Image
    :param threhold: 阈值, 不大于这个值的像素点替换为黑
    """
    data = img.getdata()
    new_data = [(0 if i <= threshold else 255) for i in data]
    new_img = img.copy()
    new_img.putdata(new_data)
    return new_img


def denoise(img, threshold=200):
    """降噪
    :param img: PIL Image
    :param threhold: 阈值, 不大于这个值的像素点替换为黑
    """
    return thresholding(img, threshold)
    # TODO: 只实现了二值化, 不过其实能够选择区域以后降噪意义不大了


def showtext(text):
    """弹出窗口显示文字
    :param text: 将要输出的文字
    """
    # TODO: 这种调整窗口大小的方式太蠢了
    # TODO: 万一不是中文?
    size = [len(i.encode('GBK', errors='ignore')) for i in text.split('\n')]
    width = min(0 + max(size) * 10, 800)
    height = min(0 + len(size) * 10, 800)

    cmd = (lambda vs: [x.format(**vs) for x in CONFIG['dialog']])(vars())
    Popen(cmd, close_fds=True)


def recognize(file):
    """识别二维码
    :param file: 二维码图片路径
    """
    reader = zxing.BarCodeReader()
    data = reader.decode(file, possible_formats=['QR_CODE'])

    if not data:
        img = denoise(Image.open(file).convert('L'))
        img.save(file)
        data = reader.decode(file, possible_formats=['QR_CODE'])

    if data:
        text = data.raw
    else:
        text = 'Nothing Found!'

    showtext(text)

# TODO: 如何提高精度
def ocr(file, lang='eng'):
    """提取图中文字
    :param file: 二维码图片路径
    :param lang: 语言, 默认英语
    """
    img = Image.open(file).convert('L')
    with tesserocr.PyTessBaseAPI(lang=lang) as api:
        api.SetImage(denoise(img))
        text = api.GetUTF8Text().strip()

        if text == '':
            api.SetImage(ImageOps.invert(denoise(img, 100)))
            text = api.GetUTF8Text().strip()

    if text == '':
        text = 'No Text Found!'

    showtext(text)


if __name__ == '__main__':
    DIR_PATH = os.path.dirname(os.path.realpath(__file__))
    CONFIG = json.load(open(os.path.join(DIR_PATH, 'config.json')))

    if len(argv) == 1 or argv[1] in ['-h', '--help']:
        print('Usage: python ScreenshotUtil.py (ocr [lang])|decode')
        exit()
    elif argv[1] not in ['decode', 'ocr']:
        stderr.write(f'no command called {argv[1]}\n')
        exit()

    TEMP = mktemp()
    os.system(CONFIG['screenshot'].format(**locals()))

    if not os.path.exists(f'{TEMP}.png'):
        exit()

    if argv[1] == 'decode':
        recognize(f'{TEMP}.png')
    elif argv[1] == 'ocr':
        ocr(f'{TEMP}.png', argv[2] if len(argv) == 3 else 'eng')
