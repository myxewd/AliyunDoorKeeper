from middleware import *
import requests
from requests.auth import HTTPBasicAuth

mq_inited = False
mq_conn = None
mq_channel = None
def init():
    global mq_inited
    global mq_conn
    global mq_channel
    mq_inited = False
    try:
        mq_channel.close()
        mq_conn.close()
    except Exception:
        pass
    need_login = True
    try:
        credentials = pika.PlainCredentials(appconf['rabbitmq']['user'], 
                                            appconf['rabbitmq']['password'])
    except KeyError:
        need_login = False

    if need_login:
        mq_conn = pika.BlockingConnection(pika.ConnectionParameters(host=appconf['rabbitmq']['host'],
                                                                port=appconf['rabbitmq']['port'],
                                                                virtual_host=appconf['rabbitmq']['virtual_host'],
                                                                credentials=credentials,
                                                                heartbeat=60))
    else:
        mq_conn = pika.BlockingConnection(pika.ConnectionParameters(host=appconf['rabbitmq']['host'],
                                                                port=appconf['rabbitmq']['port'],
                                                                virtual_host=appconf['rabbitmq']['virtual_host'],
                                                                heartbeat=60))
    mq_channel = mq_conn.channel()
    mq_inited = True

# init message queue
# queue_name: aliyundk_queue
# dead_exchange_name: {queue_name}.deadex
# dead_queue_name: {queue_name}.dead

init()
def query_queue(queue_name, vhost='/'):
    global mq_conn
    global mq_channel
    url = (
        f"{appconf['rabbitmq']['api']['url']}/api/queues/"
        f"{vhost}/"
        f"{queue_name}"
    )
    response = requests.get(url, auth=HTTPBasicAuth(appconf['rabbitmq']['api']['username'], 
                                                    appconf['rabbitmq']['api']['password']))
    if not response.status_code == 200:
        raise E_MQ_Not_Exist
    data = response.json()
    args = data.get("arguments", {})
    dle = args.get("x-dead-letter-exchange")
    dlq = args.get("x-dead-letter-routing-key")
    if dle is None or dlq is None:
        # it's seems that this queue is not created by aliyundk
        raise Exception("The queue has been detected to be occupied")
    return

try:
    query_queue(appconf['rabbitmq']['queue_name'])
except E_MQ_Not_Exist:
    # declare dead queue
    # if normal queue is not exist, but its dead queue exists
    # Presumably that will not happen
    # If this is the case, ask the user to manually initialize the environment

    dle_name = f"{appconf['rabbitmq']['queue_name']}.deadex"
    dlq_name = f"{appconf['rabbitmq']['queue_name']}.dead"
    mq_channel.exchange_declare(exchange=dle_name, 
                                exchange_type='direct')
    mq_channel.queue_declare(queue=dlq_name, durable=True)
    mq_channel.queue_bind(
        exchange=dle_name,
        queue=dlq_name,
        routing_key=dlq_name
    )
    mq_channel.queue_declare(queue=appconf['rabbitmq']['queue_name'], 
                             arguments={'x-dead-letter-exchange': dle_name, 
                                        'x-dead-letter-routing-key': dlq_name,
                                        'x-message-ttl': appconf['expiry_time'] * 1000},
                             durable=True)
# we cannot other exceptions here

def get_channel():
    if not mq_inited:
        raise E_MQ_Not_Ready('Please try again')
    return mq_channel