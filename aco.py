#!/usr/bin/env python
#-*- coding: utf-8 -*-

"""
For Arabic Collections Online (ACO)
From csv picklist get MARCXML from Voyager, insert 003, insert CCG_BOOK_ID, format xml
Set things up aco.cfg. Run like this:
`python aco.py -f ACO_princeton_NYU_batch001_20150227.csv`
MARCXML and completed picklist will be in ./out dir.
!!! NOTE: The picklist needs to be Unicode csv. See documentation in our shared folder. !!!
from 20150224
pmg
"""

import argparse
import ConfigParser
import csv
import cx_Oracle
import httplib
import logging
import pymarc
import os
import shutil
import subprocess
import sys
import time
from lxml import etree

today = time.strftime("%Y%m%d")

# commandline argument parsing
parser = argparse.ArgumentParser(description='Process ACO batch files as csv.')
parser.add_argument('-f','--filename',type=str,dest="picklist",help="The full name of csv picklist, e.g. 'ACO_princeton_NYU_batch001_20150227.csv'",required=True)
args = vars(parser.parse_args())
picklist = args['picklist']

# configuration file parsing (aco.cfg)
config = ConfigParser.RawConfigParser()
config.read('aco.cfg')
indir = config.get('env', 'indir')
outdir = config.get('env', 'outdir')
logdir = config.get('env','logdir')
share = config.get('env','share')

# logging
logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p',filename='log/aco_'+today+'.log',level=logging.INFO)

def main():
	logging.info("-" * 50)
	setup()
	fetch_picklist()
	make_new_csv(picklist)
	get_v2m_mrx()
	print('-' * 25)
	format_xml(outdir)
	print('all done!')
	logging.info("-" * 50)

def setup():
	"Simply create log, in and out dirs if they don't already exist."
	
	dirs = [indir,outdir,logdir]

	for d in dirs:
		if not os.path.exists(d):
			os.makedirs(d)
			
def fetch_picklist():
	"Fetch the batch picklist from the Windows share."
	shutil.copyfile(share+picklist, indir+picklist)

def make_new_csv(picklist):
	"Input is csv picklist. Create a copy with any missing fields filled in."
	try:
		os.remove(outdir+picklist)
	except OSError:
		pass
	
	with open(indir+picklist,'rb') as csvfile:
		reader = csv.reader(csvfile,delimiter=',', quotechar='"')
		#firstline = reader.next() # skip header row
		for row in reader:
			bibid = row[1]
			barcode = row[2]
			ccgid = row[5]
			batchid = row[21]
			objid = row[22]
			
			# When books are added manually, the barcode will be filled in but there'll be no bibid...
			if bibid == '' and barcode != '':
				row = get_missing_data(barcode,ccgid,batchid,objid)
				
			with open(outdir+picklist,'ab+') as outfile: # this will be an enhanced copy of the picklist in ./in
				writer = csv.writer(outfile)
				writer.writerow(row)
    	
def get_v2m_mrx():
	"Get marcxml using v2m service, and strip out HLDG info."
	logging.info("get_v2m_mrx()")
	conn = httplib.HTTPConnection("diglib.princeton.edu")
	flag = ""
	filename = "aco_bibs"
	timestamp = time.strftime("%Y%m%d")
	
	with open(outdir+picklist,'rb') as csvfile:
		reader = csv.reader(csvfile,delimiter=',', quotechar='"')
		firstline = reader.next()
		for row in reader:
			bibid = row[1]
			batchid = row[21]
			objid = row[22]
			conn.request("POST", "/tools/v2m/"+bibid+"?format=marc")
			got = conn.getresponse()
			data = got.read()
			conn.close()
			
			doc = etree.fromstring(data)
						
			try:
				f001 = doc.find("marc:record[@type=\'Bibliographic\']/marc:controlfield[@tag=\'001\']",namespaces={'marc':'http://www.loc.gov/MARC21/slim'})
				f008 = doc.find("marc:record[@type=\'Bibliographic\']/marc:controlfield[@tag=\'008\']",namespaces={'marc':'http://www.loc.gov/MARC21/slim'})
				rec = f001.getparent()
				#rec2 = f008.getparent()
				f001_index = rec.index(f001) # get the position of the 001
				f008_index = rec.index(f008) # and the position of the 008
				
				# remove the Holding record(s)
				for hldg in doc.xpath("//marc:record[@type=\'Holdings\']",namespaces={'marc':'http://www.loc.gov/MARC21/slim'}):
					hldg.getparent().remove(hldg)
				
				# insert the an 003
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
					f024a.text = 'princeton_aco' + batchid + objid
					# 024$2
					f0242 = etree.SubElement(f024, "{"+marc+"}subfield",code="2")
					f0242.text = "local"
					
					bibrec.insert(f001_index + 1,f003) # put the 003 immediately following the 001
					bibrec.insert(f008_index + 2,f024) # put the 024 after the 008
										
					data = etree.tostring(doc,pretty_print=True,encoding='utf-8')
					
				f = open(outdir+'princeton_aco'+bibid+'_marcxml.xml', 'wb+')
				f2 = open('log/'+filename + '_out_'+timestamp+'.csv', 'a')
 
				f.writelines(data)
				f.close()
				flag = "ok"
				f2.write("%s, %s\n" % (bibid, flag))
				f2.close()
				print('Got mrx for '+str(bibid))
			except:
				f2 = open('log/'+filename + '_out_'+timestamp+'.csv', 'a')
				flag = "not found"
				f2.write("%s, %s\n" % (bibid, flag))
				f2.close()
				print('Didn\'t get mrx for '+str(bibid))
	msg = 'MARCXML files are in place.'
	logging.info(msg)

def format_xml(work):
	"Will format marcxml and mets."
	logging.info("formatting_xml")
	try:
		subprocess.call(['./batch-format.sh',work])
		msg = 'XML has been beautifully formatted.'
	except:
		msg = 'Problem with batch-format.sh',sys.exc_info()[0]
	logging.info(msg)
	print(msg)
	
def get_missing_data(bc,ccg,bat,obj):
	"""
	When a barcode has been manually added to the picklist, pull in the missing data.
	"""
	user = config.get('database', 'user')
	pw = config.get('database', 'pw')
	sid = config.get('database', 'sid')
	ip = config.get('database', 'ip')
	
	dsn_tns = cx_Oracle.makedsn(ip,1521,sid)
	db = cx_Oracle.connect(user,pw,dsn_tns)
	
	sql = """SELECT 'Princeton' AS LIB, BIB_MFHD.BIB_ID, ITEM_BARCODE.ITEM_BARCODE, MFHD_ITEM.ITEM_ENUM, 
		MFHD_ITEM.CHRON,'%s' AS CCG_BOOK_ID,'' AS CRATE,BIB_TEXT.BEGIN_PUB_DATE, BIB_TEXT.PLACE_CODE, BIB_TEXT.AUTHOR, 
		princetondb.GETBIBTAG(BIB_TEXT.BIB_ID, '240') as TAG_240,
		BIB_TEXT.TITLE_BRIEF as TAG_245,
		princetondb.GETBIBTAG(BIB_TEXT.BIB_ID, '260') as TAG_260,
		princetondb.GETBIBTAG(BIB_TEXT.BIB_ID, '300') as TAG_300,
		princetondb.GETALLBIBTAG(BIB_TEXT.BIB_ID, '5xx') as TAG_5XX,
		princetondb.GETALLBIBTAG(BIB_TEXT.BIB_ID, '6xx') as TAG_6XX,
		MFHD_MASTER.DISPLAY_CALL_NO, LOCATION.LOCATION_CODE,'' as complete_yn,'' as NOTES, '' as handling_instructions,'%s' as batchNo, '%s' as objectNo
		FROM 
		((((ITEM_BARCODE 
		INNER JOIN MFHD_ITEM ON ITEM_BARCODE.ITEM_ID = MFHD_ITEM.ITEM_ID) 
		INNER JOIN BIB_MFHD ON MFHD_ITEM.MFHD_ID = BIB_MFHD.MFHD_ID) 
		INNER JOIN BIB_TEXT ON BIB_MFHD.BIB_ID = BIB_TEXT.BIB_ID) INNER JOIN MFHD_MASTER ON MFHD_ITEM.MFHD_ID = MFHD_MASTER.MFHD_ID) 
		INNER JOIN LOCATION ON MFHD_MASTER.LOCATION_ID = LOCATION.LOCATION_ID
		WHERE (((ITEM_BARCODE.ITEM_BARCODE)='%s'))"""

	c = db.cursor()
	c.execute(sql % (ccg,bat.zfill(3),obj.zfill(3),bc))
	new_row = []
	for row in c:
		for x in row:
			if x is None: x = ""
			new_row.append(str(x))
		return new_row
	c.close()
        
if __name__ == "__main__":
	main()
