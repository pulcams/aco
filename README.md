Arabic Collections Online (ACO)
===============================
Code for our collaboration with NYU for digitizing Arabic books. 

See [http://dlib.nyu.edu/aco/](http://dlib.nyu.edu/aco/)

Thorough documentation is in our network share.

This Python script (aco.py) will retrieve any missing data and get MARCXML for the items in a given batch picklist. On Linux (Ubuntu)... 
* `cp aco.cfg.template aco.cfg`
* fill in aco.cfg
* export batch from MS Access using the handy form (see image below)
* run `python aco.py -f ` plus the name of the batch picklist. Example:

 `python aco.py -f ACO_princeton_NYU_batch001_20150227.csv`
* Deliverables will be in ./out and then moved to the designated folder on the share (`export` in the cfg file)

####Requires
* [cx_Oracle](http://cx-oracle.sourceforge.net/) ([installation](https://gist.github.com/kimus/10012910) is a bit involved)
* [lxml](http://lxml.de/) `sudo apt-get install libxml2-dev libxslt1-dev python-dev`
* [xlsxwriter](https://xlsxwriter.readthedocs.org/)

####MS Access

Data is entered in an Access database. Batch picklists are generated and exported using a simple form:

![Simple Access form](https://raw.githubusercontent.com/pulcams/aco/master/accdb/aco_form.png)

The VBA for this is in ./accdb

####P.S.
Incomplete documentation and code for an initial phase of this project is currently still available here: [https://github.com/pulibrary/aco_planning](https://github.com/pulibrary/aco_planning)
