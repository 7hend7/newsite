//set date-select onClick
$(document).ready(function(){

    $("#button-date-select").on("click", function(){
                                     // var sdate = $("#date-nav").attr('value');  //by id
                                     // var selurl =  $('form[name="form-date-select"]').attr("action")  // by name
                                     var selurl = $("#form-date-select").attr('action');
                                     var sdate = $('input[name="date-nav"]').val();
                                     
                                     $("#form-date-select").attr('action', selurl+sdate);
                                     //alert(selurl + sdate);

                                 });

});