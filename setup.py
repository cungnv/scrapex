import os
from distutils.core import setup

setup(
    name='scrapex', 
    version='0.1',
    packages=['scrapex'],
    package_dir={'scrapex':'.'},
    author='Cung Nguyen',
    author_email='cungjava2000@gmail.com',
    description='A simple web scraping lib for Python',    
    url='https://github.com/cungnv/scrapex',   
    download_url = 'https://github.com/cungnv/scrapex/archive/master.zip', 
    license='LGPL',
)
