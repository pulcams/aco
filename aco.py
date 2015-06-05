#!/usr/bin/env python
#-*- coding: utf-8 -*-

"""
For Arabic Collections Online (ACO)

-Data is entered into an MS Access table. 
-A picklist per batch is exported as a csv picklist (using an Access form).
-This script fills in any missing fields, fetches the MARCXML, and outputs two spreadsheets,
one for NYU and one for our internal use. It returns a single zip file.

To run locally, fill in aco.cfg and then...
`python jinn.py`

NOTE: The picklist needs to be Unicode csv, code page 65001 utf-8, without BOM 
(it will be by default if using the Access form).

For more, see the documentation in our shared folder.

from 20150224
pmg
"""

import argparse
import ConfigParser
import csv
import cx_Oracle
import glob
import httplib
import logging
import pymarc
import os
import requests
import shutil
import subprocess
import sys
import tarfile
import time
import urllib2
import xlsxwriter
import zipfile
from lxml import etree

today = time.strftime("%Y%m%d")

# configuration file parsing (aco.cfg)
config = ConfigParser.RawConfigParser()
config.read('aco.cfg') # <= change this when testing locally
indir = config.get('env', 'indir')
outdir = config.get('env', 'outdir')
logdir = config.get('env','logdir')
share = config.get('env','share')
export = config.get('env','export')


def main(picklist):
	"""
	The main engine...
	"""
	logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p',filename='log/aco_'+today+'.log',level=logging.INFO)
	
	name, ext = os.path.splitext(picklist.filename)
	pul_picklist = 'pul_'+name+ext

	batchno = str(name).split('_')[3]
	
	if not glob.glob(r''+outdir+'*.xml'):
		logging.info("-" * 50)
		make_new_csv(picklist,pul_picklist)
		generate_spreadsheets(picklist,pul_picklist)
		get_v2m_mrx(pul_picklist)
		format_xml(outdir)
		logging.info("-" * 50)

	return zip_mrx(name) # => jinn.py => index.tpl


def make_new_csv(picklist,pul_picklist):
	"""
	The picklist is a csv file as output from the Access db (exported as code page 65001 utf-8, without BOM -- this is important). 
	Search Voyager for any missing data and create a fuller copy of the list for next steps.
	"""
	try:
		os.remove(outdir+pul_picklist)
	except OSError:
		pass

	name, ext = os.path.splitext(picklist.filename)

	paramFile = picklist.file
	reader = csv.DictReader(paramFile,delimiter=',', quotechar='"')

	with open(outdir+pul_picklist,'wb+') as outfile:
		writer = csv.writer(outfile)
		row = ['LIB','SYS','Item','Volume','CHRON','CCG_BOOK_ID','Crate','Date','CP','Tag_100','Tag_240','Tag_245','Tag_260','Tag_300','Tag_5XX','Tag_6XX','Callno','LOC','COMPLETE Y/N','Notes','Handling instructions','batchNo','objectNo','NOS','BW','Condition','CAT_PROB','other']
		writer.writerow(row) 
			
	for row in reader:
		lib = row['LIB']
		bibid = row['SYS.']
		barcode = row['Item .']
		vol = row['Volume .']
		cron = row['CHRON']
		ccg = row['CCG_BOOK_ID']
		crate = row['Crate .']
		date = row['Date']
		cp = row['CP']
		tag100 = row['TAG_100']
		tag240 = row['TAG_240']
		tag245 = row['TAG_245']
		tag260 = row['TAG_260']
		tag300 = row['TAG_300']
		tag5xx = row['TAG_5XX']
		tag6xx = row['TAG_6XX']
		callno = row['Call.']
		loc = row['LOC']
		complete = row['COMPLETE Y/N']
		notes = row['NOTES']
		handl = row['Handling Instructions']
		batchid = row['batchNo']
		objid = row['objectNo']
		ccgid = str(ccg + objid.zfill(6))
		nos = row['NOS']
		bw = row['BW']
		cond = row['Condition']
		cat_prob = row['CAT_PROB']
		other = row['other']
		
		if (bibid == '' and barcode != '') or (cron == '' and vol == ''):
			# When books are added manually, the barcode will be filled in but there'll be no bibid. Also, sometimes cron and vol have been subsequently added to Vger, so...
			row = get_missing_data(barcode,ccgid,batchid,objid,crate,nos,bw,cond,cat_prob,other)
		else:
			#row = get_missing_data(barcode,ccgid,batchid,objid,crate,nos,bw,cond,cat_prob,other) # <= this will just go ahead and check everything against Vger
			row = lib,bibid,barcode,vol,cron,ccgid,crate,date,cp,tag100,tag240,tag245,tag260,tag300,tag5xx,tag6xx,callno,loc,complete,notes,handl,batchid,objid,nos,bw,cond,cat_prob,other

		ccg = ccgid # make sure the ccgid is in the form of 'princeton_aco000001' ('princeton_aco' plus objid)
		# output spreadsheet for get_v2m_mrx()
		with open(outdir+pul_picklist,'ab+') as outfile: # this will be the enhanced copy of the picklist in ./in
			writer = csv.writer(outfile)
			writer.writerow(row)


def get_v2m_mrx(pul_picklist):
	"""
	Get marcxml using v2m service, and strip out HLDG info.
	"""
	logging.info("get_v2m_mrx()")
	conn = httplib.HTTPConnection("diglib.princeton.edu")
	flag = ""
	filename = "aco_bibs"
	timestamp = time.strftime("%Y%m%d")
	
	with open(outdir+pul_picklist,'rb') as csvfile:
		reader = csv.reader(csvfile,delimiter=',', quotechar='"')
		firstline = reader.next() # skip the first row
		bibs_gotten = []
		
		for row in reader:
			bibid = row[1]
			objid = row[22]
					
			if bibid not in bibs_gotten:
				conn.request("POST", "/tools/v2m/"+bibid+"?format=marc")
				got = conn.getresponse()
				data = got.read()
				conn.close()
			else:
				continue
			
			doc = etree.fromstring(data)
						
			try:
				f001 = doc.find("marc:record[@type=\'Bibliographic\']/marc:controlfield[@tag=\'001\']",namespaces={'marc':'http://www.loc.gov/MARC21/slim'})
				f008 = doc.find("marc:record[@type=\'Bibliographic\']/marc:controlfield[@tag=\'008\']",namespaces={'marc':'http://www.loc.gov/MARC21/slim'})
				rec = f001.getparent()
				f001_index = rec.index(f001) # get the position of the 001
				f008_index = rec.index(f008) # and the position of the 008
	
				# remove the Holding record(s)
				for hldg in doc.xpath("//marc:record[@type=\'Holdings\']",namespaces={'marc':'http://www.loc.gov/MARC21/slim'}):
					hldg.getparent().remove(hldg)
				
				# insert 003 and 024
				for bibrec in doc.xpath("//marc:record[@type=\'Bibliographic\']",namespaces={'marc':'http://www.loc.gov/MARC21/slim'}):
					marc = "http://www.loc.gov/MARC21/slim"
					ns = {"marc", marc}
					# 003
					f003 = etree.Element("{"+marc+"}controlfield",tag="003")
					f003.text = "NjP"
					# 024
					f024 = etree.Element("{"+marc+"}datafield",tag="024")
					f024.attrib['ind1']='7'
					f024.attrib['ind2']=' '
					# 024$a
					f024a = etree.SubElement(f024,"{"+marc+"}subfield",code="a")
					f024a.text = 'princeton_aco' + objid.zfill(6)
					# 024$2
					f0242 = etree.SubElement(f024, "{"+marc+"}subfield",code="2")
					f0242.text = "local"
					
					bibrec.insert(f001_index + 1,f003) # put the 003 immediately following the 001
					bibrec.insert(f008_index + 2,f024) # put the 024 after the 008
										
					data = etree.tostring(doc,pretty_print=True,encoding='UTF-8', xml_declaration=True) # encoding='UTF-8' is important!
					
				f = open(outdir+'princeton_aco'+bibid+'_marcxml.xml', 'wb+')
				f2 = open('log/'+filename + '_out_'+timestamp+'.csv', 'a')
 
				f.writelines(data)
				f.close()
				flag = "ok"
				f2.write("%s, %s\n" % (bibid, flag))
				f2.close()
				bibs_gotten.append(bibid)
				#print('Got mrx for '+str(bibid))
			except:
				f2 = open('log/'+filename + '_out_'+timestamp+'.csv', 'a')
				flag = "not found"
				f2.write("%s, %s\n" % (bibid, flag))
				f2.close()
				#print('Didn\'t get mrx for '+str(bibid))
	msg = 'MARCXML files are in place.'
	logging.info(msg)


def format_xml(work):
	"""
	Format marcxml.
	"""
	logging.info("formatting_xml")
	try:
		subprocess.call(['./batch-format.sh',work])
		msg = 'XML has been beautifully formatted.'
	except:
		msg = 'Problem with batch-format.sh',sys.exc_info()[0]
	logging.info(msg)
	#print(msg)
	
	
def get_missing_data(bc,ccg,bat,obj,crate,nos,bw,cond,cat_prob,other):
	"""
	Pull in missing data from Vger, based on barcode.
	"""
	user = config.get('database', 'user')
	pw = config.get('database', 'pw')
	sid = config.get('database', 'sid')
	ip = config.get('database', 'ip')
	
	dsn_tns = cx_Oracle.makedsn(ip,1521,sid)
	db = cx_Oracle.connect(user,pw,dsn_tns)
	
	sql = """SELECT 'Princeton' as LIB, BIB_MFHD.BIB_ID, ITEM_BARCODE.ITEM_BARCODE, MFHD_ITEM.ITEM_ENUM, 
		MFHD_ITEM.CHRON,'%s' AS CCG_BOOK_ID,'%s' AS CRATE,BIB_TEXT.BEGIN_PUB_DATE, BIB_TEXT.PLACE_CODE, 
		BIB_TEXT.AUTHOR, 
		princetondb.GETBIBTAG(BIB_TEXT.BIB_ID, '240') as TAG_240,
		BIB_TEXT.TITLE_BRIEF as TAG_245,
		princetondb.GETBIBTAG(BIB_TEXT.BIB_ID, '260') as TAG_260,
		princetondb.GETBIBTAG(BIB_TEXT.BIB_ID, '300') as TAG_300,
		princetondb.GETALLBIBTAG(BIB_TEXT.BIB_ID, '5xx') as TAG_5XX,
		princetondb.GETALLBIBTAG(BIB_TEXT.BIB_ID, '6xx') as TAG_6XX,
		MFHD_MASTER.DISPLAY_CALL_NO, 
		LOCATION.LOCATION_CODE,
		'' as complete_yn,
		'' as NOTES, 
		'' as handling_instructions,
		'%s' as batchNo, 
		'%s' as objectNo,
		'%s' as NOS,
		'%s' as BW,
		'%s' as Condition,
		'%s' as CAT_PROB,
		'%s' as other
		FROM 
		ITEM_BARCODE 
		INNER JOIN MFHD_ITEM ON ITEM_BARCODE.ITEM_ID = MFHD_ITEM.ITEM_ID
		INNER JOIN BIB_MFHD ON MFHD_ITEM.MFHD_ID = BIB_MFHD.MFHD_ID
		INNER JOIN BIB_TEXT ON BIB_MFHD.BIB_ID = BIB_TEXT.BIB_ID
		INNER JOIN MFHD_MASTER ON MFHD_ITEM.MFHD_ID = MFHD_MASTER.MFHD_ID 
		INNER JOIN LOCATION ON MFHD_MASTER.LOCATION_ID = LOCATION.LOCATION_ID
		WHERE ITEM_BARCODE.ITEM_BARCODE='%s'"""

	c = db.cursor()
	c.execute(sql % (ccg,crate,bat.zfill(3),obj.zfill(6),nos,bw,cond,cat_prob,other,bc))
	new_row = []
	for row in c:
		for x in row:
			if x is None: x = ""
			new_row.append(str(x))
		return new_row
	c.close()


def generate_spreadsheets(picklist,pul_picklist):
	"""
	Generate spreadsheets for (1) nyu and (2) local use
	"""
	versions = ['nyu','pul']
	name, ext = os.path.splitext(picklist.filename)
	outfile = str(name+ext)
	deliverables = []

	for version in versions:
		if version == 'pul':
			outfile = 'pul_'+outfile
		
		with open(outdir+pul_picklist,'rb') as csvfile:
			reader = csv.reader(csvfile,delimiter=',', quotechar='"')
			workbook = xlsxwriter.Workbook(outdir+outfile.replace('.csv','.xlsx'))
			worksheet = workbook.add_worksheet()
			worksheet.set_column('C:C', 15) # barcode
			worksheet.set_column('F:F', 25) # ccg id

			for r, row in enumerate(reader):
				for c, col in enumerate(row):
					if version == 'nyu':
						if c in (0,1,2,3,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19): # only write out the columns specified in MOA
							worksheet.write(r,c,col.decode('utf-8'))
					elif version == 'pul': # just being explicit here
						worksheet.write(r,c,col.decode('utf-8'))
			workbook.close()
		deliverables.append(outdir+outfile.replace('.csv','.xlsx'))


def cleanup():
	"""
	After zipping them, remove the xml, csv and xlsx files
	"""
	types = ('*.xml','*.csv','*.xlsx')
	files_gotten = []
	# clean up...
	for files in types:
		files_gotten.extend(glob.glob(r'./out/'+files))
		for tempfiles in files_gotten:
			try:
				os.remove(tempfiles)
			except:
				pass


def zip_mrx(picklist):
	"""
	Zip up the two xslx files and the xml files.
	"""
	# zip up...
	zf = './out/'+picklist+'.zip'
	# first, delete zip if already there to avoid dupes
	if os.path.exists(zf):
		os.remove(zf)
	zipper = zipfile.ZipFile(zf,'w')
	types = ('*.xml','*.xlsx')
	files_gotten = []
	for files in types:
		files_gotten.extend(glob.glob(r'./out/'+files))
		for name in files_gotten:
			zipper.write(name, os.path.basename(name), zipfile.ZIP_DEFLATED)
	zipper.close()
	cleanup()
	# return the zipfile for download...
	zipped = 'file://'+outdir+picklist+'.zip'
	return (urllib2.urlopen(zipped))
