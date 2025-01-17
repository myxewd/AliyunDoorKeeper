from middleware import *

rpool = redis.ConnectionPool(
    host=appconf['redis']['host'],
    port=appconf['redis']['port'],
    db=appconf['redis']['db'],
    socket_connect_timeout=5,
    socket_timeout=5
)