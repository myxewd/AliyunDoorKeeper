import pika.exceptions
import middleware
from middleware import *
from middleware.arabbitmq import get_channel
from middleware.arabbitmq import init as mq_init

class WhiteList:
    """
    Using redis and rabbitMQ to create a whitelist queue
    When a user logs in successfully, do four things:
    1. Verify whether key f"adkusr:{self.name}.{ip}" exists
        If it exists, throw an exception and exit the function
    2. Set a redis key f"adkusr:{self.name}.{ip}"
        and set its expiration time to {self.expiry_time}
    3. Add the user's IP address to the whitelist queue of the class through lpush
    4. Publish f"{self.sg_id}.{ip}" to a message queue, 
        set its ttl to {self.expiry_time}. Permission withdrawal is implemented by 
        other components listening for dead letter queues
    ----
    A member is removed from the whitelist,
        only in one of the following three situations:
    1. The redis key associated with the user's IP has expired
    2. The whitelist capacity reaches {self.max_size}, 
        delete the tail member of the queue
    3. (TODO) Delete whitelist IP through API
    """
    max_size = appconf['max_whitelist_size']
    expiry_time = appconf['expiry_time']
    
    def load_script(self):
        with open(os.path.join("middleware", "script", "whitelist.add.lua"), "r") as script_file:
            script_content = script_file.read()
            self.xadd = self.redis.script_load(script_content)
        with open(os.path.join("middleware", "script", "whitelist.add.undo.lua"), "r") as script_file:
            script_content = script_file.read()
            self.xadd_undo = self.redis.script_load(script_content)
    
    def __init__(self, name, sg_id, remove_callback, redis):
        self.name = name
        self.queue_name = f"adkqueue:{self.name}"
        self.sg_id = sg_id
        self.remove_callback = remove_callback
        self.redis = redis
        self.load_script()
        
        
    def add(self, ip):
        mq_channel = get_channel()
        res = []
        try:
            res = self.redis.evalsha(self.xadd,
                                     2,
                                     self.queue_name,
                                     f"adkusr:{self.name}",
                                     ip,
                                     self.expiry_time,
                                     self.max_size)
        except redis.exceptions.NoScriptError:
            self.load_script()
            raise E_DatabaseError(f"Please try again (CDB_Initing)")
        except Exception as e:
            raise E_DatabaseError(f"Script error: {e}")
        res_len = len(res)
        if res_len == 2 and res[0].decode('utf-8') == "EXISTS":
            if res[1] == -1:
                raise E_InternalError("The synchronization check failed, "
                                      "please contact the administrator; "
                                      "Or try again later")
                # Here we can also post a permission revocation message
                # However, in this case, Bluebird has not had time to revoke permission
                # So just wait for the message processing to complete is ok
            raise E_AlreadyLoggedIn(ip=ip, 
                                    expire_time=datetime.now() + timedelta(seconds=res[1]))
        elif res_len == 2 and res[0].decode('utf-8') == "EXCEEDED":
            self.remove_callback(self.sg_id, res[1])
        elif res_len == 1 and res[0].decode('utf-8') == "OK":
            pass
        else:
            # lua returns something we didn't declared
            self.redis.evalsha(self.xadd_undo,
                    2,
                    self.queue_name,
                    f"adkusr:{self.name}",
                    ip)
            raise E_InternalError("Unknown error")
        
        # publish a add message directly to dead letter queue
        queue_data_add = {
            "action": "add",
            "sg_id": self.sg_id,
            "ip": ip,
            "retry": 0
        }
        # publish a delayed message to mq
        queue_data_del = {
            "action": "del",
            "sg_id": self.sg_id,
            "ip": ip,
            "retry": 0
        }
        retry = 0
        while True:
            retry = retry + 1
            if retry > 3:
                self.redis.evalsha(self.xadd_undo,
                    2,
                    self.queue_name,
                    f"adkusr:{self.name}",
                    ip)
                raise E_InternalError("System Message Component State Abnormal")
            try:
                # We publish the del command to mq in the first order
                # in order to avoid exception happened on the second step
                # when a add command has already been published
                mq_channel.basic_publish(
                    exchange='',
                    routing_key=appconf['rabbitmq']['queue_name'],
                    body=json.dumps(queue_data_del),
                    properties=pika.BasicProperties(delivery_mode=2)
                )
                mq_channel.basic_publish(
                    exchange='',
                    routing_key=f"{appconf['rabbitmq']['queue_name']}.dead",
                    body=json.dumps(queue_data_add),
                    properties=pika.BasicProperties(delivery_mode=2)
                )
                break
            except (pika.exceptions.StreamLostError, 
                    pika.exceptions.ChannelWrongStateError,
                    pika.exceptions.AMQPConnectionError):
                try:
                    mq_init()
                except Exception as e:
                    pass
            except Exception as e:
                self.redis.evalsha(self.xadd_undo,
                    2,
                    self.queue_name,
                    f"adkusr:{self.name}",
                    ip)
                raise Exception(f"MQ error: {e}")
        
        
        # We use lua script to ensure atomicity
        # if r.sismember(self.set_name, ip):
        #     raise E_AlreadyLoggedIn(ip=ip, 
        #                             expire_time=datetime.now() + timedelta(r.ttl(ip)))
        # r.lpush(self.queue_name, ip)
        # r.sadd(self.set_name, ip)
        # r.set(name=f"adkusr:{self.name}.{ip}", ex=self.expiry_time)
        # if r.llen(self.queue_name) > self.max_size:
        #     to_be_poped = r.rpop(self.queue_name)
        #     r.srem(self.set_name, to_be_poped)
        #     r.delete(f"adkusr:{self.name}.{to_be_poped}")
        #     self.remove_callback(self.sg_id, to_be_poped.decode('utf-8'))