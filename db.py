import pymongo

class Newdb():
    def __init__(self,db_addr,db_port,db_name):
        self.db_addr = db_addr
        self.db_port = db_port
        self.db_name = db_name
    
    def init_db(self):
        db_client = pymongo.MongoClient(self.db_addr,self.db_port)
        db = db_client[self.db_name]
        return db
        
    
class Controldb():
    def __init__(self,db,db_col):
        self.db = db
        self.db_col = db_col
    
    
    def db_insert(self,data):
        if isinstance(type(data),dict):
            ins_db = self.db[self.db_col].insert_one(data)
        else:
            ins_db = self.db[self.db_col].insert_many(data)
        return ins_db

    def db_find(self,data):
        fin_db = self.db[self.db_col].find(data)
        return fin_db
    
    def db_change(self):
        pass
    
    def db_del(self):
        pass
    
    def db_max(self):
        pass
    
    def db_min(self):
        pass

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