import pymongo

class Newdb():
    def __init__(self,db_addr,db_port,db_name,db_col):
        self.db_addr = db_addr
        self.db_port = db_port
        self.db_name = db_name
        self.db_col = db_col
    
    def init_db(self):
        self.db_client = pymongo.MongoClient(self.db_addr,self.db_port)
        self.db = self.db_client[self.db_name]
        self.col = self.db[self.db_col]
        self.col.insert_one({'key': 1,"value": 'test1'})
        
    
class Controldb():
    def __init__(self,db,data):
        self.db = db
        self.data = data
    
    def db_insert(self):
        pass

mydb = Newdb('192.168.0.5',27017,'mytest','test1')
print(mydb)
print(type(mydb))