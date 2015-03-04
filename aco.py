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
import glob
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
picklist = args['picklist'] # this is the picklist as output from Access
localpicklist = 'local_'+picklist # this is the spreadsheet for local use
batchno = picklist.split('_')[3]

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
	generate_spreadsheet()
	get_v2m_mrx()
	print('-' * 25)
	format_xml(outdir)
	mv_batch_files()
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
	shutil.copyfile(share+'/for_peter/'+picklist, indir+picklist)

def make_new_csv(picklist):
	"Input is csv picklist. Create a copy with any missing fields filled in."
	try:
		os.remove(outdir+localpicklist)
	except OSError:
		pass
	
	with open(indir+picklist,'rb') as csvfile:
		reader = csv.reader(csvfile,delimiter=',', quotechar='"')
		firstline = reader.next() # skip header row
		with open(outdir+localpicklist,'ab+') as outfile:
				writer = csv.writer(outfile)
				row = ['LIB','SYS','Item','Volume','CHRON','CCG_BOOK_ID','Crate','Date','CP','Tag_100','Tag_240','Tag_245','Tag_260','Tag_300','Tag_5XX','Tag_6XX','Callno','LOC','COMPLETE Y/N','Notes','Handling instructions','batchNo','objectNo']
				writer.writerow(row) 
		for row in reader:
			barcode = row[2]
			ccg = row[5]
			crate = row[6]
			batchid = row[21]
			objid = row[22]
			ccgid = str(ccg + objid.zfill(6))

			# TODO: check all rows by default, or just ones with certain data missing (and generate ccg_book_id for output otherwise)
			# When books are added manually, the barcode will be filled in but there'll be no bibid...
			# if (bibid == '' and barcode != '') or (cron == '' and vol == ''):
			if (ccg != 'CCG_BOOK_ID'): # if not the first row
				row = get_missing_data(barcode,ccgid,batchid,objid,crate)
				
			# output spreadsheet for local reference
			with open(outdir+localpicklist,'ab+') as outfile: # this will be an enhanced copy of the picklist in ./in
				writer = csv.writer(outfile)
				writer.writerow(row)
    	
def get_v2m_mrx():
	"Get marcxml using v2m service, and strip out HLDG info."
	logging.info("get_v2m_mrx()")
	conn = httplib.HTTPConnection("diglib.princeton.edu")
	flag = ""
	filename = "aco_bibs"
	timestamp = time.strftime("%Y%m%d")
	
	with open(outdir+localpicklist,'rb') as csvfile:
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
					f024a.text = 'princeton_aco' + objid.zfill(6)
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
				bibs_gotten.append(bibid)
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
	
def get_missing_data(bc,ccg,bat,obj,crate):
	"""
	When a barcode has been manually added to the picklist, pull in the missing data.
	"""
	user = config.get('database', 'user')
	pw = config.get('database', 'pw')
	sid = config.get('database', 'sid')
	ip = config.get('database', 'ip')
	
	dsn_tns = cx_Oracle.makedsn(ip,1521,sid)
	db = cx_Oracle.connect(user,pw,dsn_tns)
	
	sql = """SELECT 'Princeton' as LIB, BIB_MFHD.BIB_ID, ITEM_BARCODE.ITEM_BARCODE, MFHD_ITEM.ITEM_ENUM, 
		MFHD_ITEM.CHRON,'%s' AS CCG_BOOK_ID,%s AS CRATE,BIB_TEXT.BEGIN_PUB_DATE, BIB_TEXT.PLACE_CODE, 
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
		'%s' as objectNo
		FROM 
		((((ITEM_BARCODE 
		INNER JOIN MFHD_ITEM ON ITEM_BARCODE.ITEM_ID = MFHD_ITEM.ITEM_ID) 
		INNER JOIN BIB_MFHD ON MFHD_ITEM.MFHD_ID = BIB_MFHD.MFHD_ID) 
		INNER JOIN BIB_TEXT ON BIB_MFHD.BIB_ID = BIB_TEXT.BIB_ID) INNER JOIN MFHD_MASTER ON MFHD_ITEM.MFHD_ID = MFHD_MASTER.MFHD_ID) 
		INNER JOIN LOCATION ON MFHD_MASTER.LOCATION_ID = LOCATION.LOCATION_ID
		WHERE (((ITEM_BARCODE.ITEM_BARCODE)='%s'))"""

	c = db.cursor()
	c.execute(sql % (ccg,crate,bat.zfill(3),obj.zfill(6),bc))
	new_row = []
	for row in c:
		for x in row:
			if x is None: x = ""
			new_row.append(str(x))
		return new_row
	c.close()

def mv_batch_files():
	dest = share+batchno
	if not os.path.isdir(dest):
		try:
			os.mkdir(dest,0775)
		except:
			etype,evalue,etraceback = sys.exc_info()
			print("problem creating batch dir on share. %s" % evalue)
	else:
		confirm = raw_input(dest + " already exists. Are you sure you want to overwrite its files? [Yn] ")
		if confirm in ['y','Y','yes']:
			pass
		else:
			sys.exit('Exiting now')

	if not glob.glob(r'./out/*.csv') or not glob.glob(r'./out/*.xml'):
		print("no files?")
		exit

	for f in glob.glob(r'./out/*'):
		try:
			shutil.copy(f,dest)
			print(f + " => " + dest)
		except OSError: # apparently caused by different filesystems / ownership?
			etype,evalue,etraceback = sys.exc_info()
			print("problem with moving files: %s" % evalue)
			pass
    
def generate_spreadsheet():
	"""
	Generate a spreadsheet for partners, with a few of the total fields
	"""
	try:
		os.remove(outdir+picklist)
	except OSError:
		pass
		
	with open(outdir+picklist,'ab+') as acooutfile:
		writer = csv.writer(acooutfile)
		row = ['LIB','SYS#','Item #','Volume #','CCG_BOOK_ID','Crate #','Date','CP','Tag_100','Tag_240','Tag_245','Tag_260','Tag_300','Tag_5XX','Tag_6XX','Call#','LOC','COMPLETE Y/N','Notes']
		writer.writerow(row)
		
	with open(outdir+localpicklist,'rb') as csvfile:
		reader = csv.reader(csvfile,delimiter=',', quotechar='"')
		firstline = reader.next() # skip header row
		for row in reader:
			lib = row[0]
			bibid = row[1]
			barcode = row[2]
			vol = row[3]
			cron = row[4]
			ccg = row[5]
			crate = row[6]
			date = row[7]
			cp = row[8]
			TAG_100 = row[9]
			TAG_240 = row[10]
			TAG_245 = row[11]
			TAG_260 = row[12]
			TAG_300 = row[13]
			TAG_5XX = row[14]
			TAG_6XX = row[15]
			callno = row[16]
			LOC = row[17]
			compl = row[18]
			notes = row[19]

			# output spreadsheet for ACO
			with open(outdir+picklist,'ab+') as acooutfile:
				writer = csv.writer(acooutfile)
				row = [lib,bibid,barcode,vol,ccg,crate,date,cp,TAG_100,TAG_240,TAG_245,TAG_260,TAG_300,TAG_5XX,TAG_6XX,callno,LOC,compl,notes]
				writer.writerow(row)
        
if __name__ == "__main__":
	main()
