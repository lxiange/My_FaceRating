#!/usr/bin/python
#-*- encoding:utf-8 -*-
import tornado.ioloop
import tornado.web
import shutil
import os
import ranker
 
class UploadFileHandler(tornado.web.RequestHandler):
    def get(self):
        self.write('''
<html>
  <head><title>Upload File</title></head>
  <body>
    <form action='file' enctype="multipart/form-data" method='post'>
    <input type='file' name='file', style="width:920px;height:300px;font-size:90px;"/><br/>
    <input type='submit' value='submit', style="width:600px;height:300px;font-size:50px;"/>
    </form>
  </body>
</html>
''')
 
    def post(self):
        upload_path=os.path.join(os.path.dirname(__file__),'files')  #文件的暂存路径
        file_metas=self.request.files['file']    #提取表单中‘name’为‘file’的文件元数据
        for meta in file_metas:
            filename=meta['filename']
            filepath=os.path.join(upload_path,filename)
            with open(filepath,'wb') as up:      #有些文件需要已二进制的形式存储，实际中可以更改
                up.write(meta['body'])
            #self.write('finished!')
            #self.write('files/'+filename+'\n')
            import time
            start_time=time.time()
            out_put=ranker.my_rank('files/'+filename)
            self.write(out_put)
            end_time=time.time()
            self.write('<br></br> spent: '+str(end_time - start_time)+' seconds')
 
app=tornado.web.Application([
    (r'/file',UploadFileHandler),
])
 
if __name__ == '__main__':
    app.listen(8888)
    tornado.ioloop.IOLoop.instance().start()