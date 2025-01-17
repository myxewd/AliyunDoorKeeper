from config import *
from config.exceptions import *
from middleware.aredis import redis, rpool
from middleware.whitelist import WhiteList

target_list = []

def add_target(server_ip, sg_id, remove_callback):
    target_list.append(WhiteList(server_ip, sg_id, remove_callback, redis.Redis(connection_pool=rpool)))
    
    
def get_target():
    try:
        return target_list[0]
    except IndexError:
        raise E_ServerNotFound(f'Server not found')
