from loguru import logger

class Device:
    name: str
    topic:str
    access_token: str

    
    def __init__(self,name:str,topic: str, access_token:str):
        self.ip = name
        self.topic = topic
        self.access_token = access_token
    
