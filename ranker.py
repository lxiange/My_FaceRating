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



class MyRanker(object):
    """docstring for MyRanker"""

    def __init__(self, arg):
        self.api_key = arg
        self.client = Client(self.api_key)
        self.xiaobing = XiaoBingV3()
        self.person_id_dict = {'f38edcbb-f17e-4c24-a819-daf3d022ba30': 'LiHan',
                               '111': 'LiXiang',
                               '222': 'WangJunTian'}
        self.comment_dict = {'LiHan': ['beautiful!', 'pretty!'],
                             'WangJunTian': ['handsome!'],
                             'LiXiang': ['shabi']}
        # TODO: import comment dict from config file, and easy to generate sentence.

    def get_faces_list(self, option):
        """Input a pic, return a list of faces.

        Args:
            option <dict>: the same as the option in projectoxford

        Returns:
            A list of face id.
        """
        resp = self.client.face.detect(option)
        face_list = [i['faceId']for i in resp]
        return face_list

    def _identify_person(self, faceid_list, group_id='goodlooking_group'):
        """Input a list of face id, got the most similar persons of the faces.
        Such as input ['faceid1', 'faceid2'], and return a dict like:
        {'faceid2':'personid2'} (because face1 is not in the group)

        Args:
            faceid_list <list of facdId>:
                a list of faceid,but we highly recommend provide only one face.
            group_id <str>:
                Which group you want to detect.

        Returns:
            A dict like "{'faceid1':'personid1', 'faceid1':'personid1'}",
            if no matchs, return {}
        """
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
        """Input a pic, return the people's id if they are in the good/bad looking
            group.
        Args:
            input_ : input the given pic.
            mode_ <str>: could be 'path', 'stream' or 'url'.
            need_bad <bool>: Weather detect the ugly people, default is False,
                            if set True, will cost double time.

        Returns:
            persons <dict>: persons['good'] is the list of goodlooking people's names,
                            persons['bad'] is ..., but [] if need_bad is False.
        """
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

    @staticmethod
    def generate_sentence(name, comment, score):
        """Generate a fluent sentence by the given information.
            This may be extremely challenging. OJZ
        """
        return ' '.join((name, comment, str(score)))

    # TODO: try *args **kw ?
    def rank(self, input_, mode_='path'):
        """Input a pic, return a sentence contains name and score.
            if person not in the good/bad looking group, use xiaobing to generate sentence.
        """
        identified_persons = self.get_person_list(input_, mode_, need_bad=False)
        sentence_list = []

        for person_name in identified_persons['good']:
            comment = random.choice(self.comment_dict[person_name])
            score = random.randint(95, 99)
            sentence_list.append(self.generate_sentence(
                person_name, comment, score))

        for person_name in identified_persons['bad']:
            comment = random.choice(self.comment_dict[person_name])
            score = random.randint(25, 59)
            sentence_list.append(self.generate_sentence(
                person_name, comment, score))

        if not sentence_list:
            sentence_list.append(self.xiaobing.rank(input_, mode_))

        return sentence_list


if __name__ == '__main__':
    with open('key.pass', 'r') as f1:
        _api_keys = json.load(f1)

    url_0 = 'http://139.129.25.147/6.jpg'
    url_1 = 'http://njucser.tk/6.jpg'
    mr = MyRanker(_api_keys['projectoxford']['face']['sub'])
    print(mr.rank('77.jpg'))
    # print(mr.get_person_list(url_1, 'url'))
    # pp = PersonGroup(_api_keys['projectoxford']['face']['sub'])
    # print(pp.list())
