import cx_Oracle
from domino.core import log

def get_fsrar_desc(key, cursor):
      q = "select f11 from db1_document where type=63111172 and code = :1"
      cursor.execute(q, [key])
      return cursor.fetchone()[0]

class Metric:
    def __init__(self, id, uid=None, name = None, product_id = None, hex = None, desc = None, is_hasp = False, is_memohasp=False):
        self.id = id
        self.uid = uid
        self.hex = hex
        self.name = name if name is not None else id
        self.product_id = product_id
        self.desc = desc
        self.is_hasp = is_hasp
        self.is_memohasp = is_memohasp
    def __eq__(self, value):
        return self.id == value.id
    def __ne__(self, value):
        return self.id != value.id
    def __str__(self):
        return self.id

    @staticmethod
    def get(query, default = None):
        global by_id
        if query is None:
            return None
        metric = by_id.get(query.upper(), default)
        return metric
        
    @staticmethod
    def find_by_uid(query, default = None):
        global by_uid
        if query is None:
            return None
        return by_uid.get(query, default)

    @staticmethod
    def find_by_hex(query, default = None):
        global by_hex
        if query is None:
            return None
        return by_hex.get(query, default)

    @staticmethod
    def find(query, default = None):
        if query is None:
            return None
        metric = Metric.get(query)
        if metric is None:
            return Metric.find_by_uid(query, default)
        else:
            return metric

NONE = Metric('NONE', uid='48431409[59375617]', hex='02E30131038A0001', desc='Без ключа защиты (Без ключа)')
COMPUTER = Metric('COMPUTER', name="Компьютер", uid='48431409[63111169]', hex='02E3013103C30001', desc="Ключ привязки к компьютеру (v.1) (CfgKEY-1)" )
MOBILE = Metric('MOBILE', name="Планшет", uid='48431409[63111172]', hex='02E3013103C30004', desc="Ключ привязки к мобильному устройству (IMEI)")
SERVER = Metric('SERVER', name="Сервер", uid='48431409[63111173]', hex='02E3013103C30005', desc='Ключ привязки к серверу приложений (APPSERVER)')
LOCATION =  Metric('LOCATION', name="Локация", uid="48431409[63111174]", hex="02E3013103C30006", desc="Ключ привязки к локации (подразделению) (LOCATION)")
FR_REGNO = Metric('FR_REGNO', name="Фискальный регистратор", uid='48431409[63111175]', hex='02E3013103C30007', desc="Ключ привязки к регистрационному номеру ФР (FR_REGNO)")

NETHASP = Metric('HASP', desc="HASP")
NETHASP_5 = Metric('NETHASP-5', is_hasp=True, uid='48431409[48431106]', hex='02E3013102E30002', desc="NetHASP-5 (NetHASP-5)")
NETHASP_10 = Metric('NETHASP-10', is_hasp=True, uid='48431409[48431107]', hex='02E3013102E30003', desc="NetHASP-10 (NetHASP-10)")
NETHASP_20 = Metric('NETHASP-20', is_hasp=True,  uid='48431409[48431108]', hex='02E3013102E30004', desc="NetHASP-20 (NetHASP-20)")
NETHASP_50 = Metric('NETHASP-50', is_hasp=True,  uid='48431409[48431109]', hex='02E3013102E30005', desc='NetHASP-50 (NetHASP-50)')
NETHASP_100 = Metric('NETHASP-100', is_hasp=True,  uid='48431409[48431110]', hex='02E3013102E30006', desc="NetHASP-100 (NetHASP-100)")
NETHASP_UNLIM = Metric('NETHASP-UNLIM', is_hasp=True,  uid='48431409[48431111]', hex='02E3013102E30007', desc="NetHASP-Unlimited (NetHASP-ULM)")

MEMOHASP = Metric('MEMOHASP', desc="MEMOHASP")
MEMHASP_1 = Metric('MEMOHASP-1', is_memohasp=True, uid='48431409[48431112]', hex='02E3013102E30008', desc="MemoHASP-1 (MemoHASP-1)")
MEMHASP_4 = Metric('MEMOHASP-4', is_memohasp=True, uid='48431409[48431113]', hex='02E3013102E30009', desc="MemoHASP-4 (MemoHASP-4)")

FSRAR =  Metric('FSRAR', name="ФСРАР", uid='63111198[63111169]', hex='03C3001E03C30001', desc="Продукт RETAIL-ALCO (ФСРАР ID) : ФСРАР ID")
INN = Metric('INN', uid='63111198[63111170]', hex='03C3001E03C30002', desc='Продукт "Обмен ЭСФ, Казахстан" (БИН/ИИН) : БИН/ИНН ЭСФ KZ')


metrics = [
NONE,
COMPUTER,
MOBILE,
SERVER,
LOCATION, 
FR_REGNO,
NETHASP,
NETHASP_5,
NETHASP_10,
NETHASP_20,
NETHASP_50,
NETHASP_100,
NETHASP_UNLIM,
MEMOHASP,
MEMHASP_1,
MEMHASP_4,
FSRAR,
INN
]

by_id = { m.id: m for m in metrics }

by_uid = {}
for m in metrics:
    if m.uid is not None:
        by_uid[m.uid] = m

by_hex = {}
for m in metrics:
    if m.hex is not None:
        by_hex[m.hex] = m

