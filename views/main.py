from views import *
from app.aliyundk import *
from config.servers import get_target
from datetime import datetime, timedelta

@AliyunDK.route("/")
def index():
    usr_ip = get_real_ip(request)
    try:
        get_target().add(usr_ip)
        return render_template('approved.html', 
                                ip=usr_ip,
                                time=format_time(appconf['expiry_time']),
                                server=appconf['server'],
                                end_time=(datetime.now()+timedelta(seconds=appconf['expiry_time'])).strftime("%m/%d/%Y %H:%M:%S"))
    except E_AlreadyLoggedIn as e:
        return render_template('linked.html', 
                                ip=usr_ip,
                                end_time=e.expire_time.strftime("%m/%d/%Y %H:%M:%S"))
    except Exception as e:
            return render_template('error.html', 
                                error_msg=e)