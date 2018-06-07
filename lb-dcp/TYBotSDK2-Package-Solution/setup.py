from setuptools import setup, find_packages
from distutils.core import setup

setup(
      name="TYBotSDK2",
      version="4.1.1",
      packages=find_packages(exclude=['contrib', 'docs', 'tests']),
      author="www.lessnet.cn",
      author_email="pxk@lessnet.cn",
      url="http://www.lessnet.cn",
      description="LessNet Bot Framework client side development SDK"
      )
