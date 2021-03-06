'''
通过修改数据库内容实现动态调整运行状态而不需要重启程序
'''

import db
import json

class Json_ctr():
    json_file = 'config/cfg.json'
    def __init__(self):
        pass
    
    @classmethod    
    def json_read(cls):
        with open(cls.json_file,'r') as cfg:
            return json.load(cfg)
    
    @classmethod    
    def json_write(cls, data):
        with open(cls.json_file,'w') as cfg:
            json.dump(data,cfg)
            cfg.close()
            print("配置信息已更新！")

class Db_ctr():
    def __init__(self):
        pass
     
    def start_start(self, db_chr):
        get_run_info = Json_ctr().json_read()
        print(get_run_info)
        the_db = db.Newdb(get_run_info['mongodb']['addr'],get_run_info['mongodb']['port'],get_run_info['db'])
        the_new_col = input("请输入新的修改单元：")
        db.Controldb.db_change()

    
      
            