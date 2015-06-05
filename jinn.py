from __future__ import unicode_literals
from bottle import * #Bottle, request, response, static_file
import aco
import os


# http://www.reddit.com/r/learnpython/comments/1037g5/whats_the_best_lightweight_web_framework_for/
# http://bottlepy.org/docs/dev/tutorial.html

app = Bottle()

def jinn(picklist):
	return aco.main(picklist)

@app.route('/static/<filename>')
def fileget(filename):
	return static_file(filename, root='./static/')

@app.route('/help')
def help():
	return template('views/help')

@app.get('/')
def home():
	return template('views/index')

@app.post('/')
def upload():
	# A file-like object open for reading...
	upload_file = request.files.get('fileupload')
	converted_file = jinn(picklist=upload_file)
	filename = upload_file.filename.replace('.csv','')+'.zip;'
	response.set_header(str('Content-Type'), str('application/zip'))
	response.set_header(str('Content-Disposition'), str('attachment; filename='+filename))
	# Return a file-like object...
	return converted_file
    
if __name__ == "__main__":
	app.run(host="0.0.0.0", port=8083, debug=True)
