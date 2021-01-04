import os, json, datetime, requests
from domino.core import log, Version, VersionInfo

class GlobalStore:
    def __init__(self, server = 'rs.domino.ru'):
        self.server = server

    def get(self, method, params):
        query = f'https://{self.server}/domino/active/python/{method}'
        #log.debug(query)
        r = requests.get(query, params=params)
        #print(r.url)
        return r

    def post(self, method, data, files):
        query = f'https://{self.server}/domino/active/python/{method}'
        #return requests.post(self.server + q, data=data, files=files, verify=False)
        r = requests.post(query, data=data, files=files)
        #print (r.url)
        return r

    def get_versions(self, product):
        versions = []
        r = self.get('distro.get_versions', { 'product':str(product) })
        #log.debug(str(r.status_code))
        if r.status_code == 200:
            for version_id in r.json():
                version = Version.parse(version_id)
                if version is not None:
                    versions.append(version)
        #log.debug("%s %s", product, Version.versions_dump(versions))
        return versions

    def get_versions_of_draft(self, product, draft):
        versions = []
        for version in self.get_versions(product):
            if version.is_draft: 
                continue
            if draft.is_draft_of(version):
                versions.append(version)
        return versions

    def get_latest_version_of_draft(self, product, draft):
        latest = max(self.get_versions_of_draft(product, draft), default=None)
        #log.debug(f"{product} {latest}")
        return latest

    def get_latest_version(self, product):
        return max(self.get_versions(product), default=None)

    def get_version_info(self, product, version):
        params = {}
        params['product'] = product
        params['version'] = str(version) 
        r = self.get('distro.get_version_info', params)
        if r.status_code != 200:
            return None
        else:
            #log.debug(json.dumps(r.text))
            info = VersionInfo.loads(r.text)
            #log.debug(info.dumps())
            return info

    def version_exists(self, product, version):
        for v in self.get_versions(product):
            if v.id == str(version):
                return True
        return False

    def listdir(self, path):
        r = self.get('public.listdir', {'path':path})
        if r.status_code == 200:
            return json.loads(r.text)
        else:
            return []

    def download(self, path, file):
        r = requests.get(f'https://{self.server}/public/{path}')
        if r.status_code == 200:
            #os.makedirs(os.path.dirname(file), exist_ok=True)
            with open(file, 'bw') as f:
                f.write(r.content)
        else:
            msg = 'HTTP Error {0} : {1}'.format(r.status_code, r.text)
            raise Exception(msg)

    def download_distro(self, product, version, distro_file, return_responce = False):
        params = {}
        params['product_id'] = str(product)
        params['version'] = str(version)
        r = self.get('distro.get', params)
        if r.status_code == 200:
            #os.makedirs(os.path.dirname(distro_file), exist_ok=True)
            with open(distro_file, 'bw') as f:
                f.write(r.content)
        else:
            if not return_responce:
                msg = 'HTTP Error {0} : {1}'.format(r.status_code, r.text)
                raise Exception(msg)
        return r
 
    def upload(self, path, file):
        files = {'file' : (path, open(file, 'rb'), 'multipart/form-data') }
        r = self.post('public.upload', {'path': path}, files=files)
        if r.status_code != 200:
            msg = 'HTTP Error {0} : {1}'.format(r.status_code, r.text)
            raise Exception(msg)

    def upload_distro(self, product, version, distro_file):
        files = {'file' : (distro_file, open(distro_file, 'rb'), 'multipart/form-data')}
        data = {'sk':'dev', 'product': str(product), 'version' : str(version)}
              
        r = self.post('distro.upload', data=data, files=files)
      
        if r.status_code != 200:
            msg = 'HTTP Error {0} : {1}'.format(r.status_code, r.text)
            raise Exception(msg)

        # Дополнительная посылка
        data = {'product_id':str(product), 'version_id':str(version.draft())}
        url = 'http://rs.domino.ru:88/api/product/upload'
        files = {'file' : (distro_file, open(distro_file, 'rb'), 'multipart/form-data')}
        r = requests.post(url, data=data, files=files)
        log.debug(f'{r.url} {data} {distro_file}')
        if r.status_code != 200:
            msg = 'HTTP Error {0} : {1}'.format(r.status_code, r.text)
            raise Exception(msg)


