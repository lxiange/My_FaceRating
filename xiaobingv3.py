"""
Codes related to Xiaobing.
"""
import requests
import base64
import time
import re


class XiaoBingV3(object):
    """Up to now, this class only provides the rank feature."""

    def __init__(self):
        """__init__"""
        pass

    def _get_raw_img_url(self, in_file):
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

    def _get_judgements(self, img_url):
        """Get Xiaobing's judgement
        Args:
            img_url <str>: the photo's url.

        Returns:
            A string of Xiaobing's judgement.
        """
        sys_time = int(time.time())
        comp_url = 'http://kan.msxiaobing.com/Api/ImageAnalyze/Process'
        payload = {'service': 'yanzhi',
                   'tid': '04a01fbe5f5c4b7496034ad9cf41ff01'}
        form = {  # don't ask me why, it's just magic numbers~
            'msgId': str(sys_time) + '233',
            'timestamp': sys_time,
            'senderId': 'mtuId' + str(sys_time - 242) + '717',
            'content[imageUrl]': img_url,
        }
        resp = requests.post(comp_url, params=payload, data=form)
        return resp.json()['content']['text']

    def _extract_point(self, text):
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

    def rank(self, input_, mode_='path', is_num=False):
        """Use Xiaobing V3 to rank the pic.

        Args:
            input_ <str>: the pic's filename or url.
            mode_ <str>: 'path' or 'url', depends on the input type.
            is_num <bool>: return the score or retain the comment.

        Returns:
            An int or str, depends on the value of is_num

        """
        if mode_ == 'path':
            raw_url = self._get_raw_img_url(input_)
        else:
            raw_url = input_

        judgement = self._get_judgements(raw_url)
        if is_num:
            return self._extract_point(judgement)
        return judgement


if __name__ == '__main__':
    xb = XiaoBingV3()
    print(xb.rank('6.jpg'))
