import json

# Пустое действие. Продолжать работу и ничего не делать
def none(widget_name=None):
   result = {}
   result['action'] = 'none';
   if (widget_name):
       result['widgetName'] = widget_name;
   return json.dumps(result)
# Удаляет строку или строки 
# Если records == None - удаляется текущая активная строка таблицы
# Если records == string (один recid) удаляется одна строка с этим recid
# Если records == массив (список), интерпретируется как список recid и удаляеются строки с этими recid



def data_refresh_line(records= None, widget_name=None):
   pass


def signal_refresh_line(recid= None, widget_name=None):
   pass

def data_refresh_line():
   pass




