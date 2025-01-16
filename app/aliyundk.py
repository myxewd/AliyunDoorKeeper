from config import appconf
from config.servers import add_target
from app import *
from middleware.aredis import r

def remove_callback(sg_id, ip):
    print("removed !", sg_id, ip)

def get_server():
    add_target(appconf['server'], appconf['sg_id'], remove_callback)

