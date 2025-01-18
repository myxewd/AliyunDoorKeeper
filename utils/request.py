from config import appconf
from utils import *
from utils.ip import filter_x_forwarded_for
def get_real_ip(request):
    if appconf["behind_proxy"] == True:
        ip = filter_x_forwarded_for(xff_header=request.headers.get('X-Forwarded-For'),
                                    ips_to_remove=appconf['igonre_ips'])
        # Spelling error, will be fixed in future version
        if not ip:
            raise E_GetIPError(f"No proxy header found")
        else:
            return ip
    else:
        return request.remote_addr