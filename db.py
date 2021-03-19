import pymongo

class db_call():
    def __init__(self,db_addr,db_port,db_name,db_col,data):
        self.db_addr = db_addr
        self.db_port = db_port
        self.db_name = db_name
        self.db_col = db_col
        self.data = data
    
    def link_db(self):
        db_client = pymongo.MongoClient("mongodb://{self.db_addr}/{self.db_port}/")
        db = db_client[self.db_name]
        col = db[self.db_col]
        return col
    
    def insert_data(self):
        link_db().insert_many(self.data)
        print("all data inserted!")
    
    def db_search(self)
        pass

