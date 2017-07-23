__author__ = 'Mr.Bool'
import socketserver
import json
import configparser
from conf import settings
import os
import hashlib
import time

STATUS_CODE={
    250:"没有动作命令,e.g:{'action':'get','filename':'test.py','size':344}",
    251:"没有该方法",
    252:"有空数据",
    253:"错误用户名或密码",
    254:"验证成功",
    255:'客户端传过来的文件名为空',
    256:'文件不存在',
    257:'文件已经准备好',
    258:'md5生成',
    259:'服务器准备接受文件'
}
class FTPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        while True:
            print('有用户连接服务器')
            self.data=self.request.recv(1024).strip()
            print(self.data)
            if not self.data:
                print("客户端已关闭！！")
                break

            data=json.loads(self.data.decode())
            print(data)
            if data.get('action') is not None:
                if hasattr(self,'_%s'%data.get('action')):
                    func=getattr(self,'_%s'% data.get('action'))
                    func(data)
                else:
                    print('没有该方法')
                    self.send_response(251)
            else:
                print('没有动作命令')
                self.send_response(250)
    def send_response(self,status_code,data=None):
        response={'status_code':status_code,'status_msg':STATUS_CODE[status_code]}
        if data:
            response.update(data)
        self.request.send(json.dumps(response).encode())
        print('hello')

    def authenticate(self,username,password):
        '验证用户合法性，合法返回用户数据'
        config = configparser.ConfigParser()
        config.read(settings.ACCOUNT_FILE)
        if username in config.sections():
            _password=config[username]["Password"]
            if _password==password:
                print("验证成功")
                config[username]['Username']=username
                return config[username]
            else:
                print('验证失败')
    def _put(self,*args,**kwargs):
        data=args[0]
        userpath=''
        if data.get('filename') is None:
            '沒有指定位置'
            pass
        elif os.path.exits(data.get('filename')):
            '有这个路径'
            userpath=data.get('filename')
            pass
        else:
            '没有这个路径，创造这个路径'
            os.makedirs(data.get('filename'))
            userpath=data.get('filename')
        self.send_response(259)
        file_size=data.get('filesize')
        receivesize=0
        wf=open(userpath,'wb')
        while receivesize<file_size:
            data=self.request.recv(1024)
            wf.write(data)
            receivesize+=len(data)
        else:
            print('接受完成')
            wf.close
        pass
    def _get(self,*args,**kwargs):
        data=args[0]
        if data.get('filename') is None:
            self.send_response(255)
        userhomedir='%s/%s'%(settings.USER_HOME,self.user['Username'])
        fileabspath='%s/%s'%(userhomedir,data.get('filename'))
        print(fileabspath)
        if os.path.isfile(fileabspath):
            print('文件存在,还没有确定用户访问范围')
            file_size=os.path.getsize(fileabspath)
            self.send_response(257,data={'file_size':file_size})
            # self.request.recv(1)#等待客户端确认
            rf=open(fileabspath,'rb')

            if data.get('md5'):
                md5_obj=hashlib.md5()
                for line in rf:
                    md5_obj.update(line)
                    self.request.send(line)
                # while True:
                #     print('12334445')
                #     data=self.request.recv(1).strip()
                #     print('=====',data)
                #     if data !='':
                #         print('md5加密')
                #         md5_val=md5_obj.hexdigest()
                #         self.send_response(258,data={'md5_value':md5_val})
                #         print(md5_val)
                #         print('传送成功')
                #         rf.close()
                else:
                    time.sleep(0.3)
                    print('md5加密')
                    md5_val=md5_obj.hexdigest()
                    self.send_response(258,data={'md5_value':md5_val})
                    print(md5_val)
                    print('传送成功')
                    rf.close()
            else:
                for line in rf:
                    self.request.send(line)
                else:
                    print('传送完成')
                    rf.close()
        else:
            self.send_response(256)

        pass
    def _cd(self,*args,**kwargs):
        pass
    def _ls(self,*args,**kwargs):
        pass
    def _auth(self,*args,**kwargs):
        data=args[0]
        if data.get("username") is None or data.get('password') is None:
            self.send_response(252)
        user=self.authenticate(data.get('username'),data.get("password"))
        if user is None:
            self.send_response(253)
        else:
            print("通过验证",user)
            self.user=user
            self.send_response(254)