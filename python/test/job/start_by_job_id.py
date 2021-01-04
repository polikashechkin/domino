import redis
r = redis.StrictRedis(host='localhost', port=6379)
r.publish('job:start', '{"JOB_ID":"27"}')



