import os, sys, datetime, requests, pickle, json
python = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(python)

from domino.server import Server, GUID
from domino.cli  import print_comment, Console, print_header, print_warning

if __name__ == "__main__":
    c = Console(__file__)
    params= {}
    params['account_id'] = c.input('account_id')
    params['product_id']= c.input('product_id')
    r = requests.get('https://dev.domino.ru/domino/active/python/get_product_info', params)
    print_comment(r.url)
    print_header(r.status_code)
    print_warning(r.text)



