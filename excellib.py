import sys, os, threading
from xlwt import *
import xlrd


def savexls(filepath, data):
	
	book = Workbook(encoding="utf-8")
	
	sheet = book.add_sheet("sheet1")
	style = XFStyle()
	style.num_format_str = '0.00'
	rowindex = 0
	for i, r in enumerate (data):
		heahers = []
		values = []
		for j, col in enumerate(r):
			if j % 2 == 0:
				heahers.append(col)
			else:			
				if isinstance(col, basestring):
					col = col.strip()			
				values.append(col)
		if i==0:
			#write headers
			for colindex, h in enumerate(heahers):
				sheet.write(0,colindex,h)

		rowindex += 1
		for colindex, value in enumerate(values):
			sheet.write(rowindex,colindex,value, style)	
	book.save(filepath)			