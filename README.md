Arabic Collections Online (ACO)
===============================
Code for our collaboration with NYU for digitizing Arabic books. 

See [http://dlib.nyu.edu/aco/](http://dlib.nyu.edu/aco/)

Thorough documentation is in our network share.

####jinn.py
This Python bottle app will retrieve any missing data and get MARCXML for the items in a given batch picklist. 

Generally...
* export batch from MS Access using the handy form (see screenshot below)
* go to the app's URL and follow the steps given there
* deliverables will be a single zip file to be moved to the designated batch folder on our share

If running locally on Linux (Ubuntu)... 
* `cp aco.cfg.template aco.cfg`
* fill in aco.cfg
* cd into the aco dir and run `python jinn.py`

#####Requires
* [bottle](http://bottlepy.org/docs/dev/index.html)
* [cx_Oracle](http://cx-oracle.sourceforge.net/) ([installation](https://gist.github.com/kimus/10012910) is a bit involved)
* [lxml](http://lxml.de/) `sudo apt-get install libxml2-dev libxslt1-dev python-dev`
* [xlsxwriter](https://xlsxwriter.readthedocs.org/)

####MS Access

Data for each batch is entered in an Access database. Batch picklists are generated and exported using a simple form:

![Simple Access form](https://raw.githubusercontent.com/pulcams/aco/master/accdb/aco_form.png)

The VBA for this is in ./accdb

####P.S.
Incomplete documentation and code for an initial phase of this project is currently still available here: [https://github.com/pulibrary/aco_planning](https://github.com/pulibrary/aco_planning)
