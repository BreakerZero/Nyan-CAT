 setInputFilter(document.getElementById("sectionnumber"), function(value) {return /^\d*$/.test(value);});
    function upsectionnumber(){
        document.getElementById("sectionnumber").value = parseInt(document.getElementById("sectionnumber").value ) + 1;
        getRessourceProject(document.getElementById('sectionnumber').value);
    }
    function downsectionnumber(){
        if (document.getElementById("sectionnumber").value != "0")
        document.getElementById("sectionnumber").value = parseInt(document.getElementById("sectionnumber").value ) - 1;
        getRessourceProject(document.getElementById('sectionnumber').value);
    }