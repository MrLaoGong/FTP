__author__ = 'Mr.Bool'
import os,sys
import socket
import json
import optparse
import hashlib
import time
class FTPClient(object):
    def __init__(self):
        self.parse=optparse.OptionParser()
        self.parse.add_option("-s","--host",dest="host",help="ip地址")
        self.parse.add_option("-p","--port",dest="port",type='int',help="端口号")
        self.parse.add_option("-U","--username",dest="username",help="登陆用户名")
        self.parse.add_option("-P","--password",dest="password",help="登陆密码")
        self.option,self.args=self.parse.parse_args()
        print(dir(self.option))
        self.verify_args()
        self.makeconnect()

        pass
    def makeconnect(self):
        self.sock=socket.socket()
        print(self.option.host,'---',self.option.port)
        self.sock.connect((self.option.host,self.option.port))
    def verify_args(self):
        if self.option.username is not None and self.option.password is not None:
            pass
        elif self.option.username is None and  self.option.password is None:
            pass
        else:
            exit('Err:用户名必须同时出现或者同时没有')

        if self.option.host and self.option.port:
            if self.option.port>0 and self.option.port<65535:
                return True
            else:
                exit('Err:port 必须 大于0 小于65535')

    def interactive(self):
        if self.authenticate():
            print('----server-----')
            while True:
                choice=input('[%s]:'%self.user).strip()
                list_cmd=choice.split()
                if hasattr(self,'_%s'%list_cmd[0]):
                    func=getattr(self,'_%s'%list_cmd[0])
                    func(list_cmd)
                else:
                    print('输入命令没找到')
    def __md5_requeired(self,list_cmd):
        '是否使用md5校验'
        if '--md5' in list_cmd:
            return True

    def _put(self,list_cmd):
        print('put功能',list_cmd)
        'put 文件位置 放的位置'
        if  os.path.isfile(list_cmd[1]):
            '文件位置正确'
            file_size=os.path.getsize(list_cmd[1])
            if len(list_cmd)==2:
                data_header={
                    'action':'put',
                    'filesize':file_size,
                    'username':self.option.username
                }
            else:
                data_header={
                    'action':'put',
                    'filename':list_cmd[2],
                    'filesize':file_size,
                    'username':self.option.username
                }
            self.sock.send(json.dumps(data_header).encode('utf-8'))
            response=self.get_response()
            print(response)
            if response.get('status_code')==259:
                '开始发送'
                print('开始发送')
                rf = open(list_cmd[1],'rb')
                for line in rf:
                    self.sock.send(line)
                else:
                    print('发送完成')
                    rf.close()
                pass
        else:
            print('没有该文件')
        pass

    def _ls(self,list_cmd):
        print('ls功能',list_cmd)
        if len(list_cmd)==1:
             print('根目录')
             data_header={
                'action':'ls'
             }
        else:
             print('根据路径搜索')
             data_header={
                        'action':'ls',
                        'path':list_cmd[1]
                    }
        self.sock.send(json.dumps(data_header).encode('utf-8'))
        response=self.get_response()
        if response.get('status_code')==260:
            filepath=response.get('filepath')
            print('文件夹下文件为：',filepath)
        else:
            print('该文件夹错误')
    def _get(self,list_cmd):
        print('get功能',list_cmd)
        if len(list_cmd)==1:
            print('没有文件位置信息')
            return

        data_header={
            'action':'get',
            'filename':list_cmd[1],
            'username':self.option.username
        }
        if self.__md5_requeired(list_cmd):
            data_header['md5']=True
        self.sock.send(json.dumps(data_header).encode('utf-8'))
        response=self.get_response()
        print(response)
        if response.get('status_code')==257:
            print('准备接受')
            # self.sock.send(b'1')
            recivesize=0
            wf=open(r'%s'%list_cmd[1],'wb')
            if self.__md5_requeired(list_cmd):
                md5_obj=hashlib.md5()
                progress=self.show_progress(response['file_size'])
                progress.__next__()
                while recivesize<response.get('file_size'):
                    data=self.sock.recv(1024)
                    md5_obj.update(data)
                    wf.write(data)
                    recivesize+=len(data)
                    try:
                        progress.send(len(data))
                    except StopIteration as e:
                        print('100%')
                        print('接收完成')
                        md5_val=md5_obj.hexdigest()
                        md5_response=self.get_response()
                        print(md5_val,md5_response)
                        if md5_response.get('status_code')==258:
                            if md5_val==md5_response.get('md5_value'):
                                print('文件一致性校验成功')
                        wf.close()
                # else:
                #     print('接收完成')
                #     md5_val=md5_obj.hexdigest()
                #     md5_response=self.get_response()
                #     print(md5_val,md5_response)
                #     if md5_response.get('status_code')==258:
                #         if md5_val==md5_response.get('md5_value'):
                #             print('文件一致性校验成功')
                #     wf.close()
            else:
                progress=self.show_progress(response['file_size'])
                progress.__next__()
                while recivesize<response.get('file_size'):
                    data=self.sock.recv(1024)
                    wf.write(data)
                    recivesize+=len(data)
                    try:
                        progress.send(len(data))
                    except StopIteration as e:
                        print('100%')
                else:
                    print('接收完成')
                    wf.close()
        else:
            print(response.get('status_msg'))

    def show_progress(self,total):
        received_size=0
        current_size=0
        while received_size<total:
            if int((received_size/total)*100)>current_size:
                print('#')
                current_size=int((received_size/total)*100)
            new_size=yield
            received_size+=new_size
    def authenticate(self):
        if self.option.username:
            print(self.option.username,'--',self.option.password)
            return self.get_auth_result(self.option.username,self.option.password)
        else:
            count=0
            while count<3:
                username=input('请输入用户名').strip()
                password=input('请输入密码').strip()
                count+=1
                '验证'
                return self.get_auth_result(username,password)
            exit()
    def get_auth_result(self,username,password):
        data={
            'action':'auth',
            'username':username,
            'password':password
        }
        self.sock.send(json.dumps(data).encode('utf-8'))
        response= self.get_response()
        if response.get('status_code')==254:
            print("验证成功")
            self.user=username
            return True
        else:
            print(response.get('status_msg'))
            return False

    def get_response(self):
        data=self.sock.recv(1024)
        data=json.loads(data.decode())
        return data



if __name__=='__main__':
    ftp=FTPClient()
    ftp.interactive()#英文单词是交互的意思