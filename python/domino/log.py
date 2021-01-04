import os
import logging

DOMINO_LOG = '/DOMINO/log'

os.makedirs(DOMINO_LOG, exist_ok=True)
log = logging.getLogger('domino')
hdlr = logging.FileHandler(os.path.join(DOMINO_LOG, 'domino.log'))
formatter = logging.Formatter('%(asctime)s %(levelname)s %(module)s.%(funcName)s %(message)s')
#formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
log.addHandler(hdlr) 
#log.setLevel(logging.INFO)
log.setLevel(logging.DEBUG)
