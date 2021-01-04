#!/usr/bin/python3.6
import sys
import cmd
import time
import redis
import threading
import json


run = True
thread  = None
r = None
process_name  = None
resp_message = None
job_id = None


def monitor():
    global thread
    global run
    global r
    global resp_message
    global job_id


    r = redis.Redis(host='localhost', port=6379)
    p = r.pubsub()
    p.subscribe('job:stop')

    print ('monitoring channel job')
    for m in p.listen():
        if m['type'] == 'message':
            message = json.loads(m['data'])
            print(message['job_id'])
            print(job_id)
            if str(message['job_id']) == str(job_id) :
                print('will stop')
                resp_message = message
                run = False


if __name__ == '__main__':
    job_id = sys.argv[1]
    thread = threading.Thread(target=monitor)
    thread.setDaemon(True)
    thread.start()

    while run :
        print('running test.... new')
        time.sleep(10)


    r.publish('job:stopped', json.dumps({"job_id":job_id}))
