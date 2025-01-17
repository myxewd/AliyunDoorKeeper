from config import appconf
from config.servers import add_target
from app import *
from middleware.arabbitmq import get_channel, init as mq_init

def remove_callback(sg_id, ip):
    # Cache in Redis has been deleted
    queue_data_del = {
        "action": "del",
        "sg_id": sg_id,
        "ip": ip,
        "retry": 0
    }
    while True:
        try:
            get_channel().basic_publish(
                exchange='',
                routing_key=f"{appconf['rabbitmq']['queue_name']}.dead",
                body=json.dumps(queue_data_del),
                properties=pika.BasicProperties(delivery_mode=2)
            )
            break
        except (pika.exceptions.StreamLostError, pika.exceptions.ChannelWrongStateError):
            mq_init()
        except Exception as e:
            # If other error occurs here, the program cannot revoke the permission
            #   by itself, so you should reset the security group policy 
            #   and clear the cache in Redis manually (or by automation component based on log analysis)
            #
            # But normally, the program shouldn't have reached this point
            print(f"Error: {e}")
            break

def get_server():
    add_target(appconf['server'], appconf['sg_id'], remove_callback)

