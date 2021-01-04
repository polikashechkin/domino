import redis
r = redis.StrictRedis(host='localhost', port=6379)
r.publish('job:start', '{"proc":"test.py", "module":"domino", "account":"00674812"}')



