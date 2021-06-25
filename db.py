#使用MongoDB作为主要的数据库存储方案，对于数据库的操作建立相关的函数调用

import pymongo
import json

class Dbctl:
    def __init__(self, address, port, db_name):
        self.address = address
        self.port = port
        self.db = db_name
    
    def db_link(self, col_name):
        return pymongo.MongoClient(self.address, self.port)[self.db][col_name]

    def db_insert(self, data):
        if not isinstance(data, tuple):
            return
        else:
            pass

    def db_search(self, *data):
        pass

    def db_update(self):
        pass

class Newdb():
    def __init__(self,mongodb,db_name):
        self.mongodb = mongodb
        self.db_name = db_name
    
    def init_db(self):
        if isinstance(self.mongodb,dict):
            db = pymongo.MongoClient(self.mongodb['addr'],self.mongodb['port'])[self.db_name]
            return db
        else:
            print("输入类型错误")
            exit()
        
    
class Controldb():
    def __init__(self,db,db_col):
        self.db = db
        self.db_col = db_col
    
#数据库插入内容
    def db_insert(self,data):
        if isinstance(type(data),dict):
            ins_db = self.db[self.db_col].insert_one(data)
        else:
            ins_db = self.db[self.db_col].insert_many(data)
        return ins_db

#数据库查找
    def db_find(self,data):
        fin_db = self.db[self.db_col].find(data)
        return fin_db

#修改数据库内容    
    def db_change(self,query,data):
        chg_db = self.db[self.db_col].update_one(query,data)
        return chg_db

#删除数据库内容    
    def db_del(self,data):
        del_db = self.db[self.db_col].remove(data)
        return del_db

#查询数据库内数据极值    
    def db_extreme(self,mod,data):
        if mod == "max":
            db_data = self.db[self.db_col].find(data)
        elif mod == "min":
            db_data = self.db[self.db_col].find(data)
        else:
            db_data = self.db[self.db_col].find(data)
        return db_data


# mydb = Newdb('172.16.1.2',27017,'python')
# db_data = [{'key1':1,"key2":2,"key3":3},{'key1':3,"key2":4,"key3":8}]
# mycol = Controldb(mydb.init_db(),'test1')
# print(mydb)
# print(mydb.init_db())
# print(mydb.__dict__)
# print(mycol.db_insert(db_data))
# print(mycol.__dict__)
# print(type(mycol.db_find({'key1': {"$lte": 3}})))
# for i in mycol.db_find({'key1': {"$lte": 3}}):
#     print(i)