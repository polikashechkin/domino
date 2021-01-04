import os, json
from domino.core import log, Version
from domino.account import find_account

def get_info(request):
    try:
        account_id = request.get('account_id')
        account = find_account(account_id)
        if account is None:
            return 'Не найдена учетная запись {account_id}', '400 unknown account_id'
        return json.dumps(account.info.js)
    except BaseException as ex:
        log.exception(request.url)
        return f'{ex}' , f'500 {ex}'

