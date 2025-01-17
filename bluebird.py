# -*- coding: utf-8 -*-
# 青鸟·信使

from config import appconf
from config.exceptions import *
import time
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
queue_name = f"{appconf['rabbitmq']['queue_name']}.dead"
def mq_init():
    global queue_name
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
                                                                heartbeat=30))
    else:
        mq_conn = pika.BlockingConnection(pika.ConnectionParameters(host=appconf['rabbitmq']['host'],
                                                                port=appconf['rabbitmq']['port'],
                                                                virtual_host=appconf['rabbitmq']['virtual_host'],
                                                                heartbeat=30))
    mq_channel = mq_conn.channel()
    mq_channel.queue_declare(queue=queue_name) 
    return mq_conn, mq_channel

# listen to the dead letter queue



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
        retry_2 = 0
        while True:
            retry_2 = retry_2 + 1
            if retry_2 > 3:
                logger.error(f"Unable to send retry revoke message of sg_id:{sg_id}; ip:{ip}")
                break
            mq_conn, mq_channel = mq_init()
            try:
                mq_channel.basic_publish(exchange='',
                                         routing_key=queue_name,
                                        body=json.dumps(data),
                )
                break
            except (pika.exceptions.StreamLostError, 
                    pika.exceptions.ChannelWrongStateError,
                    pika.exceptions.AMQPConnectionError):
                pass
            finally:
                try:
                    if mq_conn and not mq_conn.is_closed:
                        mq_conn.close()
                except Exception as e:
                    logger.error(f"Error while closing connection: {e}")
            
    except Exception as e:
        logger.error(f"{e}")

def main():
    while True:
        try:
            mq_conn, mq_channel = mq_init()
            logger.info('Bluebird is waiting for messages. To exit press CTRL+C')
            mq_channel.basic_consume(queue=queue_name, on_message_callback=work, auto_ack=True)
            mq_channel.start_consuming()
        except pika.exceptions.AMQPConnectionError as e:
            logger.error(f"Connection error: {e}. Retrying in 5 seconds...")
            time.sleep(5)
        except pika.exceptions.ChannelError as e:
            logger.error(f"Channel error: {e}. Retrying in 5 seconds...")
            time.sleep(5)
        except KeyboardInterrupt:
            logger.info("Interrupted by user. Exiting...")
            break
        finally:
            try:
                if mq_conn and not mq_conn.is_closed:
                    mq_conn.close()
            except Exception as e:
                logger.error(f"Error while closing connection: {e}")


if __name__ == "__main__":
    main()



