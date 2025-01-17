class E_GetIPError(Exception):
    pass

class E_AlreadyLoggedIn(Exception):
    def __init__(self, ip, expire_time, message="User is already logged in"):
        super().__init__(message)
        self.ip = ip
        self.expire_time = expire_time
        
class E_ServerNotFound(Exception):
    pass

class E_DatabaseError(Exception):
    pass

class E_InternalError(Exception):
    pass

class E_MQ_Not_Exist(Exception):
    pass

class E_MQ_Not_Ready(Exception):
    pass

class E_API_Request_Error(Exception):
    pass

class E_Retry(Exception):
    pass