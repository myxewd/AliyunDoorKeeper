-- KEYS[1]: self.queue_name
-- KEYS[2]: f"adkusr:{self.name}"
-- ARGV[1]: ip
-- ARGV[2]: self.expiry_time
-- ARGV[3]: self.max_size

local key_name = KEYS[2] .. "." .. ARGV[1]
if redis.call("EXISTS", key_name) == 1 then
    local ttl = redis.call("TTL", key_name)
    return {"EXISTS", ttl}
end
local chk_exist = false
for i, elem in ipairs(redis.call('LRANGE', KEYS[1], 0, -1)) do
    if elem == ARGV[1] then
        chk_exist = true
        break
    end
end
if chk_exist then
    return {"EXISTS", -1}
end
redis.call("LPUSH", KEYS[1], ARGV[1])
redis.call("SET", key_name, "1", "EX", ARGV[2])
if redis.call("LLEN", KEYS[1]) > tonumber(ARGV[3]) then
    local to_be_popped = redis.call("RPOP", KEYS[1])
    redis.call("DEL", KEYS[2] .. "." .. to_be_popped)
    return {"EXCEEDED", to_be_popped}
end
return {"OK"}