import base64, json, time, os, threading, re
import urllib.parse, urllib.request

import requests
from PIL import Image

def get_raw_img_url(in_file, type='path'):
    with open(in_file,'rb') as f_stream:
        img_base64=base64.b64encode(f_stream.read())

    uploadUrl='http://kan.msxiaobing.com/Api/Image/UploadBase64'

    r = requests.post(uploadUrl, data=img_base64)
    return 'http://imageplatform.trafficmanager.cn'+r.json()['Url']


def get_ranked_img_url(imgUrl):
    sys_time=int(time.time())
    CompUrl='http://kan.msxiaobing.com/Api/ImageAnalyze/Comparison'
    form={
        'msgId':str(sys_time)+'233',
        'timestamp':sys_time,
        'senderId':'mtuId'+str(sys_time-242)+'717',
        'content[imageUrl]':imgUrl,
        }

    r = requests.post(CompUrl, data=form)
    return r.json()['content']['imageUrl']


def img_url_to_file(img_url, out_file):
    with open(out_file,'wb') as f_out:
        resp=requests.get(img_url)
        f_out.write(resp.content)
    return out_file


def get_cropped_img(img_url, out_pic, box=(240,1280,1210,1530)):
    img_url_to_file(img_url, out_pic+'.tmp')
    with Image.open(out_pic+'.tmp') as img1:
        img2=img1.crop(box)
        img2.save(out_pic)
        img2.close()
    os.remove(out_pic+'.tmp')
    return out_pic

"""
TODO:
get_evaluation_words(in_pic):
    upload or move to nginx path
    get_ranked_img_url
    baidu or ms ocr:
        baidu:  get_cropped_img     #DONE
                ocr                 #DONE
        MS:     ocr                 #DONE
    trim
    def get rank point?
"""

def ocr_via_baidu(url, apikey):
    rand_name=str(int(time.time()))+'.jpg'
    get_cropped_img(url, rand_name)
    with open(rand_name, 'rb') as input_file:
        img_base64=base64.b64encode(input_file.read())
    url = 'http://apis.baidu.com/apistore/idlocr/ocr'
    data={'fromdevice':"pc", 'clientip':"10.10.10.0", 'detecttype':"LocateRecognize",
            'languagetype':"CHN_ENG", 'imagetype':"1", 'image':img_base64 }
    headers={
        "Content-Type":"application/x-www-form-urlencoded",
        "apikey":apikey
    }
    req = requests.post(url, data, headers= headers)
    resp=req.json()
    words=[i['word'] for i in resp['retData']]
    os.remove(rand_name)
    return ''.join(words)


#     match=re.search(r'\d{2}|\d\.\d',textStr)
#     pointStr=match.group(0)
#     point=float(pointStr)
#     if point <= 10:      # . is identified
#         point *= 10
#     if point <= 20:      # 7 is identified as 1
#         point += 60
#     return point


def rank_pic(infile, apikey):
    a=time.time()
    getScoreImg(infile, infile+'_temp.jpg')
    b=time.time()
    print('getScoreImg time: ', b-a)
    point=getNumViaBaiduOCR(infile+'_temp.jpg', apikey)
    c=time.time()
    print('getNumViaBaiduOCR time: ', c-b)
    os.remove(infile+'_temp.jpg')
    if not 10<point<100: 
        return -1
    return int(point)

from projectoxford import Client
import random

with open('key.pass','r') as f1:
    _api_keys = json.load(f1)

    
client = Client(_api_keys['projectoxford']['face']['sub']) #Oxford face api key

def is_good_looking(f_in):
    the_face_list=client.face.detect({'stream':f_in})
    '''
    if len(the_face_list)>1:
        return False
        #assert (0)
    '''
    faceid_list=[]
    for i in the_face_list:
        faceid_list.append(i['faceId'])

    candidates_list=client.face.identify("goodlooking_group", faceid_list)  #only match 1 person
    #print(candidates_list)
    if len(candidates_list)>1:
        for i in candidates_list:
            if i['candidates']!=[]:
                if i['candidates'][0]['confidence']>0.6:
                    return True
        return False
    else:
        if(candidates_list[0]['candidates']!=[]):
            if candidates_list[0]['candidates'][0]['confidence']>0.6:
                return True
        return False


def my_rank(f_name):
    #f_in = open(f_name, 'rb')
    img1=Image.open(f_name)
    (r_x, r_y)=img1.size
    a_x=700
    a_y=int(r_y * a_x / r_x)
    out=img1.resize((a_x,a_y),Image.ANTIALIAS)
    out.save("temp/"+f_name)
    f_in = open("temp/"+f_name, 'rb')
    t_s=time.time()
    flag = is_good_looking(f_in)
    t_e=time.time()
    print("is_good_looking time: ",t_e-t_s)
    if flag:
        return '哇，李晗女神！这张脸我给 '+str(random.randint(95,99))+' 分！'
    else:
        return 'your rank: '+str(rank_pic("temp/"+f_name))
        #return random.randint(49,85)

#print(my_rank("1.jpg"))



def ocr_via_oxford(input, key_, type='url', dect_area=(210,1200,1100,330)):
    def _if_contains(l_a,l_b):#  a in b
        a=[int(i) for i in l_a]
        b=[int(i) for i in l_b]
        return ( a[0]>b[0] and a[1]>b[1] and 
                (a[0]+a[2])<(b[0]+b[2]) and 
                (a[1]+a[3])<(b[1]+b[3]) )

    cl = Client(key_)

    ocr_obj=cl.vision.ocr({'detectOrientation':False, 'language':'zh-Hant', type:input})

    plain_list=[k['text'] for i in ocr_obj['regions'] for j in i['lines'] for k in j['words']]
    return ''.join(plain_list).strip()


if __name__ == '__main__':
    f_in='fetchimage.jpg'
    print(ocr_via_oxford(f_in, _api_keys['projectoxford']['vision']['sub']))



