from views import *
from app.aliyundk import *
from config.servers import get_target

@AliyunDK.route("/")
def index():
    usr_ip = get_real_ip(request)
    try:
        get_target().add(usr_ip)
        return render_template('approved.html', 
                                ip=usr_ip,
                                server=appconf['server'],
                                end_time=datetime.now().strftime("%B %d, %Y"))
    except E_AlreadyLoggedIn as e:
        return render_template('linked.html', 
                                ip=usr_ip,
                                end_time=e.expire_time.strftime("%B %d, %Y"))
    except Exception as e:
            return render_template('error.html', 
                                error_msg=e)