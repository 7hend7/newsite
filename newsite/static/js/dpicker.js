//set datepicker localization
$(function(){
    //$( "#date" ).datepicker( "option", $.datepicker.regional["ru"]);
    //$( "#date-nav" ).datepicker( $.datepicker.regional[ "ru" ] );
    //$.datepicker.setDefaults($.datepicker.regional['ru']);
    $( "#date-nav" ).datepicker({
                    dateFormat: "dd/mm/yy", // "yy-mm-dd", 
                    onSelect: function(dateText, inst){
                                  var date = new Date(dateText);
                                  //var month = date.getMonth();
                                  //var date = date.getDate();
                                  //var year = date.getFullYear();
				  //var selurl = $("#form-date-select").attr('action');
				  //var sdate = $('input[name="date-nav"]').val();
				  //$("#form-date-select").attr('action', selurl+sdate);
				  $("#form-date-select").submit();
                              }
                  });
    //if($('input[name="date-nav"]').val() == '')              
        $("#date-nav" ).datepicker("setDate", new Date());
});


