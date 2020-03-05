#encoding: utf-8

import os
try:
	from setuptools import setup, find_packages
except ImportError:
	from distutils.core import setup, find_packages
	
setup(
	name='scrapex', 
	version='0.2.0',
	packages=find_packages(),
	author='Cung Nguyen',
	author_email='cungjava2000@gmail.com',
	description='A simple web scraping framework in Python',    
	long_description= 'You can also install by download the package here:\n https://github.com/cungnv/scrapex/archive/master.zip',
	url='https://github.com/cungnv/scrapex',   
	download_url = 'https://github.com/cungnv/scrapex/archive/master.zip', 
	
	install_requires = [
		'lxml',
		'requests',
		'openpyxl',
		'pyOpenSSL',
		'future',
	],
	
	license='MIT',

	classifiers=[
        
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        
    ],

)
