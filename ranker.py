import base64
import json
import time
import os
import re
import requests
from PIL import Image
from projectoxford import Client
import random


def get_raw_img_url(in_file):
    """Upload a pic, and get it's url.

    Cause Xiaobing only accepts URL input. We should upload the file to get
    its url. This function uploads the pic to Xiaobing's server.
    You can upload to other place you like, then this function is useless.

    Args:
        in_file <str>: the filename of the pic to be uploaded.

    Returns:
        A string of the pic's url
    """
    with open(in_file, 'rb') as f_stream:
        img_base64 = base64.b64encode(f_stream.read())

    upload_url = 'http://kan.msxiaobing.com/Api/Image/UploadBase64'

    resp = requests.post(upload_url, data=img_base64)
    return 'http://imageplatform.trafficmanager.cn' + resp.json()['Url']


def get_judgements(img_url):
    """Get Xiaobing's judgement
    Args:
        img_url <str>: the photo's url.

    Returns:
        A string of Xiaobing's judgement.
    """
    sys_time = int(time.time())
    comp_url = 'http://kan.msxiaobing.com/Api/ImageAnalyze/Process'
    payload = {'service': 'yanzhi', 'tid': '04a01fbe5f5c4b7496034ad9cf41ff01'}
    form = {  # don't ask me why, it's just magic numbers~
        'msgId': str(sys_time) + '233',
        'timestamp': sys_time,
        'senderId': 'mtuId' + str(sys_time - 242) + '717',
        'content[imageUrl]': img_url,
    }
    resp = requests.post(comp_url, params=payload, data=form)
    return resp.json()['content']['text']


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



def extract_point(text):
    """Extract the point form Xiaobing's judgement

    Args:
        text <str>: Xiaobing's judgement.

    Returns:
        An INT num of the point, (in hundred mark system).

    """
    match = re.search(r'\d[.·,。，]?\d', text)
    point_str = match.group(0)
    useless_char = ['.', '·', ',', '，', '。']
    for i in useless_char:
        point_str = point_str.replace(i, '')
    point = int(point_str)
    if point < 20:  # 7 is identified as 1
        point += 60
    return point


def rank_pic(in_file, api_key, mode_='fool'):
    """TODO"""
    if mode_ == 'smart':
        pass
        #   move pic to /www/pic
        #   imgUrl='http://vpsip/pic/xxxx.jpg'
    elif mode_ == 'fool':
        imgUrl = get_raw_img_url(in_file)
    else:
        return ''

    judges = get_judgements(imgUrl)
    return extract_point(judges)


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


_personGroupUrl = 'https://api.projectoxford.ai/face/v0/persongroups'


class MyRanker(object):

    def __init__(self, face_api_key):
        self.face_client = Client(face_api_key)
        self.key = face_api_key

    def create_person(self, personGroupId, faceIds, name, userData=None):
        """Creates a new person in a specified person group for identification.
        The number of persons has a subscription limit. Free subscription amount is 1000 persons.
        The maximum face count for each person is 32.
        Args:
            personGroupId (str). The target person's person group.
            faceIds ([str]). Array of face id's for the target person
            name (str). Target person's display name. The maximum length is 128.
            userData (str). Optional fields for user-provided data attached to a person. Size limit is 16KB.
        Returns:
            object. The resulting JSON
        """

        body = {
            'faceIds': faceIds,
            'name': name
        }

        if userData is not None:
            body['userData'] = userData

        uri = _personUrl + '/' + personGroupId + '/persons'
        return self._invoke('post', uri, json=body, headers={'Ocp-Apim-Subscription-Key': self.key})

    def list_groups(self):
        return self._invoke('get', _personGroupUrl,
                            headers={'Ocp-Apim-Subscription-Key': self.key})

    def create_group(self, personGroupId, name, userData=None):
        """Creates a new person group with a user-specified ID.
        A person group is one of the most important parameters for the Identification API.
        The Identification searches person faces in a specified person group.
        Args:
            personGroupId (str). Numbers, en-us letters in lower case, '-', '_'. Max length: 64
            name (str). Person group display name. The maximum length is 128.
            userData (str). Optional user-provided data attached to the group. The size limit is 16KB.
        Returns:
            object. The resulting JSON
        """

        body = {
            'name': name,
            'userData': userData
        }

        return self._invoke('put',
                            _personGroupUrl + '/' + personGroupId,
                            json=body,
                            headers={'Ocp-Apim-Subscription-Key': self.key})

    def start_training(self, personGroupId):
        """Starts a person group training.
        Training is a necessary preparation process of a person group before identification.
        Each person group needs to be trained in order to call Identification. The training
        will process for a while on the server side even after this API has responded.
        Args:
            personGroupId (str). Name of person group to train
        Returns:
            object. The resulting JSON
        """

        return self._invoke('post',
                            _personGroupUrl + '/' + personGroupId + '/training',
                            headers={'Ocp-Apim-Subscription-Key': self.key})

    def _invoke(self, method, url, json=None, data=None, headers={}, params={}, retries=0):
        """Attempt to invoke the a call to oxford. If the call is trottled, retry.
        Args:
            :param method: method for the new :class:`Request` object.
            :param url: URL for the new :class:`Request` object.
            :param data: (optional) Dictionary, bytes, or file-like object to send in the body of the :class:`Request`.
            :param json: (optional) json data to send in the body of the :class:`Request`.
            :param headers: (optional) Dictionary of HTTP Headers to send with the :class:`Request`.
            :param params: (optional) Dictionary or bytes to be sent in the query string for the :class:`Request`.
            :param retries: The number of times this call has been retried.
        """

        response = requests.request(
            method, url, json=json, data=data, headers=headers, params=params)

        if response.status_code == 429:  # throttling response code
            if retries <= retryCount:
                delay = int(response.headers['retry-after'])
                print('The projectoxford API was throttled. Retrying after {0} seconds'.format(
                    str(delay)))
                time.sleep(delay)
                return self._invoke(method, url, json=json, data=data,
                                    headers=headers, params=params, retries=retries + 1)
            else:
                raise Exception('retry count ({0}) exceeded: {1}'.format(
                    str(retryCount), response.text))
        elif response.status_code == 200 or response.status_code == 201:
            result = response  # return the raw response if an unexpected content type is returned
            if 'content-length' in response.headers and int(response.headers['content-length']) == 0:
                result = None
            elif 'content-type' in response.headers and isinstance(response.headers['content-type'], str):
                if 'application/json' in response.headers['content-type'].lower():
                    result = response.json() if response.content else None
                elif 'image' in response.headers['content-type'].lower():
                    result = response.content

            return result
        elif response.status_code == 404:
            return None
        else:
            raise Exception('status {0}: {1}'.format(
                str(response.status_code), response.text))


if __name__ == '__main__':
    with open('key.pass', 'r') as f1:
        _api_keys = json.load(f1)

    # client = Client(_api_keys['projectoxford']['face']['sub'])

    # url = get_raw_img_url('77.jpg')

    url = 'http://139.129.25.147/6.jpg'
    judge = get_judgements(url)

    print(judge)
