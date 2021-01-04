import os, sys, datetime, requests, pickle, json
python = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(python)

from domino.server import Server, GUID
from domino.cli  import print_comment, Console, print_header, print_warning

if __name__ == "__main__":
    c = Console(__file__)
    server = c.input('server')
    params= {}
    params['account_id'] = c.input('account_id')
    params['type'] =  c.input('type')
    params['product_id']= c.input('product_id')
    params['id'] = c.input('id')
    r = requests.get(f'https://{server}/domino/active/python/check_license', params)
    print(r.url)
    print_header(r.status_code)
    print_warning(r.text)



