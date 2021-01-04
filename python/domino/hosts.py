import re

class Hosts:
    def __init__(self):
        self.lines = []
        with open('/etc/hosts') as f:
            for line in f:
                try:
                    line = line.strip()
                    address, names = re.split('\s+' , line, maxsplit=1, flags=0)
                    names = re.split('\s+' , names)
                    self.lines.append({'address':address, 'names' : names})
                except:
                    pass

    def save(self):
        with open('/etc/hosts', 'w') as f:
            for line in self.lines:
                if len(line['names']) > 0:
                    f.write("{0:15} {1}\n".format(line['address'], ' '.join(line['names'])))
    @staticmethod
    def print():
        with open('/etc/hosts') as f:
            for line in f:
                print(line.strip())

    def remove_name(self, name):
        name = str(name)
        for line in self.lines:
            try:
                line['names'].remove(name)
            except:
                pass

    def remove_address(self, address):
        address = str(address)
        for line in self.lines:
            if line['address'] == address:
                line['names'] = []

    def remove(self, pattern):
        self.remove_address(pattern)
        self.remove_name(pattern)

    def add(self, address, name):
        self.remove_name(name)
        for line in self.lines:
            if line['address'] == address:
                line['names'].append(name)
                return
        self.lines.append({'address':address, 'names':[name]})
