from utils import *

def get_real_ip(request):
    if appconf["behind_proxy"] == True:
        ip = request.headers.get('X-Forwarded-For')
        if not ip:
            raise E_GetIPError(f"No proxy header found")
        else:
            return ip
    else:
        return request.remote_addr