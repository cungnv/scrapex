#encoding: utf-8

from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function

from builtins import range
from builtins import object
import os
import csv
from pymongo import MongoClient
from datetime import datetime


from . import common

class DB(object):
	"""Provides a scaleable storage for big scrapes."""
	def __init__(self, config):
		
		self.config = config

		if 'host' in config:
			self.client = MongoClient(config['host'], config['port'])
		else:
			self.client = MongoClient()

		#init the database	
		self._db = self.client[config['dbname']]


	def exists_search(self, _id):
		_item = self.get_search(_id)
		if _item:
			return True
		else:
			return False	

	def insert_search(self, _id_or_dict):
		if isinstance(_id_or_dict, dict):
			#search dict provided
			
			_id_or_dict.update({'created': datetime.now()})
			return self._db.searches.insert(_id_or_dict)
		else:	
			#just _id provided
			return self._db.searches.insert({'_id': _id_or_dict, 'created': datetime.now()})

	def get_search(self, _id):
		return self._db.searches.find_one({'_id': _id})


	def remove_search(self, _id):
		self._db.searches.delete_one({'_id': _id})
	def remove_searches(self, query={}):
		self._db.searches.delete_many(query)

	def update_search(self, search):
		self._db.searches.update_one({'_id': search['_id']},{'$set': search}, upsert=True)
	
	def count_searches(self, query={}):
		return self._db.searches.count(query)
	

	def insert_item(self, item):
		if '_id' in item:
			#check for existence first
			if self.exists_item(item['_id']):
				return False


		self._db.items.insert(item)

		return True


	def insert_items(self, items):
		self._db.items.insert_many(items)

	def insertorupdate_item(self, item):
		
		self._db.items.update_one({'_id': item['_id']},{'$set': item}, upsert=True)
	
	def get_item(self, _id):
		return self._db.items.find_one({'_id': _id})
	
	def remove_item(self, _id):
		self._db.items.delete_one({'_id': _id})

	def remove_items(self, conditions = {}):
		self._db.items.delete_many(conditions)

	
	def update_item(self, item):

		self._db.items.update_one({'_id': item['_id']},{'$set': item}, upsert=False)

	def update_items(self, query, set_dict):	
		self._db.items.update_many(query, {'$set': set_dict})

	def count_items(self, query={}):
		return self._db.items.count(query)

	def exists_item(self, _id):
		_item = self.get_item(_id)
		if _item:
			return True
		else:
			return False	
	
	def _compile_all_fields(self,include_hidden_fields = False, exclude_fields = [], query={}, limit=10000):
		fields = []
		for item in self._db.items.find(query).limit(limit):#just need first 10,000 records to find all possible fields?
			for field in list(item.keys()):
				if field in exclude_fields:
					continue
					
				if field.startswith('_'):
					#hidden field
					if not include_hidden_fields:
						continue

				if field not in fields:
					fields.append(field)

		return sorted(fields)

	def export_items(self, dest_file, query = None, limit = None, sort=None, fields = None, include_hidden_fields = False, multicol_fields={}, exclude_fields = []):
		
		""" 
		@query: None means all items
		
		@fields: None means all fields

		"""
		if os.path.exists(dest_file):
			os.remove(dest_file)

		if not fields:
			fields =self._compile_all_fields(include_hidden_fields, exclude_fields=exclude_fields)

		format = common.DataItem(dest_file).subreg('\.([a-z]{2,5})$').lower()
		
		rows = []

		query = query or {}
		
		cnt = self.count_items(query)
		
		print('cnt: {}'.format(cnt))		


		cursor = self._db.items.find(query)

		if sort:
			cursor = cursor.sort(sort)

		if limit:
			cursor = cursor.limit(limit)
				
		for item in cursor:
			res = []

			for field in fields:
				# value = item.get(field) or ''
				value = item.get(field)
				if value is None:
					value = ''

				if field in multicol_fields:
					maxcol = multicol_fields[field]['maxcol']
					field_format = multicol_fields[field]['field_format']


					parts = []
					if value is None:
						value = []

					if isinstance(value, list):
						parts = value
					
					else:
						parts = value.split('|')

					if len(parts) < maxcol:
						#normalize
						for i in range(maxcol-len(parts)):
							parts.append('')


					for i in range(maxcol):
						res.append(field_format.format(i+1))
						res.append(parts[i])

				else:	
					res.append(field)
					res.append(value)

					
			if format == 'csv':		
				common.save_csv(dest_file, res)
			else:
				rows.append(res)	

		
		if format == 'xls':
			from . import excellib
			excellib.save_xls(dest_file, rows)
		elif format == 'xlsx':
			from . import excellib
			excellib.save_xlsx(dest_file, rows)	


	def insert_log(self, _dict):
			
		_dict.update({'created': datetime.now()})
		return self._db.logs.insert(_dict)

	def remove_logs(self, query={}):
		self._db.logs.delete_many(query)


	def get_logs(self, query={}):
		logs = []

		for log in self._db.logs.find(query):

			logs.append(log)

		return logs	


			