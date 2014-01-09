import os
from distutils.core import setup

def read(filename):
    return open(os.path.join(os.path.dirname(__file__), filename)).read()

setup(
    name='scrapex', 
    version='0.1',
    packages=['scrapex'],
    package_dir={'scrapex':'.'},
    author='Cung Nguyen',
    author_email='cungjava2000@gmail.com',
    description='A simple web scraping lib for Python',    
    url='https://github.com/cungnv/scrapex',    
    license='lgpl',
)
