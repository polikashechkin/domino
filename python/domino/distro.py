import os, sys
import json
import shutil
import requests
import datetime
import subprocess
import pickle
import logging
from domino.core import Version, VersionInfo


SERVER_CONFIG_FILE = '/DOMINO/domino.config.info.json'
INSTALLED_PRODUCTS = '/DOMINO/products'
STORE_PRODUCTS = '/DOMINO/public/products'
PUBLIC_PRODUCTS = '/DOMINO/public/products'
JOBS = '/DOMINO/jobs'
JOB_REPORTS = '/DOMINO/jobs.reports'
DOMINO_LOG = '/DOMINO/log'

class Distro:
    def __init__(self, product, version):
        self.product = product
        self.version = Version.parse(str(version))
        self.file_name = Distro.make_file_name(product, version)
        self.folder = os.path.join(PUBLIC_PRODUCTS, str(product), str(version))
        self.file = os.path.join(self.folder, self.file_name)
        self.apk = os.path.join(self.folder, f'{product}.apk')

    @staticmethod
    def make_file_name(product, version):
        return f'{product}.{version}.zip'

    @staticmethod
    def product_folder(product):
        return os.path.join(PUBLIC_PRODUCTS, str(product))

    @property
    def exists(self):
        return os.path.isfile(self.file)

    def version_info(self):
        info_file = os.path.join(self.folder, "info.json")
        if os.path.isfile(info_file):
            with open(info_file, "r") as f:
                return VersionInfo.load(f)
        return None

    @staticmethod
    def get_versions(product, draft = None):
        versions = []
        product_folder = Distro.product_folder(product)
        if os.path.isdir(product_folder):
            for version_id in os.listdir(product_folder):
                version = Version.parse(version_id)
                if version is not None:
                    if draft is None or draft.is_draft_of(version):
                        versions.append(version)
        return versions

    @staticmethod
    def get_latest_version(product, draft = None):
        return max(Distro.get_versions(product, draft), default=None)

