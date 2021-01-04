import os, sys, datetime, requests, pickle, json, uuid
import xml.etree.ElementTree as ET
from multiprocessing import Process, Queue
from time import sleep

DIR = os.path.dirname(os.path.abspath(__file__))
os.makedirs('/DOMINO/data/test', exist_ok=True)
VALUES_FILE = '/DOMINO/data/test/questions'
VALUES = {}

try:
    with open(os.path.join(DIR, VALUES_FILE)) as f:
        VALUES = json.load(f)
except:
    pass

def question(q):
    old_value = VALUES.get(q, '')
    new_value = input(f'{q} [{old_value}] ? ')
    if new_value != '':
        VALUES[q] = new_value
        with open(os.path.join(DIR, VALUES_FILE), 'w') as f:
            json.dump(VALUES, f)
        return new_value
    else:
        return old_value

def h(text):
    print()
    print(text.upper())
    d = ('-'* len(text))
    print(d)

class TestRequest:
    def __init__(self, server, product):
        self.server = server
        self.product = product
        
        self.r = None
        self.time_ms = 0

    @property
    def url(self):
        return self.r.url if self.r is not None else ''

    @property
    def status_code(self):
        return self.r.status_code if self.r is not None else ''

    @property
    def text(self):
        return self.r.text if self.r is not None else ''

    def request(self):
        query = 'domino/active/python/distro.get_versions'
        start = datetime.datetime.now()
        data = {'product': self.product}
        self.r = requests.post(f'https://{self.server}/{query}',  data=data)
        self.time_ms = round((datetime.datetime.now() - start).total_seconds() * 1000, 3)

def test(r):
    r.request()
    h('Запрос')
    print(r.url)
    h(f'Ответ : {r.status_code} : {r.time_ms} ms : {len(r.text)}')
    print(r.text)

if __name__ == "__main__":
    
    server = question('Сервер')
    product = question('Продукт')

    r = TestRequest(server, product)
    test(r)
