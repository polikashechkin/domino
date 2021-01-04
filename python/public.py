import os, json
from domino.core import log

PUBLIC = '/DOMINO/public'

def hello(request):
    return 'hellp'

def listdir(request):
    names = []
    path = request.get('path')
    if path is None:
        path = ''
    if path is not None:
        if os.path.isabs(path):
            return 'Недопустим абсолютный путь', '400 unknown path'
        dir = os.path.join(PUBLIC, path)
        if os.path.isdir(dir):
            names = os.listdir(dir)
    return json.dumps(names)

def download(request):
    try:
        log.debug(request.url)
        path = request.get('path')
        if path is not None:
            return 'Не задан путь', '400 unknown path'
        if os.path.isabs(path):
            return 'Недопустим абсолютный путь', '400 unknown path'

        file = os.path.join(PUBLIC, path)
        if not os.path.isfile(file):
            return f'File "{file}" not found', '400 File not found'

        file_name = request.get('file_name')
        if file_name is None:
            file_name = os.path.basename(file)
        
        return request.download(file, file_name) 

    except BaseException as ex:
        log.exception(request.url)
        return str(ex), '500 {0}'.format(ex)

def upload(request):
    try:
        args = request.form
        path = args.get('path')
        if path is None:
            log.debug(json.dumps(args))
            return 'Параметр "path" не определен', '400 unknown path'
        if os.path.isabs(path):
            return 'Недопустим абсолютный путь', '400 unknown path'

        upload_file = os.path.join('/DOMINO/public', path) 
        os.makedirs(os.path.dirname(upload_file), exist_ok=True)

        file = request.files['file']
        if file is None:
            return 'Не задано файла', '400 No file contence'

        file.save(upload_file)
        return f'File "{path}" uploaded'

    except BaseException as ex:
        log.exception(request.url)
        return str(ex), '500 {0}'.format(ex)
   
   




