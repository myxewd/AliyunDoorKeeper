from middleware import *

r=redis.Redis(host=appconf['redis']['host'],
                    port=appconf['redis']['port'],
                    db=appconf['redis']['db'])

