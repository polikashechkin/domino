
class Product:
    def __init__(self, id, uid = None, hex = None, name = None, desc = None):
        self.id = id
        self.uid = uid if uid is not None else ''
        self.hex = hex if hex is not None else ''
        self.name = name if name is not None else id
        self.desc = desc if desc is not None else 'Лицензия на продукт {0}'.format(id)
    def __eq__(self, value):
        return self.id == value.id
    def __ne__(self, value):
        return self.id != value.id
    def __str__(self): 
        return self.id
    @staticmethod
    def find_by_hex(product_hex, default= None):
        global by_hex
        if product_hex is None:
            return None
        return by_hex.get(product_hex, default)
    @staticmethod
    def get(product_id, default= None):
        global by_id
        if product_id is None:
            return None
        return by_id.get(product_id.upper(), default)
    @staticmethod
    def find_by_uid(uid, default= None):
        global by_uid
        if uid is None: 
            return None
        return by_uid.get(uid, default)
    @staticmethod
    def find(query, default= None):
        if query is None:
            return None
        p = Product.get(query)
        if p is not None:
            return p
        return Product.find_by_uid(query, default)

DOMINO_ID = 'DOMINO'

UNKNOWN = Product('UNKNOWN')
DOMINO = Product('DOMINO', desc="Универсальная лицензия на все продукты Домино как  с программной так и с аппаратной защитой")
RETAIL_STORE = Product('RETAIL-STORE','4653069[11]','0047000D0000000B')   
RETAIL_POS = Product('RETAIL-POS','4653069[2]','0047000D00000002', 'Торговая касса', desc='Лицензия на продукт RETAIL_POS как с программной так и с аппаратной защитой на компьютер')   
RETAIL_ALCO = Product('RETAIL-ALCO','4653069[42401798]','0047000D02870006', desc='Лицензия на продукт RETAIL-ALCO. Лицензия выдается на каждый ФСРАР индивидуально')   
RETAIL_OFFICE = Product('RETAIL-OFFICE','4653069[6]','0047000D00000006')   
RETAIL_BOX = Product('RETAIL-BOX','4653069[3]','0047000D00000003')   
RETAIL_STORE_2010 = Product('RETAIL-STORE-2010','4653069[5]','0047000D00000005')   
RETAIL_STORE_KZ = Product('RETAIL-STORE-KZ','4653069[8]','0047000D00000008')   
RETAIL_NET = Product('RETAIL-NET','4653069[7]','0047000D00000007')   
SALARY = Product('SALARY','4653069[12]','0047000D0000000C')   
RSBU_USN = Product('RSBU-USN','4653069[13]','0047000D0000000D')   
RSBU_OSNO = Product('RSBU-OSNO','4653069[14]','0047000D0000000E')   
EXCHANGE_EDI = Product('EXCHANGE-EDI','4653069[60424197]','0047000D039A0005')   
EXCHANGE_1C = Product('EXCHANGE-1C','4653069[19]','0047000D00000013')   
CRM = Product('CRM','4653069[40566786]','0047000D026B0002')
M_INVENT = Product('M_INVENT','4653069[63111170]','0047000D03C30002', 'Инвентаризация')
M_ASSIST = Product("M_ASSIST",'4653069[63111171]','0047000D03C30003', 'Мобильный помошник')
M_SS = Product("M_SS",'4653069[63111172]','0047000D03C30004')
M_CS = Product("M_CS",'4653069[63111173]','0047000D03C30005')
POS_SERVER = Product("POS_SERVER", '4653069[20]', '0047000D00000014', 'Сервер кассового оборудования')
CINEMA_POS = Product("CINEMA-POS", '4653069[21]', '0047000D00000015', 'Кинокасса')

products = [
UNKNOWN,
DOMINO,
RETAIL_STORE,
RETAIL_POS,
RETAIL_ALCO,
RETAIL_OFFICE,
RETAIL_BOX,
RETAIL_STORE_2010,
RETAIL_STORE_KZ,
RETAIL_STORE,
RETAIL_NET,
SALARY,
RSBU_USN,
RSBU_OSNO,
EXCHANGE_EDI,
EXCHANGE_1C,
CRM,
M_INVENT,
M_ASSIST,
M_SS,
M_CS,
POS_SERVER,
CINEMA_POS
]

by_id = { p.id: p for p in products }
by_uid = { p.uid: p for p in products }
by_hex = { p.hex: p for p in products }

