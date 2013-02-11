  $('#info-button').click(function() {
    $.ajaxSetup({ 
      beforeSend: function(xhr, settings) {
        function getCookie(name) {
          var cookieValue = null;
          if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
              var cookie = jQuery.trim(cookies[i]);
              // Does this cookie string begin with the name we want?
              if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
              }
            }
          }
          return cookieValue;
        }
        if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
          // Only send the token to relative URLs i.e. locally.
          xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
        }
      } 
    });
  
    var formData = $('#info-form').serialize();
    $.ajax ({
      url: '../info_submit/', 
      type: 'POST',
      data: formData,
      dataType: 'json',
      error: function(xhr, status, exception) {
        console.log(xhr);
        console.log(status);
        console.log(exception);
        alert('whoops! something went wrong');
      },
      success: function(data, status, xhr) {
        if (data['form_valid'] == true) {
          toTab('safety');
        } else if (data['form_valid'] == false) {
          $('#info-form').html(data['new_form']);
          console.log('replaced shit');
        } else {
          alert('alex is dumb');
        }
      },
    });
  });

  function toTab(id) {
    $('#secondnav .active').removeClass('active');
    $('.tab-content .active').removeClass('active');
    $('#tab-'+id).removeClass('disabled');
    $('#tab-'+id + ' a').attr("href", "#"+id);
    $('#'+id).addClass('active');
    $('a[href="#'+id+'"]').parent().addClass('active');
  };
  
  $('button#info-form').click(function(){
    toTab('safety');
  });
  
  $('button#safety-form').click(function(){
    toTab('waiver');
  });
  
  $('button#waiver-form').click(function(){
    toTab('pay');
    var pcnum = $("#id_penncard").val();
    console.log(pcnum);

    $.ajaxSetup({ 
      beforeSend: function(xhr, settings) {
        function getCookie(name) {
          var cookieValue = null;
          if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
              var cookie = jQuery.trim(cookies[i]);
              // Does this cookie string begin with the name we want?
              if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
              }
            }
          }
          return cookieValue;
        }
        if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
          // Only send the token to relative URLs i.e. locally.
          xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
        }
      } 
    });

    var payInfo = {'pennid': pcnum};
    var pennidData = $.param(payInfo);
    console.log(payInfo);
    console.log(pennidData);
    $.ajax ({
      url: '../verify_waiver/', 
      type: 'POST',
      data: payInfo,
      dataType: 'json',
      error: function(xhr, status, exception) {
        console.log(xhr);
        console.log(status);
        console.log(exception);
        alert('waiver failed');
      },
      success: function(data, status, xhr) {
        console.log('waiver success');
      },
    });


    var living_location = $("#id_living_location").val();
    console.log(living_location);
    if(living_location == "Stouffer") {
      $('div#pay').replaceWith('<h2>You\'ve already paid. Thanks!</h2>'); 
      console.log("replaced html");
    } else {
      $("#penncardnum-id").val(pcnum);

      var plan = null;

      $("form#planform select option:selected").each(function () {
        plan = $(this);
        console.log("selected plan: " + plan.text());
        $.extend(payInfo, {'plan': plan.attr("name")});
        console.log(payInfo);
        console.log("done logging payinfo");
      });
      console.log("exited loop");

      $.ajax ({
        url: '/addpayment/',
        type: 'POST',
        data: payInfo,
        //dataType: 'json',
        error: function(xhr, status, exception) {
          console.log(xhr);
          console.log(status);
          console.log(exception);
          alert('making payment failed');
        },
        success: function(data, status, xhr) {
          console.log('payment creation success');
        },
      });

      console.log("ajax call made");
      /*if(amt == 0) {
        alert("whoops! price processing went wrong.");
        return;
      }
      */

      $("#amount-id").val(10);

      $('#paybycredit').click(function(){
        $('#payform').submit();
      });
      
      function appendPcnum (id, pcnum) {
        var _href = $(id).attr('href');
        $(id).attr('href', _href + pcnum);
        console.log('appended');
      }
      
      appendPcnum('#paybycash', pcnum);
      appendPcnum('#paybypenncash', pcnum);
      appendPcnum('#paybybursar', pcnum);
      // Might not be necessary
      appendPcnum("#fisher", pcnum);
      appendPcnum("#ware", pcnum);
    }
  }); 

  // set background for active tab in navbar    
  $('.nav1 li#signup').addClass('active');