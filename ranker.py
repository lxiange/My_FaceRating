"""
It's the main file.
"""
import base64
import json
import time
import os
import re
import requests
from PIL import Image
from projectoxford import Client
import random

from xiaobingv3 import XiaoBingV3


"""
TODO:
get_evaluation_words(in_pic):
    upload or move to nginx path    #TODO
    get_ranked_img_url
    baidu or ms ocr:
        baidu:  get_cropped_img     #DONE
                ocr                 #DONE
        MS:     ocr                 #DONE
    trim                            #DONE
    def get rank point?             #DONE
"""


def identify_person(in_put_, mode_='path', group_id='goodlooking_group'):
    the_face_list = client.face.detect({mode_: in_put_})

    # NOT good.
    person_id_dict = {'f38edcbb-f17e-4c24-a819-daf3d022ba30': 'LiHan'}

    faceid_list = []
    for i in the_face_list:
        faceid_list.append(i['faceId'])

    candidates_list = client.face.identify(
        group_id, faceid_list)  # only match 1
    person_list = []
    for i in candidates_list:
        if i['candidates'] != [] and i['candidates'][0]['confidence'] > 0.6:
            person_list.append(person_id_dict[i['candidates'][0]['personId']])

    return person_list


# TODO:
# use tinypng to compress pictures.
# use lrz4 to compress pic in user's browser.
def compress_pic(f_name, width=700):
    with Image.open(f_name) as img1:
        (r_x, r_y) = img1.size
        a_x = 700
        a_y = int(r_y * a_x / r_x)
        out = img1.resize((a_x, a_y), Image.ANTIALIAS)
        out.save("compressed/" + f_name)


# TODO:
# reduce the transmisson times.
# enable 'smart' mode!
def my_rank(f_name):
    comment = {'LiHan': '哇，李晗女神！这张脸我给 %d 分！' % random.randint(95, 99)}
    t_s = time.time()
    person_list = identify_person(f_name)
    t_e = time.time()
    print("identify_person time: ", t_e - t_s)

    if person_list:
        comm_list = [comment[i] for i in person_list]
        return comm_list
    return "fuckyou"


class MyRanker(object):
    """docstring for MyRanker"""

    def __init__(self, arg):
        self.api_key = arg
        self.client = Client(self.api_key)
        self.person_id_dict = {'f38edcbb-f17e-4c24-a819-daf3d022ba30': 'LiHan'}


    #TODO: refactor, split into two functions
    def identify_person(self, in_put_, mode_='path', group_id='goodlooking_group'):
        the_face_list = self.client.face.detect({mode_: in_put_})

        faceid_list = []
        for i in the_face_list:
            faceid_list.append(i['faceId'])

        candidates_list = self.client.face.identify(group_id, faceid_list)
        #only match 1 person.

        person_list = []
        for i in candidates_list:
            if i['candidates'] != [] and i['candidates'][0]['confidence'] > 0.6:
                person_list.append(self.person_id_dict[
                                   i['candidates'][0]['personId']])

        return person_list


if __name__ == '__main__':
    with open('key.pass', 'r') as f1:
        _api_keys = json.load(f1)

    # client = Client(_api_keys['projectoxford']['face']['sub'])

    # url = get_raw_img_url('77.jpg')

    url_0 = 'http://139.129.25.147/6.jpg'
    url_1 = 'http://njucser.tk/6.jpg'
    # judge = get_judgements(url)

    # pg = PersonGroup(_api_keys)
    # print(pg.list())

    xb = XiaoBingV3()
    xb._get_raw_img_url('6.jpg')
    print(xb.rank('6.jpg'))
