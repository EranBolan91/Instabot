from datetime import datetime
class Proxy:
    def __init__(self, host, username, password, port):
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        #self.date = datetime.now().strftime("%d/%m/%Y %H:%M")