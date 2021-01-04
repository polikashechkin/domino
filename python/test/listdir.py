import os, sys, datetime, requests, pickle, json
python = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(python)

from domino.server import Server, GUID
from domino.cli  import print_comment, Console, print_header, print_warning
from domino.globalstore import GlobalStore

if __name__ == "__main__":
    c = Console(__file__)
    server = c.input('server')
    method = 'public.listdir'
    params= {}
    params['path'] = c.input('path')
    r = requests.get(f'https://{server}/domino/active/python/{method}', params)
    print(r.url)
    print_header(r.status_code)
    print_warning(r.text)
    names = json.loads(r.text)
    for name in names:
        print (name)
    print()
    gs = GlobalStore()
    for name in gs.listdir('products'):
        print (name)



