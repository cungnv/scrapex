import os
try:
	from setuptools import setup, find_packages
except ImportError:
	from distutils.core import setup, find_packages
	
setup(
	name='scrapex', 
	version='0.1.1',
	packages=find_packages(),
	author='Cung Nguyen',
	author_email='cungjava2000@gmail.com',
	description='A simple web scraping lib for Python',    
	long_description= 'You can also install by download the package here:\n https://github.com/cungnv/scrapex/archive/master.zip',
	url='https://github.com/cungnv/scrapex',   
	download_url = 'https://github.com/cungnv/scrapex/archive/master.zip', 
	install_requires = [
		'lxml',
		'xlwt',
		'xlrd',
		'openpyxl',
		'twisted',
		'pyOpenSSL',
		'service_identity'
	],
	
	license='LGPL',

)
