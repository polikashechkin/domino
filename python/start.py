#!/usr/bin/env python3.6
import os, sys
from domino.log import log

log.info('#dominostart')
os.system('uwsgi --ini /DOMINO/uwsgi/uwsgi.emperor.ini')


