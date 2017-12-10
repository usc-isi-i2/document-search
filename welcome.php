<?php
  include("session.php");
  
  ini_set("display_errors", 0);
  
?>
<html>
   <head>
      <title>Welcome <?php echo $_SESSION['login_user']; ?></title>
			<style>
			table {border-collapse:collapse; table-layout:fixed; width:1000px;}
			table td { word-wrap:break-word; float:left; padding-right:30px;}
			table th {text-align:left; }
			</style>
   </head>
   
   <body>
      <h3>Welcome <?php echo $_SESSION['login_user']; ?></h3> 
	  <div align = "center">
         <div style = "width:1000px; border: solid 1px #333333; " align = "left">
            <div style = "background-color:#333333; color:#FFFFFF; padding:3px;"><b>Please find below the files found on the web:-</b></div>
				
            <div style = "margin:30px">
               
               <form action = "" method = "post">
<script>
	function Inc(id,fi,mi){
			var xmlhttp = new XMLHttpRequest();
			xmlhttp.onreadystatechange = function() {
				if (xmlhttp.readyState == 4 && xmlhttp.status == 200) {
					var htmldata = xmlhttp.responseText;
					htmldata = htmldata.replace(/\\/gi , "");
					var stringIndex = htmldata.substring(htmldata.lastIndexOf("start") +5 ,htmldata.lastIndexOf("end"));
					var divtagNumbers = stringIndex.split("Begin");
					for (i = 1; i < divtagNumbers.length; i++) {
							console.log(divtagNumbers[i]);
							console.log(divtagNumbers[i].split(" === ")[0]);
							document.getElementById(divtagNumbers[i].split(" === ")[0]).innerHTML = divtagNumbers[i].split(" === ")[1];
					}
				}	
			};
			xmlhttp.open("GET","welcome.php?q="+fi+"&h="+id+"&f="+mi,true);
			xmlhttp.send();
	}	
</script>
<?php
$q = $_REQUEST["q"];
$h = $_REQUEST["h"];
$p = $_REQUEST["f"];

if($q == null){
$sql = "SELECT DISTINCT filename, search_date FROM FileSearch ORDER BY search_date DESC";
$result = mysqli_query($mysqli,$sql);

if ($result->num_rows > 0) {
    // output data of each row
    while($row = $result->fetch_assoc()) {
				echo "<div id='". $row['filename'] ." ". $row['search_date'] ."'>";
        echo "<table><th align=\"left\">File: \"". $row['filename'] ."\" ran on \"". $row['search_date'] ."\"</th><br />";
        $sql1 = "SELECT search_result FROM FileSearch WHERE search_status = 'wait' and filename = '". $row['filename'] ."' and search_date = '". $row['search_date'] ."'";
        $result1 = mysqli_query($mysqli,$sql1);
        while($row1 = $result1->fetch_assoc()) {
            echo "<tr><td width=\"700\"><a href=\"" . $row1['search_result'] . "\">". $row1['search_result']  ."</a></td><td><input type=\"button\" value=\"Ignore\" onclick=\"Inc( '". $row1['search_result'] . "' , '". $row['filename'] . "' , 'ignore' )\"/> </td><td><input type=\"button\" value=\"Resolved\" onclick=\"Inc( '". $row1['search_result'] . "' , '". $row['filename'] . "' , 'resolved' )\"/> </td></tr>";
        }
				echo "</table>";
				echo "</div><br /><br />";
    }
}
}else {
	echo add($q,$h,$p);								
	echo refresh($q);						
}

function refresh($file){
	global $mysqli;
	$sql3 = "SELECT DISTINCT filename, search_date FROM FileSearch WHERE filename = '$file' ORDER BY search_date DESC";
  $result3 = mysqli_query($mysqli ,$sql3);
	
	if ($result3->num_rows > 0) {
    // output data of each row
    $data="start";
    while ($row3 = $result3->fetch_assoc()) {
				$data = $data . "Begin";
				$data = $data  . $row3['filename'] ." ". $row3['search_date'] ." === ";
        $data = $data  . "<table><th align=\"left\">File: \"". $row3['filename'] ."\" ran on \"". $row3['search_date'] ."\"</th><br />";
        $sql4 = "SELECT search_result FROM FileSearch WHERE search_status = 'wait' and filename = '". $row3['filename'] ."' and search_date = '". $row3['search_date'] ."'";
        $result4 = mysqli_query($mysqli ,$sql4);
        while($row4 = $result4->fetch_assoc()) {
            $data = $data  . "<tr><td width=\"700\"><a href=\"" . $row4['search_result'] . "\">". $row4['search_result']  ."</a></td><td><input type=\"button\" value=\"Ignore\" onclick=\"Inc( '". $row4['search_result'] . "' , '". $row3['filename'] . "' , 'ignore' )\"/> </td><td><input type=\"button\" value=\"Resolved\" onclick=\"Inc( '". $row4['search_result'] . "' , '". $row3['filename'] . "' , 'resolved' )\"/> </td></tr>";
     }
    $data = $data  . "</table>";
	}				
	}
	return json_encode($data."end");
}
  
function add($file,$link,$status) {
	echo "in add";
	global $mysqli;
	$sql2 = "UPDATE FileSearch SET search_status = '$status' where  filename ='$file' and search_result = '$link'";
	if(mysqli_query($mysqli ,$sql2)){
		return json_encode($sql2);
	}
	return json_encode($sql2);							
}

?>

               </form>
               
					
            </div>
				
         </div>
			
      </div>
   </body>
   
</html>
