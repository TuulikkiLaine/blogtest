 $(document).ready(function(){
 
 $('.navi_month').click(function(e)
	{
	$(this).children().slideToggle();
	});

var windowheight = $(window).height();
	
 $('.pusher').css('min-height',windowheight-373-57);  /*footerfix*/
 
 $('#add_new_entry').click(function(e)
	{
	$('#post_entry_form').slideToggle();
	});
 
  $('.edit').click(function(e)
	{
	$(this).parent().children('.edit_entry_form').slideToggle();
	});
  
 $('.open_delete').click(function(e)
	{
	 $(this).parent().children('.are_you_sure').show();
	});
 
 $('.close_delete').click(function(e)
	{
	 $('.are_you_sure').hide();
	});
  
 });