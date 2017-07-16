__author__ = 'Mr.Bool'
import optparse
import socketserver
from core.ftp_server import FTPHandler
from conf import settings
class ArgvHandler(object):
    def __init__(self):
        self.parse=optparse.OptionParser()
        self.parse.add_option("-s","--host",dest="host",help="服务ip")
        self.parse.add_option("-p","--port",dest="port",help="服务端口")
        (option,args)=self.parse.parse_args()
        self.verify_args(option,args)
    def verify_args(self,option,args):
        if hasattr(self,args[0]):
            func=getattr(self,args[0])
            func()
        else:
            print(self.parse.print_help())
    def start(self):
        print("----the server is start------")
        server=socketserver.ThreadingTCPServer((settings.HOST,settings.PORT),FTPHandler)
        server.serve_forever()
