-- KEYS[1]: self.queue_name
-- KEYS[2]: f"adkusr:{self.name}"
-- ARGV[1]: ip

local key_name = KEYS[2] .. "." .. ARGV[1]
redis.call("LREM", KEYS[1], 0, ARGV[1])
redis.call("DEL", key_name)