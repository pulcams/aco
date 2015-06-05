<!DOCTYPE HTML>
<html>
<head>
<title>ACO jinn</title>
<script src="http://ajax.googleapis.com/ajax/libs/jquery/1.11.2/jquery.min.js"></script>
<link href="/jinn/static/bootstrap.min.css" rel="stylesheet">
<link href='http://fonts.googleapis.com/css?family=Lobster' rel='stylesheet' type='text/css'>
<style>
h1 {
    font-family: 'Lobster', cursive;
}
img {
    border: 1px solid #ccc;
}
</style>
</head>
<body>
<script type="text/javascript" src="/jinn/static/bootstrap.min.js"></script>
<div class="container">
<h1>ACO jinn</h1>
<h5>ACO picklist generator</h5>
<ul>
<li>In the Access database (NYU_Arabic_Project.mdb): After all the data for a batch has been entered into "PickList NEW", open the make_batch_lists form and click "make batch table" and then "export batch table" <p><img src="/jinn/static/aco_form.png" alt="access form"/></p></li>
<li>With ACO Geany (this web app), browse for the csv file that you just exported.  It will be in \\lib-tsserver\NYU_Arabic_Project\batches\exports</li> (The download button will be clickable *after* you choose the csv file.)
<li>Click the "do magic!" download buttons to get a zip file (this might take a few seconds). The zip file will include the formatted MARCXML records and two picklists, one for us and one for NYU.</li>
<li>Copy the zipfile from the Downloads folder on your workstation to the appropriate batches folder, as given in step 3. For example "batch003" will be at \\lib-tsserver\NYU_Arabic_Project\batches\batch003</li>
<li>Take a break</li>
</ul>
<p>P.S. There's more documentation in \\lib-tsserver\NYU_Arabic_Project\docs</p>
<p>(<a href="/jinn">go back</a>)</p>
</div>
</body>
</html>
