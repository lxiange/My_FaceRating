"""
It's the main file.
"""
import json
import time
from PIL import Image
from projectoxford import Client
from projectoxford import PersonGroup
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


# TODO:
# use tinypng to compress pictures.
# use lrz4 to compress pic in user's browser.
def compress_pic(f_name, width=700):
    with Image.open(f_name) as img1:
        (r_x, r_y) = img1.size
        a_x = width
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
        self.xiaobing = XiaoBingV3()
        self.person_id_dict = {'f38edcbb-f17e-4c24-a819-daf3d022ba30': 'LiHan',
                               '111': 'LiXiang',
                               '222': 'WangJunTian'}

    def get_faces_list(self, option):
        resp = self.client.face.detect(option)
        face_list = [i['faceId']for i in resp]
        return face_list

    def _identify_person(self, faceid_list, group_id='goodlooking_group'):
        candidates_list = self.client.face.identify(group_id, faceid_list)
        face_person = {}
        for i in candidates_list:
            sub_cand = i['candidates']
            for j in sub_cand:
                if j['confidence'] > 0.6:
                    face_person[i['faceId']] = j['personId']
                    # only find one people
                    break
        return face_person

    def get_person_list(self, input_, mode_='path', need_bad=False):
        persons = {'good': [], 'bad': []}

        face_list = self.get_faces_list({mode_: input_})

        face_person = self._identify_person(face_list)
        for fid in face_person:
            if face_person[fid] in self.person_id_dict:
                persons['good'].append(self.person_id_dict[face_person[fid]])

        if need_bad:
            face_person = self._identify_person(face_list, 'ugly_group')
            for fid in face_person:
                if face_person[fid] in self.person_id_dict:
                    persons['bad'].append(self.person_id_dict[face_person[fid]])

        return persons

    # TODO: try *args **kw ?
    def rank(self, input_, mode_='path', is_num=False):
        return 0


if __name__ == '__main__':
    with open('key.pass', 'r') as f1:
        _api_keys = json.load(f1)

    url_0 = 'http://139.129.25.147/6.jpg'
    url_1 = 'http://njucser.tk/6.jpg'
    mr = MyRanker(_api_keys['projectoxford']['face']['sub'])
    print(mr.get_person_list(url_1, 'url'))
    # pp = PersonGroup(_api_keys['projectoxford']['face']['sub'])
    # print(pp.list())
