'''
通过修改数据库内容实现动态调整运行状态而不需要重启程序
'''

import db
import json

json_file = 'config/cfg.json'

class Json_ctr():
    def __init__(self, file):
        self.file = file
        
    def json_read(self):
        with open(self.file,'r') as cfg:
            return json.load(cfg)
        
    def json_write(self, data):
        with open(self.file,'w') as cfg:
            json.dump(data,cfg)
            cfg.close()
            print("Data has been updated!")

class Db_ctr():
    def __init__(self):
        print("开始进行运行参数配置！")
        print("*" * 20)
     
    def start_start(self):
        pass 
    
      
            