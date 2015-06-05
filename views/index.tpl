<!DOCTYPE HTML>
<html>
<head>
<title>ACO jinn</title>
<script src="http://ajax.googleapis.com/ajax/libs/jquery/1.11.2/jquery.min.js"></script>
<link href="/jinn/static/bootstrap.min.css" rel="stylesheet">
<link href='http://fonts.googleapis.com/css?family=Lobster' rel='stylesheet' type='text/css'>
<script>
$(document).ready(function(){    
  $(function() {
      
  // enable button only after file has been chosen
     $("input:file").change(function (){
       $("#zip").removeClass("btn-disabled").addClass("btn-primary");
       $("#zip").prop('disabled', false);
     });
  });
  
  // provide feedback after button's been clicked
  $("#zip").click(function(){
    var filename = $("#fileupload").val().replace(/\\/g, '/').replace(/.*\//, '').replace(/.csv/,'.zip');
    var batchno = $("#fileupload").val().split(/[_]+/);
    $("#zip").removeClass("btn-primary").addClass("btn-success");
    $("#chosen_file").text(filename);
    $("#batch_dir").text(batchno[batchno.length - 2]);
   });
  
 });   
</script>
<style>
h1 {
    font-family: 'Lobster', cursive;
}
.btn-file {
    position: relative;
    overflow: hidden;
    margin-top: 10px;
}
.btn-file input[type=file] {
    position: absolute;
    top: 0;
    right: 0;
    min-width: 100%;
    min-height: 100%;
    text-align: right;
    filter: alpha(opacity=0);
    opacity: 0;
    outline: none;
    cursor: inherit;
    display: block;
}
.info {
    color: #339933;
    font-weight: bold;
}
</style>
</head>
<body>
<script type="text/javascript" src="/jinn/static/bootstrap.min.js"></script>
<div class="container">
<h1>ACO jinn</h1>
<h5>ACO picklist generator (<a href='/jinn/help'>?</a>)</h5>
<form id="getxlsx" method="POST" enctype="multipart/form-data" action="/jinn">
<ol>
<li>
<span class="btn btn-default btn-file">
    Browse for CSV... <input id="fileupload" name="fileupload" type="file">
</span><br /><br />
</li>
<li>
<input id="zip" type="submit" name="zip_btn" class="btn btn-lg btn-disabled" value="do magic!" disabled='true'/><br /><br />
</li>
<li>Move the downloaded file <span id="chosen_file" class="info"></span> to the batch folder <span id="batch_dir" class="info"></span></li>
<ol>
</form>
</div>
<div class="modal"></div>
</body>
</html>
