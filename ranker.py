import base64, json, time, os, threading, re
import urllib.parse, urllib.request
from PIL import Image

def getRawImgUrl(infile):
    file_in=open(infile,'rb')
    img_base64=base64.b64encode(file_in.read())
    file_in.close()

    uploadUrl='http://kan.msxiaobing.com/Api/Image/UploadBase64'
    resp=urllib.request.urlopen(uploadUrl,data=img_base64)
    imgUrl='http://imageplatform.trafficmanager.cn'+json.loads(resp.read().decode('utf-8'))['Url']
    #print(imgUrl)
    return imgUrl


def getRespImgUrl(imgUrl):
    sys_time=int(time.time())
    CompUrl='http://kan.msxiaobing.com/Api/ImageAnalyze/Comparison'
    form={
        'msgId':str(sys_time)+'233',
        'timestamp':sys_time,
        'senderId':'mtuId'+str(sys_time-242)+'717',
        'content[imageUrl]':imgUrl,
        }
    
    resp=urllib.request.urlopen(CompUrl,
        data=urllib.parse.urlencode(form).encode('utf-8'))
    respUrl=json.loads(resp.read().decode('utf-8'))['content']['imageUrl']
    return respUrl


def saveUrlAsFile(respurl,outfile):
    file_out=open(outfile,'wb')
    resp=urllib.request.urlopen(respurl)
    file_out.write(resp.read())
    file_out.close()


def getScoreImg(inPic, outPic):
    rawurl=getRawImgUrl(inPic)      #no good
    respurl=getRespImgUrl(rawurl)
    saveUrlAsFile(respurl, inPic+'.temp')
    img1=Image.open(inPic+'.temp')
    box=(240,1300,1210,1520)    #(left, upper, right, lower)
    img2=img1.crop(box)
    img1.close()
    img2.save(outPic)#no good
    os.remove(inPic+'.temp')


def getNumViaBaiduOCR(infile, apikey):
    input_file=open(infile,'rb')
    img_base64=base64.b64encode(input_file.read())
    url = 'http://apis.baidu.com/apistore/idlocr/ocr'
    data={}
    data['fromdevice'] = "pc"
    data['clientip'] = "10.10.10.0"
    data['detecttype'] = "LocateRecognize"
    data['languagetype'] = "CHN_ENG"
    data['imagetype'] = "1"
    data['image'] = img_base64

    decode_data=urllib.parse.urlencode(data)
    req=urllib.request.Request(url,data=decode_data.encode('utf-8'))
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    req.add_header("apikey", apikey)#baidu api key
    resp=urllib.request.urlopen(req)
    content=json.loads(resp.read().decode('utf-8'))
    textStr = content['retData'][0]['word']

    match=re.search(r'\d{2}|\d\.\d',textStr)
    pointStr=match.group(0)
    point=float(pointStr)
    if point <= 10:      # . is identified
        point *= 10
    if point <= 20:      # 7 is identified as 1
        point += 60
    return point


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



def _if_contains(l_a,l_b):#  a in b
    a_x=int(l_a[0])
    a_y=int(l_a[1])
    a_w=int(l_a[2])
    a_h=int(l_a[3])

    b_x=int(l_b[0])
    b_y=int(l_b[1])
    b_w=int(l_b[2])
    b_h=int(l_b[3])

    return a_x>b_x and a_y>b_y and (a_x+a_w)<(b_x+b_w) and (a_y+a_h)<(b_y+b_h)


def ocr_via_oxford(f_in, key_, dect_area=(210,1200,1100,330)):
    """(210,1200,1100,330)"""

    cl = Client(key_)
    ocrObject=cl.vision.ocr({'detectOrientation':False,
        'language':'zh-Hant',
        'path':f_in})
    plain_list=[]
    if ocrObject['regions']!=[]:
        for i in ocrObject['regions']:
            for j in i['lines']:
                for k in j['words']:
                    word_area=k["boundingBox"].split(',')
                    if _if_contains(word_area, dect_area):
                        plain_list.append(k['text'])

                plain_list.append('\n')
            plain_list.append('\n\n')

    return ''.join(plain_list).strip()





if __name__ == '__main__':
    f_in='fetchimage.jpg'
    print(ocr_via_oxford(f_in, _api_keys['projectoxford']['vision']['sub']))



