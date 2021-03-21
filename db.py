import pymongo

class Newdb():
    def __init__(self,db_addr,db_port,db_name,db_col):
        self.db_addr = db_addr
        self.db_port = db_port
        self.db_name = db_name
        self.db_col = db_col
    
    def init_db(self):
        db_client = pymongo.MongoClient(self.db_addr,self.db_port)
        db = db_client[self.db_name]
        col = db[self.db_col]
        return col.insert_one({'key': 1,"value": 'test1'})
        
    
class Controldb():
    def __init__(self,db,data):
        self.db = db
        self.data = data
    
    def db_insert(self):
        pass

mydb = Newdb('192.168.0.5',27017,'mytest','test1')
print(mydb)
print(mydb.init_db())
print(mydb.__dict__)