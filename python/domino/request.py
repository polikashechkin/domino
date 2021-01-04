import sys
from domino.core import log

#log.debug('domino.request init')

from flask import Flask, make_response, request
from time import time
import os, sys, uuid
import domino.parser as parser
#log.debug('domino.request init import parser')
#import domino.database
#import domino.webgui as webgui
#log.debug('domino.request init import webgui')

class DominoRequest:
   def __init__(self, req):
      self.request = req
      self.args = req.args
      self.form = req.form
      self.values = req.values   
      self.path = req.path
      self.base_url = req.base_url
      self.url_root = req.url_root
      self.script_root = req.script_root
      self.method = req.method
      self.data = req.data
      self.headers = req.headers
      self.files = req.files
      self.url = req.url
      
      self.folder = '/'.join(req.path.split('/')[:-1])
      self.root_folder = '/DOMINO' + self.folder
      split_url = req.url.split('?')
      if len(split_url) > 1 and req.method == 'GET':
         self.qs = split_url[1]
         self.args_obj = parser.parse(req.url.split('?')[1])
      else :
         self.args_obj = {}
      self.folder_product = '/'.join(self.folder.split('/')[0:4])
      self.root_folder_product = '/DOMINO' +  self.folder_product
      self.arg = self.args_obj
      
   def count(self, widget_name):
      id = self.args.get(widget_name + '[length]', 0)
      return id

   #def cursor(self):
   #     SK = self.args.get('sk')
   #     sk = webgui.SessionKey(SK)
   #     return domino.database.connect(sk.account).cursor()

   def get(self, name, alias = None):
        value = self.args.get(name)
        if value is not None:
            return value 
        else:
            return self.args.get(alias) if alias is not None else None

   def download(self, file, file_name = None):
        if not os.path.isfile(file):
            return f'File "{file}" not found','404 File "{file}" not found'
        if file_name is None:
            file_name = os.path.basename(file)
        with open(file, 'rb') as f:
            response  = make_response(f.read())
        response.headers['Content-Type'] = 'application/octet-stream'
        response.headers['Content-Description'] = 'File Transfer'
        response.headers['Content-Disposition'] = 'attachment; filename={0}'.format(file_name)
        response.headers['Content-Length'] = os.path.getsize(file)
        return response

   def recid(self, widget_name, index=None):
      if index :
         index = -1 * index
         widget_name = 'prev:' * index + widget_name 
      id = self.args.get(widget_name + '[record][recid]')
      return id

   def record(self, widget_name, index=None):
      if index :
         index = -1 * index
         widget_name = 'prev:' * index + widget_name 
      widget = self.args_obj.get(widget_name)
      if widget :
         return widget.get('record')
      return None

   def get_param(self, param_name, index=None):
      if index :
         index = -1 * index
         param_name = 'prev:' * index + param_name 
      return self.args.get(param_name)

   def field(self, widget_name, field_id, index=None):
      if index :
         index = -1 * index
         widget_name = 'prev:' * index + widget_name 
      widget = self.args_obj.get(widget_name)
      if widget :
         record = widget.get('record')
         if record :
            field = record.get(field_id) 
            if type(field) is str :
               return field
            elif field is not None:
               return field.get('value')
            else:
               return None
         else:
            return None
      else:
         return None

#log.debug('domino.request init ok')
