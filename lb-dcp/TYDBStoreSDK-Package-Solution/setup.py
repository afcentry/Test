from setuptools import setup, find_packages
from distutils.core import setup

setup(
      name="TYDBStoreSDK",
      version="0.0.1",
      packages=find_packages(exclude=['contrib', 'docs', 'tests']),
      author="www.lessnet.cn",
      author_email="pxk@lessnet.cn",
      url="http://www.lessnet.cn",
      description="LessNet Database Storage Manager Framework SDK"
      )
