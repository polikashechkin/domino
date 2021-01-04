import sys
import json
import os
import inspect
import requests
import datetime
import re
import flask
import uuid
import domino.parser as parser
from domino.log import log
import traceback
import redis

class SessionKey: 
   def __init__(self, sk):
      if sk is None:
         return None
      self.sk = sk 


      r = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)
      sk_data = r.hgetall(sk)
#      print(sk_data)
#      return sk_data


#      requests.packages.urllib3.disable_warnings()
#      r = requests.get('http://127.0.0.1/domino/nginx/get_account_by_sk.lua?sk=' + sk, verify=False)
#      self.info = r.json()
      self.account = sk_data.get('account')
      

def json_converter(o):
   if isinstance(o, datetime.datetime):
      return o.date().__str__()

def action_data(rows, widget_name=None):
   result = {}
   result['action'] = 'data';
   result['dataAction'] = 'refresh_data';
   if (widget_name):
       result['widgetName'] = widget_name;
   result['eof'] = True;
   result['tof'] = True;
   result['records'] = rows;
   return json.dumps(result, default = json_converter)


def action_refresh_line(rows, recid=None, widget_name=None, start_edit=False, as_object=False):
   result = {}
   result['action'] = 'data';
   result['dataAction'] = 'refresh_line';
   if start_edit:
      result['startEdit'] = True
   if recid :
       result['item'] = recid;
   if (widget_name):
       result['widgetName'] = widget_name;
   result['eof'] = True;
   result['tof'] = True;
   result['records'] = rows;
   if as_object:
      return result
   else :
      return json.dumps(result, default = json_converter)

def action_append_blank_line(rows, widget_name=None):
   result = {}
   result['action'] = 'data';
   result['dataAction'] = 'append_blank_line';
   if (widget_name):
       result['widgetName'] = widget_name;
   result['records'] = rows;
   return json.dumps(result, default = json_converter)


def action_append_line(rows, widget_name=None):
   result = {}
   result['action'] = 'data';
   result['dataAction'] = 'append_blank_line';
   if (widget_name):
       result['widgetName'] = widget_name;
   result['records'] = rows;
   return json.dumps(result, default = json_converter)



def action_remove_line(row=None, widget_name=None):
   result = {}
   result['action'] = 'data';
   result['dataAction'] = 'remove_line';
   if (widget_name):
       result['widgetName'] = widget_name;
   return json.dumps(result, default = json_converter)



class Widget:
   def __init__(self, name=None):
       self.obj = {}
       if (name is not None) :
          self.obj['_name'] = name
       self.params = {}
       self.desc = {}
       self.class_params = {}
       self.actions = []
       self.events = {}
       self.currentFile = flask.request.path
       splitList = self.currentFile.split('/')
       self.full_path = '/DOMINO' + '/'.join(flask.request.full_path.split('/')[0:-1])

       try :
           index = splitList.index('products') 
           productName = splitList[index+1]
           index = splitList.index('web') + 1
           self.path_to_script = productName + '/' + '/'.join(splitList[index:-1])
           self.path = self.path_to_script
       except:
           self.path_to_script = flask.request.path
           pass


   def set_desc(self, paramName, paramVal):
      self._set_key('desc.' + paramName, paramVal)
      self.desc.update(self.obj['desc'])

   def cash_disable(self, disable=True):
      self._set_key('classAttr.cashDisable', disable)

   def set_event(self, event, action):
       self._set_key('events.' + event, action);
       self.events.update(self.obj['events'])

   def set_class_param(self, paramName, paramVal):
       self._set_key('classAttr.' + paramName, paramVal)

   def set_class_attr(self, paramName, paramVal):
       self._set_key('classAttr.' + paramName, paramVal)

   def get(self, url) :
       self._set_key('get', url);

   def _set_key(self, key, val) :
       lkeys = key.split('.')
       tmp = {lkeys[-1] : val}
       t = self.obj 
       for k in lkeys[:-1] :
           if (t.get(k) is None):
               t[k] = {}
           t = t[k]    
       t.update(tmp)


   def _beforeReturn(self):
       if (self.desc) :
           if (self.obj.get('desc') is None) :
               self.obj['desc'] = {}
           self.obj['desc'].update(self.desc)

       if (self.actions) :
           if (self.obj.get('actions') is None) :
               self.obj['actions'] = self.actions

   @staticmethod
   def none(widget_name=None):
      result = {}
      result['action'] = 'none';
      if (widget_name):
          result['widgetName'] = widget_name;
      return json.dumps(result)



   def dict(self):
       self._beforeReturn()
       return self.obj

   def json(self):
       self._beforeReturn()
       return json.dumps(self.obj)

class WidgetCode(Widget):
    def __init__(self, name, file):
        super().__init__(name)
        self._set_key('class', 'code')
        # загружаем файл
        currentFile = flask.request.path
        path = '/DOMINO/' + '/'.join(currentFile.split('/')[1:5]) + file
        
        content = ''
        f = open(path)
        first_line = True
        for line in f.readlines():
           if first_line:
              content = content + line[1:]
              first_line = False
           else:
              content = content + line
        self._set_key('desc.code', content) 



class WidgetHtml(Widget):
   def __init__(self, name):
      super().__init__(name)
      self._set_key('class', 'html')
      self._set_key('classAttr.tpl', name + '.html')
      self.currentFile = str(inspect.stack()[1].filename);
      splitList = self.currentFile.split('/');
      try :
          index = splitList.index('products') 
          productName = splitList[index+2]
          index = splitList.index('web') + 1
#          path = productName + '/' + '/'.join(splitList[index:-1])
          path = '/'.join(splitList[index:-1])
          self.path_to_script = path
      except:
          pass

      print('')
      self._set_key('classAttr.tplPath', path)

   
   def set_action(self, selector, action, action_type='exec'):
      if action_type == 'signal' :
         act =  'trigger ' + action
      elif action_type == 'exec' :
         if action[0] == '/': # absolute path
            act = 'exec ' + action
         else :
            act = 'exec ' + self.path_to_script + '/' + action
      else :
         return

      i = 0
      for a in self.actions:
         if self.actions[i]['selector'] == selector:
            self.actions[i]['action'] = self.actions[i]['action'] + ';' + act
            break
         i += 1
      else :
         self.actions.append({'selector':selector, 'action' :  act})

   def append(self, widget, position='#body') :
       w = widget.dict()
       widgetName = w['_name']
       self._set_key('widgets.' + widgetName , w) 
       self._set_key('widgets.' + widgetName + '.position', position)

   @staticmethod
   def data_refresh(data={}, widget_name=None, enforce=False) :
      resp = {"action" : "desc", "desc" : data}
      if (widget_name):
         resp['widgetName'] = widget_name

      resp['enforceRefresh'] = enforce
      return json.dumps(resp)

   @staticmethod
   def desc_refresh(desc={}, widget_name=None, enforce=False) :
      resp = {"action" : "desc", "desc" : data}
      if (widget_name):
         resp['widgetName'] = widget_name

      resp['enforceRefresh'] = enforce
      return json.dumps(resp)

   @staticmethod
   def desc(desc={}) :
      return data_refresh(data, enforce = True)


   @staticmethod
   def signal_refresh(widget_name=None, enforce=False) :
      result = {}
      result['action'] = 'trigger refreshDesc';
      if (widget_name):
          result['action'] = result['action'] + ' ' + widget_name;
      return json.dumps(result)




class WidgetMsgBox(Widget) :
   def __init__(self, name, context_menu_button=False) :
      self.name = name
      super().__init__(name)
      self._set_key('class', 'mbox')
      self._set_key('desc.header', 'paramVal');



class WidgetGrid(Widget) :
   def __init__(self, name, context_menu_button=False) :
      self.name = name
      super().__init__(name)
      self.fields = {}
      self.remove_show_save = False
      self.ctm = []
      self.std_tb_array = []
      self.std_tb_array.append('search')
      self.std_tb_array.append('showRefresh')
      
      self.key = None


      if (context_menu_button) :
          self._set_key('classAttr.contextMenuButton', context_menu_button)

      self._set_key('classAttr.filterControl', True)        
      self.std_tb_array.append('showFilter')

      self.editable_table = False
      self.filter = False
      self._set_key('class', 'grid')
      # Установка аттрибутов класс по умолчанию

      #self._set_key('classAttr.bootstrapTableToolbar', ["showRefresh", "search" ])
      self._set_key('classAttr.pagination', False)
      self._set_key('classAttr.preventSwap', True)


      #self._set_key('get', self.path_to_script + '/' + name +'.get.py')
   
#      self._set_key('urlData', self.path + '/' + name +'.get.py');
#      self._set_key('urlDesc', self.path + '/' + name +'.desc.py');
   

      self.currentFile = str(inspect.stack()[1].filename);
      splitList = self.currentFile.split('/');
      try :
         index = splitList.index('products') 
         productName = splitList[index+1]
         index = splitList.index('web') + 1
         #self.path_to_script = productName + '/' + '/'.join(splitList[index:-1])
         self.path_to_script = '/'.join(splitList[index:-1])
      except:
         self.path_to_script = ''




      if os.path.exists(self.full_path + '/' + self.name + '.inline_edit.py') :
         self._set_key('urlInlineEdit', self.path_to_script + '/' + self.name + '.inline_edit.py')


   def enumerate_row(self, show=True):
       self._set_key('classAttr.enumRow', show)        

   def context_menu_button(self, show=True):
       self._set_key('classAttr.contextMenuButton', show)

   def show_filter(self, show=False):
      self._set_key('classAttr.filterControl', show)        
      if not show :
         self.std_tb_array.remove('showFilter')

   def show_edit(self, show=False, uri=None):
      if show :
         self.std_tb_array.append('showEdit')
         if uri :
            if (uri[0] == '/') : # absolute path
                self._set_key('urlEdit', uri)
            else :
                self._set_key('urlEdit', self.path_to_script + '/' + uri)



   def show_refresh(self, show=False):
      if show :
         self.std_tb_array.append('showRefresh')
      else :
         self.std_tb_array.remove('showRefresh')

   def show_save(self, show=False, uri=None):
      if show :
         self.std_tb_array.append('showSave')
         if uri :
            if (uri[0] == '/') : # absolute path
                self._set_key('urlSave', uri)
            else :
                self._set_key('urlSave', self.path_to_script + '/' + uri)
         else :
            self._set_key('urlSave', self.path_to_script + '/save.py')
      else :
         self.remove_show_save = True
         if 'showSave' in self.std_tb_array:
            self.std_tb_array.remove('showSave')

   def show_search(self, show=False):
      if show :
         self.std_tb_array.append('search')
      else :
         self.std_tb_array.remove('search')



   def show_complete_select(self, show=False, action=None, action_type='exec'):
      if show :
         self.std_tb_array.append('showCompleteSelect')
         if not action:
            action_1 = action_type + ' ' + self.path_to_script + '/' + self.name + '.complete_select.py'
         else:
            if (action[0] == '/') : # absolute path
               action_1 = action
            else :
               action_1 = action_type + ' ' + self.path_to_script + '/' + action
         self._set_key('events.completeSelect', action_1)


   def show_append(self, show=False, uri=None):
      if show :
         self.std_tb_array.append('showAppend')
         if uri :
            if (uri[0] == '/') : # absolute path
                self._set_key('urlAppend', uri)
            else :
                self._set_key('urlAppend', self.path_to_script + '/' + uri)
         else :
            self._set_key('urlAppend', self.path_to_script + '/' + self.name + '.append.py')

   def show_remove(self, show=False, method_uri=None) :
      if show : 
         self.std_tb_array.append('showRemove')
         if method_uri :
            self._set_key('urlRemove', uri)
         else :
            self._set_key('urlRemove', self.path_to_script + '/' + self.name + '.remove.py')

   def set_url_get(self, url):
      if uri[0] == '/':
         self._set_key('urlData', uri);
      else :
         self._set_key('urlData', self.path_to_script + '/' + uri)

   def on_change_row(self, action) :
      self._set_key('events.changeRow', action)

   def on_complete_select(self, action) :
      self._set_key('events.completeSelect', action)

   def on_load_data(self, action) :
      self._set_key('events.loadData', action)

   def inline_edit_handler(self, uri=None):
      if not uri:
         self._set_key('urlInlineEdit', self.path_to_script + '/' + self.name + '.inline_edit.py')
      else :
         if (uri[0] == '/') : # absolute path
            self._set_key('urlInlineEdit', uri)
         else :
            self._set_key('urlInlineEdit', self.path_to_script + '/' + uri)

   def add_record(self, record) :
      if (self.obj.get('get') is None) :      
         self.obj['get'] = {};
         self.obj['get']['records'] = []
      self.obj['get']['records'].append(record)


   def add_ctm_item(self, id, type='item', text = '', action = None, action_type = 'exec') :
       if action :
          action_1 = action_type + ' ' + self.path_to_script + '/' + action
       else :
          action_1 = ''
       self.ctm.append({"id" : id, "type" : type, "text" : text, "action" : action_1})

   def add_toolbar_item(self, button,  caption=None, action=None, action_type='exec', icon=None, btn_class='btn-default'):
      if (self.obj.get('desc') is None) :      
          self.obj['desc'] = {}
      if (self.obj['desc'].get('toolbar') is None) :            
          self.obj['desc']['toolbar'] = []

      if (action is None) :
          self.obj['desc']['toolbar'].append({"btn_class":btn_class, "icon":icon, "text":caption, "button":"custom", "action" : "exec " + self.path_to_script + '/' + self.obj['_name'] + '.' + button + '.py'})
      else :
          if action[0] == '/' : #absolute path
             self.obj['desc']['toolbar'].append({"btn_class":btn_class,"icon":icon,"text":caption, "button":"custom", "action" : action_type + ' ' + action})
          else:
             self.obj['desc']['toolbar'].append({"btn_class":btn_class,"icon":icon, "text":caption, "button":"custom", "action" : action_type + ' ' + self.path_to_script + '/' + action})

   def exec_dblclick(self, path=None) :
      if (path is None):
         event_handler = self.path_to_script + '/' + self.name + '.dblclick.py'
      else:
         if (path[0] == '/') : # absolutr path
            event_handler = path
         else :
            event_handler = self.path_to_script + '/' + path
      self._set_key('events.dblClick', 'exec ' + event_handler)


   def trigger_dblclick(self, action) :
      self._set_key('events.dblClick', 'trigger ' + action);

   def get_data_on_demand(self, mode=True) :
      self._set_key('classAttr.getDataOnDemand', mode);


   def add_field(self, field, caption, field_type='string', editable=False, options=None, action=None, key=False, filter='input' , action_type='exec', not_send=False) : 
      if (self.obj.get('desc') is None) :      
          self.obj['desc'] = {}
      if (self.obj['desc'].get('fields') is None) :
          self.obj['desc']['fields'] = []
      if caption == '' :
         caption = '&nbsp;'


      if (field_type == 'select' and action is None) :
         action = 'exec ' + self.path_to_script + '/' + field + '/' + field + '.win.py'
      else :
         if action :
            if action[0] == '/' : # absolute path
               action = action_type + ' ' + action
            else :
               action = action_type + ' ' + self.path_to_script + '/' + action
         else :
            action = ''


      self.obj['desc']['fields'].append({"notSend" : not_send, "key":key, "field":field, "caption":caption, "type" : field_type, "editable" : editable, "options":options, "action":action, "filterControl" : filter})

      if key :
         self.key = field;

      if editable : 
         self.editable_table = True

   @staticmethod
   def data_remove_line(records=None, widget_name=None):
      result = {}
      result['action'] = 'data';
      result['dataAction'] = 'remove_line';
      if records:
         result['records'] = []
         if type(records) is str: # одна запись (recid)
            result['records'].append(records)
         if type(records) is list: # массив записей ['recid1', 'recid2', ...]
            result['records'] = records
      if (widget_name):
          result['widgetName'] = widget_name;
      return json.dumps(result)

   @staticmethod
   def signal_remove_line(widget_name=None):
      result = {}
      result['action'] = 'trigger remove_line';
      if (widget_name):
         result['action'] = 'trigger remove_line ' + widget_name;
      return json.dumps(result)

   @staticmethod
   def data_append_line(data, widget_name=None, start_edit=False, select_record_id=None):
      result = {}
      result['action'] = 'data';
      result['dataAction'] = 'append_line';
      if (select_record_id):
         result['item'] = select_record_id;
      if (widget_name):
          result['widgetName'] = widget_name;
      if (start_edit):
          result['startEdit'] = True;
      if type(data) is list:
         result['records'] = data;
      elif type(data) is dict:
         result['records'] = [];
         result['records'].append(data)
      else:
         result['records'] = [];

      return json.dumps(result, default = json_converter)

   @staticmethod
   def data_refresh_line(data, widget_name=None, start_edit=False, select_record_id=None, sent_fields=False, stop_timer=None):
      result = {}
      result['action'] = 'data';
      result['dataAction'] = 'refresh_line';
      if sent_fields:
         result['update_only_sent_fields'] = True
      if start_edit:
         result['startEdit'] = True
      if (widget_name):
          result['widgetName'] = widget_name;
      result['eof'] = True;
      result['tof'] = True;
      if stop_timer:
         result['stopTimer'] = True

      if type(data) is str: # Воспринимаем как recid
         result['records'] = []
         result['records'].append({'recid' : data})

      if type(data) is list: # массив записей
         result['records'] = data;

      if type(data) is dict: # одна запись
         result['records'] = []
         result['records'].append(data)

      return json.dumps(result, default = json_converter)

   @staticmethod
   def data_refresh(data, widget_name=None, select_record_id=None):
      result = {}
      result['action'] = 'data';
      result['dataAction'] = 'refreshData';
      if (widget_name):
          result['widgetName'] = widget_name;
      result['eof'] = True;
      result['tof'] = True;

      if type(data) is list: # массив записей
         result['records'] = data;

      if type(data) is dict: # одна запись
         result['records'] = []
         result['records'].append(data)

      return json.dumps(result)


   @staticmethod
   def signal_refresh(widget_name):
      result = {}
      result['action'] = 'trigger refreshData';
      if (widget_name):
          result['action'] = result['action'] + ' ' + widget_name;
      return json.dumps(result)


   @staticmethod
   def signal_refresh_line(widget_name, recid=None):
      result = {}
      result['action'] = 'trigger refresh-line';
      if (widget_name):
          result['action'] = result['action'] + ' ' + widget_name;

      if (recid):
          result['action'] = result['action'] +  ' ' + recid;

      return json.dumps(result)

   @staticmethod
   def signal_refresh_line_by_timer(interval=10, widget_name=None):
      result = {}
      result['action'] = 'trigger refreshLineByTimer'
      if (widget_name):
          result['action'] = result['action'] + ' ' + widget_name + ' ' + str(interval)
      return json.dumps(result)




   def _beforeReturn(self):
      super()._beforeReturn()

      if (self.fields) :
         if (self.obj.get('desc') is None) :
            self.obj['desc'] = {}
         self.obj['desc']['fields'] = self.fields


      if (self.std_tb_array) :
         self._set_key('classAttr.bootstrapTableToolbar', self.std_tb_array)

      # таблица с редактируемыми полями - задаем метод save по умолчанию
      if (self.editable_table) :
         #self._set_key('urlInlineEdit', self.path_to_script + '/' + self.name + '.inline_edit.py')
         self._set_key('save', self.path_to_script + '/' + self.name + '.save.py')

      if self.key:
         self._set_key('desc.uniqueId', self.key)

      if self.ctm :
         self._set_key('ctm', self.ctm)

      if self.obj.get('desc'):
         toolbar = self.obj['desc'].get('toolbar')
         if toolbar and len(toolbar) == 1:
            self.obj['desc']['toolbar1'] = {}
            self.obj['desc']['toolbar1']['text'] = toolbar[0]['text']
            self.obj['desc']['toolbar1']['button'] = toolbar[0]['button']
            self.obj['desc']['toolbar1']['action'] = toolbar[0]['action']
            self.obj['desc']['toolbar1']['icon'] = toolbar[0]['icon']
            self.obj['desc']['toolbar1']['btn_class'] = toolbar[0]['btn_class']


            del self.obj['desc']['toolbar']
         

class WidgetForm(Widget) :
   def __init__(self, name) :
      super().__init__(name)
      self.toolbar_user_define = False
      self.name = name
      self._set_key('class', 'form')
      self._set_key('widgets.' + self.name + '.position', '#body')
      self._set_key('widgets.'+ self.name + '.class', 'form-fields')
      self._set_key('widgets.'+ self.name + '.desc.fields', [])

      #self._set_key('widgets.form_fields.position', '#body')
      #self._set_key('widgets.form_fields.class', 'form-fields')
      #self._set_key('widgets.form_fields.desc.fields', [])

      self._set_key('widgets.toolbar.position', '#footer')
      self._set_key('widgets.toolbar.class', 'toolbar')
      self._set_key('widgets.toolbar.classAttr.tpl', 'toolbar.html')
      self._set_key('widgets.toolbar.desc.items', [])

      self.currentFile = str(inspect.stack()[1].filename);
      splitList = self.currentFile.split('/');
      try :
        index = splitList.index('products') 
        productName = splitList[index+1]
        index = splitList.index('web') + 1
        self.path_to_script = productName + '/' + '/'.join(splitList[index:-1])
      except:
        self.path_to_script = ''


   def set_mode(self, mode):
      self._set_key('widgets.' + self.name + '.mode', mode)

   def add_field(self, field, caption, field_type, action = None, readonly=False, value=None, values=None) : 
      if(field_type == 'select' and action == None) :
          action = 'exec ' + self.path_to_script + '/' + field + '/' + field + '.win.py'
      if (self.obj.get('desc') is None) :      
          self.obj['desc'] = {}
      if (self.obj['desc'].get('fields') is None) :
          if readonly :
             readonly_field = 'readonly' 
          else :
             readonly_field = '' 

      field_desc = {"field":field, "caption":caption, "type" : field_type, "action": action, "readonly" : readonly_field, "value" : value}
      if values :
         field_desc['values'] = values

      #self.obj['widgets']['form_fields']['desc']['fields'].append(field_desc)
      self.obj['widgets'][self.name]['desc']['fields'].append(field_desc)
      #return len(self.obj['widgets']['form_fields']['desc']['fields']) - 1
      return len(self.obj['widgets'][self.name]['desc']['fields']) - 1

   


   def add_toolbar_item(self, id, caption, action=None, action_type='exec'):
      self.toolbar_user_define = True
      if (action is None) : 
         action = 'exec ' + self.path_to_script + '/' + self.name + '.' + id + '.py'
      else :
         if action_type == 'exec':
            if action[0] == '/':
               action = 'exec ' + action
            else:
               action = 'exec ' + self.path_to_script + '/' + action
         if action_type == 'signal':
            action = 'trigger ' + action

      self.obj['widgets']['toolbar']['desc']['items'].append({"type":"button", "caption" : caption, "action" : action})

   def _beforeReturn(self):
      super()._beforeReturn()
      # нет кнопок определнных пользователем, добавдяемя 2 Отмена, Сохранить
      if not self.toolbar_user_define:
         self.add_toolbar_item('save',  'Сохранить')
         self.add_toolbar_item('cancel',  'Отмена', action = 'close', action_type='signal')

   @staticmethod
   def data_refresh_line(data, widget_name=None, sent_fields=False ):
      result = {}
      result['action'] = 'data';
      if (widget_name):
          result['widgetName'] = widget_name;
      if type(data) is dict: # одна запись
         if sent_fields :
            data['update_only_sent_fields'] = True
         result['records'] = []
         result['records'].append(data)

      return json.dumps(result)


class WidgetTabsForm(Widget) :
   def __init__(self, name) :
      super().__init__(name)
      self.name = name
      self.fields = {}
      self.tabs = []

      self.currentFile = str(inspect.stack()[1].filename);
      splitList = self.currentFile.split('/');
      try :
        index = splitList.index('products') 
        productName = splitList[index+1]
        index = splitList.index('web') + 1
        self.path_to_script = productName + '/' + '/'.join(splitList[index:-1])
      except:
         pass


   def add_tab(self, caption) : 
      self.tabs.append({"caption":caption})
      return len(self.tabs) - 1

   def add_toolbar_item(self, id, caption, action=None):
      
      if (action is None) : 
         action = 'exec ' + self.path_to_script + '/' + self.name + '.' + id + '.py'

      self.obj['widgets']['toolbar']['desc']['items'].append({"type":"button", "caption" : caption, "action" : action})

   def add_field(self, tab_index, field, caption, field_type, action = None, readonly=False) : 

      if(field_type == 'select' and action == None) :
          action = 'exec ' + self.path_to_script + '/' + field + '/' + field + '.win.py'

      if (self.fields.get(tab_index) is None) :
         self.fields[tab_index] = []
      self.fields[tab_index].append({"field":field, "caption":caption, "type" : field_type, "action": action, "tab_index" : tab_index})

   def _beforeReturn(self):
      super()._beforeReturn()
      if (not self.tabs or not self.fields) :
         return

      self._set_key('class', 'form')
      self._set_key('position', '#body')
      self._set_key('widgets.form_header.class', 'tabs')
      self._set_key('widgets.form_header.position', '#body')
      self._set_key('widgets.form_header.desc.tabs', [])
      
      # создаем закладки
      tab_index = 0
      for t in self.tabs :
         self.obj['widgets']['form_header']['desc']['tabs'].append({"caption": t['caption'], 'id' : tab_index + 1})   
         if (tab_index == 0) :
            self.obj['widgets']['form_header']['desc']['tabs'][0]['active'] = True
         tab_index = tab_index + 1

      # создаем виджеты form-fields на закладках       
      

      tab_index = 0
      for t in self.tabs :
         fields = self.fields[tab_index]
         key = 'widgets.form_header.widgets.form_fields_' + str(tab_index+1)
         self._set_key(key + '.class', 'form-fields')
         self._set_key(key + '.position', '#tab_' + str(tab_index+1))
         self._set_key(key + '.desc.tabIndex', str(tab_index+1))

         self.obj['widgets']['form_header']['widgets']['form_fields_'+ str(tab_index+1)]['desc']['fields'] = fields 

         tab_index = tab_index + 1

class WidgetToolbarSubmenu(Widget) :
    def __init__(self) :    
        self.obj = {}
        self.params = {}
        self.obj['items'] = []
        self.obj['params'] = {}

    def add_item(self, caption, action) :
        self.obj['items'].append({"caption":caption, "action":action, "type":"item"})

    def add_submenu(self, caption, submenu) :
        self.obj['items'].append({"caption":caption,  "type":"menu", "items" : submenu.dict()['items'] })

class WidgetToolbar(Widget) :
    def __init__(self, name) :    
        super().__init__(name)
        self._set_key('class', 'toolbar')
        self._set_key('position', '#toolbar')
        self._set_key('desc.items', [])
        self._set_key('classAttr.tpl', 'toolbar-nav.html')

    def add_item(self, caption, action) :
        self.obj['desc']['items'].append({"caption":caption, "action":action, "type":"button"})

    def add_submenu(self, caption, submenu) :
        self.obj['desc']['items'].append({"caption":caption,  "type":"menu", "items" : submenu.dict()['items'] })



class Window(Widget):
    def __init__(self, window_class, title, window_id=None, position='#body', tpl=None, tplPath=None):
        super().__init__('')
        self._set_key('action', 'open')
          
        if (title) :
            self.set_title(title)

        #определяем путь к текущему файлу и на основе его формируем id окна
        if window_id :
            self._set_key('window_id', window_id)
        else:
            self.currentFile = str(inspect.stack()[1].filename);
            splitList = self.currentFile.split('/');
            try :
                index = splitList.index('products') 
                productName = splitList[index+1]
                index = splitList.index('web') + 1
                #path = productName + '/' + '/'.join(splitList[index:-1])
                path =  '/'.join(splitList[index:-1])
                self._set_key('window_id', path)
            except:
                pass

        self._set_key('position', position)
        self._set_key('window.class', window_class)

        if tpl :
            self._set_key('window.classAttr.tpl', tpl)

        if tplPath :
            self._set_key('window.classAttr.tpl', tplPath)
     
    def set_title(self, title = '') :
        self._set_key('window.desc.title', '<h3>' + title + '</h3>')

    def vscroll(self, scroll=False, zone='#body'):
       if scroll:
          self._set_key('window.classAttr.scrollY',True);

    def hscroll(self, scroll=False, zone='#body'):
       if scroll:
          self._set_key('window.classAttr.scrollX',True);

    def set_class_param(self, paramName, paramVal):
        self._set_key('window.classAttr.' + paramName, paramVal);

    def set_param(self, paramName, paramVal):
        self._set_key('window.ctx.' + paramName, paramVal);

    def append(self, widget, position='#body') :
        w = widget.dict()
        widgetName = w['_name']
        self._set_key('window.widgets.' + widgetName , w) 
        self._set_key('window.widgets.' + widgetName + '.position', position)

    def hide_close_button(self):
        self.set_class_param('hideCloseButton', True)

    def pass_context(self, args=None):
       if not args:
          return
       
       for key in args:
          if args[key] and args[key] != '' :
             self.set_param('prev:'+ key, args[key])


    @staticmethod
    def signal_close():
       resp = {'action' : 'trigger close'}
       return json.dumps(resp)

    def _beforeReturn(self):
        super()._beforeReturn()
        if (self.params) :
            if (self.obj['window'].get('ctx') is None) :
                self.obj['window']['ctx'] = {}
            self.obj['window']['ctx'].update(self.params)

class WidgetTabs(Widget) :
   def __init__(self, name) :
      super().__init__(name)
      self.tabs = []
      self._set_key('class', 'tabs')
      self._set_key('desc', {})
    
   def add_tab(self, caption, action=None, action_type='exec', active=False, disable=False) : 
      tab_obj = {}
      tab_obj['caption'] = caption
      if action :       
         if action_type=='exec':
            if action[0] == '/':
               tab_obj['action'] = 'exec ' + action
            else :
               tab_obj['action'] = 'exec ' + self.path_to_script + '/' + action

         if action_type=='signal' :
            tab_obj['action'] = 'trigger ' + action
      else :
          tab_obj['action'] = ''

      if active:
         tab_obj['active'] = True
      if disable:
         tab_obj['disabled'] = 'disabled'
      else:
         tab_obj['disabled'] = ''

      self.tabs.append(tab_obj)
      return len(self.tabs) - 1

   def append(self, tab, widget) :
      w = widget.dict()
      widgetName = w['_name']
      self._set_key('widgets.' + widgetName , w) 
      self._set_key('widgets.' + widgetName + '.position', '#tab_' + str(tab+1))
      self._set_key('widgets.' + widgetName + '.tabIndex', str(tab+1))

   @staticmethod
   def signal_disable_tabs(tabs_id, widget_name):
      if type(tabs_id) is str: 
         tabs = []
         tabs.append(tabs_id)
      else :
         tabs = tabs_id

      resp = {}
      resp['action'] = 'desc'
      resp['widgetName'] = widget_name
      resp['desc'] = {}
      resp['desc']['tabs'] = []
      for id in tabs:
         resp['desc']['tabs'].append({'id':id, 'disabled':'disabled'})
      return json.dumps(resp)

   @staticmethod
   def signal_enable_tabs(tabs_id, widget_name):
      if type(tabs_id) is str: 
         tabs = []
         tabs.append(tabs_id)
      else :
         tabs = tabs_id

      resp = {}
      resp['action'] = 'desc'
      resp['widgetName'] = widget_name
      resp['desc'] = {}
      resp['desc']['tabs'] = []
      for id in tabs:
         resp['desc']['tabs'].append({'id':id, 'disabled':''})
      return json.dumps(resp)

   @staticmethod
   def signal_select(tab_id, widget_name) :
      resp = {}
      resp['action'] = 'trigger select ' + widget_name + ' ' + str(tab_id)
      return json.dumps(resp)


   def _beforeReturn(self):
      super()._beforeReturn()
      if (not self.tabs) :
         return      
      # создаем закладки
      if (self.obj['desc'].get('tabs') is None) :
         self.obj['desc']['tabs'] = []
      tab_index = 0
      has_active_flag = False
      for t in self.tabs :
         if t.get('active') and not has_active_flag :
            has_active_flag = True
            self.obj['desc']['tabs'].append({'action' : t['action'],'caption': t['caption'], "active" : True, 'id' : tab_index + 1, 'disabled':t['disabled']})   
         else:
            self.obj['desc']['tabs'].append({'action' : t['action'], 'caption': t['caption'], "id" : tab_index + 1, 'disabled':t['disabled']})   
         tab_index = tab_index + 1
      if not has_active_flag:
         self.obj['desc']['tabs'][0]['active'] = True 

class UpdateWidget(Widget) :
   def __init__(self, name) :
     self.desc = {}
     self.obj = { "action" : "desc", "widget" : name }

class UpdateWindow() :
   def __init__(self) :
     self.desc = {}
     self.obj = { "action" : "desc", "widget" : 'window' }

def menu_separator():
   return {'type':'break'}

def menu_item(text = None, action = None, items = None, params = None):
   if text is None: return {'type':'break'}
   item = {'type':'item', 'text':text}
   item['action'] = action
   item['params'] = params
   if items:
      item['type']='menu'
      item['actions']=items
   return item

class ExecCreator:
   def __init__(self, path):
      #products/{product_name}/{version}/web/{path}/method.py
      #self.dir = os.path.join("/DOMINO", os.path.dirname(path))
      self.dir = "/DOMINO" + os.path.dirname(path)
      p = path.split('/')
      self.product_name = p[p.index('products') + 1]
      self.web_path = os.path.join(self.product_name, '/'.join(p[p.index('web') + 1:-1]))

   def create(self, action, params = None):
      if action is None: 
         return None
      if action.find('/') < 0:
         files = [ action + '.py', action + '.php']
         files.append(os.path.join(action, action + '.win.py'))
         files.append(os.path.join(action, action + '.win.json'))
         for file in files:
            real_file = os.path.join(self.dir, file)
            if os.path.isfile(real_file):
               action= os.path.join(self.web_path, file)
               break
         else:
            return None
      if params is not None:
         args = []
         for name,value in params.items():
            args.append(name + '=' + value)
         action += '?' + '&'.join(args)
      return 'exec ' + action

 
def prepeare_menu_items(items, parent_id, e):
   index = 0
   for item in items:
      index += 1
      if parent_id:
         item['id'] = "{0}.{1}".format(parent_id, index)
      else:
         item['id'] = "{0}".format(index)
      type = item['type']
      if type == 'item':
         action = item.get('action')
         params = item.get('params')
         if action:
            item['action.org'] = action
            item['action'] = e.create(action, params)
            #item['dir'] = e.dir
            #item['path'] = flask.request.path
      elif type == 'menu':
         subitems = item.get('actions')
         if subitems:
            prepeare_menu_items(subitems, item['id'], e)
      else:
         continue

def action_ctm (items):
   if items: 
      prepeare_menu_items(items, None, ExecCreator(flask.request.path))
   return json.dumps({'action':'ctm', 'data':items})


def action_close_selector(field_name, text='', value=None, widget_name=None) :
   field = {}
   
   if (value) :
      field[field_name] = {"text" : text, "val" : value}
   else :
      field[field_name] = "text"

   field['update_only_sent_fields'] = 1
   record = [field]

   resp = [{"action":"trigger close"},{"action" : "data", "records" : record}]
   if (widget_name):
      resp[1]["widgetName"] = widget_name
   return json.dumps(resp)


def action_update_form_fields(record=[], widget_name=None) :
   if (record is not None) :
      record[0]['update_only_sent_fields'] = 1
   resp = {"action" : "data", "records" : record}

   if (widget_name):
      resp['widgetName'] = widget_name
   return json.dumps(resp)

# Это унивесальные функции и трогать их не будем.
def close_and_send_data(record=[],  widget_name=None, update_only_sent_fields=False, data_action=None ) :
   action_close = {"action":"trigger close"}
   action_data = {"action" : "data", "records" : record}

   if (update_only_sent_fields) :
       action_data['update_only_sent_fields'] = True

   if (data_action) :
       action_data['dataAction'] = data_action


   resp = [action_close, action_data]
   if (widget_name):
      resp[1]["widgetName"] = widget_name
   return json.dumps(resp)

def send_data(records=[], widget_name=None) :
   resp = {"action" : "data", "records" : records}
   if (widget_name):
      resp['widgetName'] = widget_name
   return json.dumps(resp)

def send_desc(desc={}, widget_name=None, enforce=False) :
   resp = {"action" : "desc", "desc" : desc}
   if (widget_name):
      resp['widgetName'] = widget_name

   resp['enforceRefresh'] = enforce

   return json.dumps(resp)

def get_key_name() :
   return '_blank_' + str(uuid.uuid4())


def refresh_data(widgetName) :
   return 'trigger refreshData ' + widgetName


# Тут начинаются осмыслееные action-ы

def action_append_line(rows, widget_name=None, as_object=False):
   result = {}
   result['action'] = 'data';
   result['dataAction'] = 'append_blank_line';
   if (widget_name):
       result['widgetName'] = widget_name;
   result['records'] = rows;

   if as_object :
      return result
   else:
      return json.dumps(result, default = json_converter)


def action_close(as_object=False):
   if as_object:
      return {"action":"trigger close"}
   else :
      return json.dumps({"action":"trigger close"})



class WidgetMsgBox(Widget) :
   def __init__(self, status, title=None, message=None, action_ok=None, action_yes=None, action_no=None):
      self.name = 'messagebox'
      super().__init__(self.name)
      self._set_key('class', 'mbox')

      if not message:
         message=''

      self._set_key('desc.message', message)
      #Заголовок по статусу
      if not title :
         if status == 'success':
            self._set_key('desc.header', 'Успешно')
         elif status == 'error':
            self._set_key('desc.header', 'Ошибка')
         elif status == 'yes_no':
            self._set_key('desc.header', 'Подтверждение')
         elif status == 'alert':
            self._set_key('desc.header', 'Внимание')
      else :
  
         self._set_key('desc.header', title)


      #Кнопки
      if status == 'success':
         self._set_key('desc.success',  True)
         self._set_key('desc.display_ok',  'block')
         self._set_key('desc.display_no',  'none')
         self._set_key('desc.display_yes', 'none')
         self._set_key('desc.panel_type',  'primary')
         if not action_ok:
            self._set_key('desc.action_ok',  'trigger close')
         else:
            self._set_key('desc.action_ok',  'trigger close;' + action_ok)

      if status == 'alert':
         self._set_key('desc.alert',  True)
         self._set_key('desc.display_ok',  'block')
         self._set_key('desc.display_no',  'none')
         self._set_key('desc.display_yes', 'none')
         self._set_key('desc.panel_type',  'default')
         if not action_ok:
            self._set_key('desc.action_ok',  'trigger close')
         else:
            self._set_key('desc.action_ok',  'trigger close;' + action_ok)

      elif status == 'error':
         self._set_key('desc.error',  True)
         self._set_key('desc.display_ok',  'block')
         self._set_key('desc.display_no',  'none')
         self._set_key('desc.display_yes', 'none')
         self._set_key('desc.panel_type',  'warning')
         if not action_ok:
            self._set_key('desc.action_ok',  'trigger close')
         else:
            self._set_key('desc.action_ok',  'trigger close;' + action_ok)
      elif status == 'yes_no':
         self._set_key('desc.yes_no',  True)
         self._set_key('desc.display_ok',  'none')
         self._set_key('desc.display_no',  'block')
         self._set_key('desc.display_yes', 'block')
         self._set_key('desc.panel_type',  'default')
         if not action_yes:
            self._set_key('desc.action_yes', 'trigger close')
         else:
            self._set_key('desc.action_yes', 'trigger close;' + action_yes)

         if not action_no:
            self._set_key('desc.action_no', 'trigger close')
         else:
            self._set_key('desc.action_no', 'trigger close;' + action_no)


def mbox(status='success', title=None, message=None, action_ok=None, action_yes=None, action_no=None, pass_context=False):
   win = Window('windowmb','*')
   if pass_context:
      win.pass_context(flask.request.args)
   mb = WidgetMsgBox(status, title=title, message=message, action_ok=action_ok, action_yes=action_yes, action_no=action_no)
   win.append(mb)
   return win.json()

def confirm(text, title=None, action_yes=None, action_no=None, status='yes_no', pass_context=True):
   return mbox(status, title, message=text, action_yes=action_yes, action_no=action_no, pass_context=True)

def error(text, title=None, action_ok=None):
   return mbox('error', message=text, title=title, action_ok=action_ok)

def exception_error(request, ex = None):
    log.exception(request.url)
    (type, value, tb) = sys.exc_info()
    stack = traceback.extract_tb(tb, 10)
    text = ''
    for entry in stack:
        text_line = '<p>{0}<br/>line {1} in {2} : {3}<p>'.format(entry[0], 
            f'<span style="font-size:large">{entry[1]}</span>', 
            entry[2], 
            f'<span style="font-size:large">{entry[3]}</span>', 
            )
        text += text_line

    #text += traceback.format_exception( type , value, tb ) 
    #text += traceback.format_stack()
    #text = '{0} : {1}:{2}'.format(type, value, traceback)
    return mbox('error', message=text, title='Internal Program Error', action_ok=None)

def alert(text, title=None,  action_ok=None):
   return mbox('alert', message=text, title=title, action_ok=action_ok)

def success(text, title=None, action_ok=None):
   return mbox('success', message=text, title=title, action_ok = action_ok)

def action_none(widget_name=None, as_object=False):
   result = {}
   result['action'] = 'none';
   if (widget_name):
       result['widgetName'] = widget_name;
   if as_object:
      return result
   else :
      return json.dumps(result)


def response (*args):
   return '[' + ','.join(args) + ']'
   

      
   



