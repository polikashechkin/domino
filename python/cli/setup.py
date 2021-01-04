#!/usr/bin/env python
import os, sys, json
import shutil

version_folder = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
#product_folder = os.path.dirname(version_folder)

try:
    info_file = os.path.join(version_folder, "info.json")
    with open(info_file, "r") as f:
        info = json.load(f)
    version = info['version']
    product = info['product']
except:
    print('Version info not found in "{0}"'.format(version_folder))
    sys.exit()

print('"{0} {1}", "{2}"'.format(product, version, version_folder))

#domino_usr = os.path.join(version_folder, 'python', 'domino.usr.py')
#cmd = 'python3.6 {0} activate domino {1}'.format(domino_usr, version)
#os.system(cmd)

os.system('/bin/cp -f -r {src} /etc/nginx'.format(src = os.path.join(version_folder, 'nginx.template' )+'/*'))
requirements_txt = os.path.join(version_folder, 'python', 'requirements.txt')
os.system('pip3.6 -q install -r {0}'.format(requirements_txt))
#os.system('source /DOMINO/uwsgi/bin/activate; pip -q install -r {0}; deactivate'.format(requirements_txt))
os.system('/bin/cp -f -r {src} /DOMINO/uwsgi'.format(src = os.path.join(version_folder, 'uwsgi.template' )+'/*'))
#os.system('service nginx reload')
