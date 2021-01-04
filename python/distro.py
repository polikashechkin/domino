import os, json
from zipfile import ZipFile

from domino.server import Server
from domino.core import log, Version
from domino.distro import Distro

def get_versions(request):
    product = request.get('product', 'product_id')
    if product is None:
        return 'Unknown product', '400 Unknown product'
    if not os.path.isdir(f'/DOMINO/public/products/{product}'):
        return f'Продукт не найден "{product}"', '400 Unknown product'
    versions = Distro.get_versions(product)
    return json.dumps([v.id for v in versions])

def get_version_info(request):
    product = request.get('product', 'product_id')
    version = Version.parse(request.get('version'))
    info = Server.get_version_info(product, version)
    return json.dumps(info.js)

def get(request):
    try:
        #log.debug(request.url)
        args = request.args
        product = request.get('product', 'product_id')
        if product is None:
            return 'Unknown product', '400 Unknown product'
        if not os.path.isdir(f'/DOMINO/public/products/{product}'):
            return f'Продукт не найден "{product}"', '400 Unknown product'

        version_id = args.get('version')
        if version_id is None:
            version = Distro.get_latest_version(product)
        else:
            version = Version.parse(version_id)

        if version is None:
            return 'Latest version not found', '400 Latest version not found'
        
        distro = Distro(product, version)

        file_name = request.get('file_name')
        if file_name is None:
            file_name = distro.file_name
        
        file = os.path.join(distro.folder, file_name)
        return request.download(file, file_name) 

    except BaseException as ex:
        log.exception(request.url)
        return str(ex), '500 {0}'.format(ex)

def get_apk(request):
    try:
        args = request.args
        product = request.get('product', 'product_id')
        if product is None:
            return 'Unknown product', '400 Unknown product'

        version_id = args.get('version')
        if version_id is None:
            version = Distro.get_latest_version(product)
        else:
            version = Version.parse(version_id)

        if version is None:
            return f'Не найдено apk файла для подходяещей версии для ', '404 Latest version not found'
        
        distro = Distro(product, version)
        return request.download(distro.apk) 

    except BaseException as ex:
        log.exception(request.url)
        return str(ex), '500 {0}'.format(ex)

def get_msi(request):
    try:
        args = request.args
        product = request.get('product', 'product_id')
        if product is None:
            return 'Unknown product', '400 Unknown product'

        version_id = args.get('version')
        if version_id is None:
            version = Distro.get_latest_version(product)
        else:
            version = Version.parse(version_id)

        if version is None:
            return f'Не найдено apk файла для подходяещей версии для ', '404 Latest version not found'
        
        distro = Distro(product, version)
        return request.download(distro.msi) 

    except BaseException as ex:
        log.exception(request.url)
        return str(ex), '500 {0}'.format(ex)

def upload(request):
    try:
        args = request.form # ! POST request data in dict form
        product = args.get('product')
        version = Version.parse(args.get('version'))
        if version is None:
            return 'Unknown version', '400 Unknown version'

        file = request.files['file']
        if file is None:
            return 'Unknown distro', '400 Unknown distro'

        distro = Distro(product, version)
        os.makedirs(distro.folder, exist_ok=True)

        file.save(distro.file)

        with ZipFile(distro.file, "r") as zip:
            with zip.open('info.json') as infile:
                with open(os.path.join(distro.folder,"info.json"), "wb") as outfile:
                    outfile.write(infile.read())
            #№apk_file_name = f'{product}.apk'
            #try:
            #    with zip.open(apk_file_name) as infile:
            #        with open(os.path.join(distro.folder,apk_file_name), "wb") as outfile:
            #            outfile.write(infile.read())
            #except BaseException as ex:
            #    log.exception(request.url)

        return 'File uploaded {0}'.format(distro.file)

    except BaseException as ex:
        log.exception(request.url)
        return str(ex), '500 {0}'.format(ex)
   
