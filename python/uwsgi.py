import sys
sys.path.append('/DOMINO/products/domino/CURRENT/python')
sys.path.append('/DOMINO/uwsgi')
from importlib.machinery import SourceFileLoader

from flask import Flask, make_response, request
from time import time
import importlib.util as il
import importlib
import os, sys, uuid
from domino import parser
from domino.log import log
import domino.database
import domino.webgui as webgui

application = Flask(__name__)
application.config['USE_X_SENDFILE'] = True
application.config['UPLOAD_FOLDER'] = '/DOMINO/upload'
application.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024
application.secret_key = 'random string'

class Context:
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

   def cursor(self):
        SK = self.args.get('sk')
        sk = webgui.SessionKey(SK)
        return domino.database.connect(sk.account).cursor()

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

   def load_module(self, module):
      return SourceFileLoader(module, self.root_folder_product + '/python/' + module + '.py').load_module()

#application.errorhandler(404)
@application.route('/', methods=['GET','POST'], defaults={'path': ''})
@application.route('/<path:path>', methods=['GET','POST'])
def dynamic_module(path):

    path_path = '/DOMINO' +  request.path
    if  (os.path.exists(path_path)) :
        module_name = path_path.split('/')[-1].split('.')[0]
        log.debug('%s %s',path_path, module_name)

        spec = il.spec_from_file_location(module_name, path_path)
        module = il.module_from_spec(spec)
        spec.loader.exec_module(module)
        ctx = {}
        ctx['args'] = request.args
        currentFile = request.path
        splitList = currentFile.split('/')
        try:
            index = splitList.index('products') 
            productName = splitList[index+1]
            index = splitList.index('web') + 1
            ctx['path'] = productName + '/' + '/'.join(splitList[index:-1])
        except:
            ctx['path'].request.path
        
        domino_workplace_id = request.cookies.get('domino_workplace_id')
        r = module.response(Context(request))
        resp = make_response(r)
        if not domino_workplace_id:
            resp.set_cookie('domino_workplace_id', str(uuid.uuid4()), max_age=86400000, expires=time() + 86400000)
        
        return resp
    else:
        return 'PAGE NOT FOUND!', 404

   


if __name__ == '__main__':
    application.run()
