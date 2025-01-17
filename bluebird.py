# -*- coding: utf-8 -*-
# 青鸟·信使

from config import appconf
from config.exceptions import *
import logging
import json
from middleware.aredis import redis, rpool
import pika
from sdk.alisdk import APIRequest

logging.getLogger('pika').setLevel(logging.WARNING)
logging.getLogger('urllib3.connectionpool').setLevel(logging.WARNING)
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.StreamHandler()
                    ])
logger = logging.getLogger('bluebird')

r=redis.Redis(connection_pool=rpool)
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
                                                            credentials=credentials))
else:
    mq_conn = pika.BlockingConnection(pika.ConnectionParameters(host=appconf['rabbitmq']['host'],
                                                            port=appconf['rabbitmq']['port'],
                                                            virtual_host=appconf['rabbitmq']['virtual_host']))
mq_channel = mq_conn.channel()

# listen to the dead letter queue

queue_name = f"{appconf['rabbitmq']['queue_name']}.dead"
mq_channel.queue_declare(queue=queue_name)

def work(ch, method, properties, body):
    try:
        data = json.loads(body)
        action = data['action']
        if action != 'add' and action != 'del':
            raise ValueError(f'Invalid action: {action}')
        sg_id = data['sg_id']
        ip = data['ip']
        retry = data['retry']
    except Exception as e:
        logger.error(f"{e}")
        return
    if retry > appconf['bluebird']['max_retry']:
        logger.error(f"Fail to {action} {ip} from {sg_id}")
        return
    try:
        submitter = APIRequest(logger)
        if action == 'add':
            submitter.submit_add(priority=appconf['rule_priority'], 
                                 src_ip=ip, 
                                 sg_region_id=appconf['sg_region_id'], 
                                 sg_id=sg_id)
        elif action == 'del':
            submitter.submit_del(priority=appconf['rule_priority'], 
                                 src_ip=ip, 
                                 sg_region_id=appconf['sg_region_id'], 
                                 sg_id=sg_id)
            # remove queue member
            try:
                r.lrem(name=f"adkqueue:{appconf['server']}",
                    count=0,
                    value=ip) 
            except Exception as e:
                logger.error(f"Redis queue synchronization failed, ip: {ip};"
                             f"sg_id: {sg_id};"
                             f"redis_queue: adkqueue:{appconf['server']}"
                             f"{e}")
                raise E_Retry
            # queue naming rule is defined in middleware.whitelist
    except (E_API_Request_Error, E_Retry):
        #log has been recorded
        data['retry'] = retry + 1
        mq_channel.basic_publish(exchange='', 
                                 routing_key=queue_name, 
                                 body=json.dumps(data))
    except Exception as e:
        logger.error(f"{e}")
    


mq_channel.basic_consume(queue=queue_name, on_message_callback=work, auto_ack=True)
logger.info('Bluebird is waiting for messages. To exit press CTRL+C')
mq_channel.start_consuming()



