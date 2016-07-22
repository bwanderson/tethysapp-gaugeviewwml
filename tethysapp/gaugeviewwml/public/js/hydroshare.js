//Upload snow WaterML file to HydroShare. This file is based on the Snow Inspector app
var displayStatus = $('#display-status');
var resource_url
var USGS_type

$(function(){
  $("input[name='time_period']").click(function () { // listen for change - not click
    if( $(this).val() == 'preceding' ) { // use the "raw" DOM property `checked`
//      console.log('inside if');
      $("#time_selection").show();
    }
    else {
//    console.log('inside else');
      $("#time_selection").hide();
    }
  });
});


// AHPS Upload to HS Controls
$('#btnUploadflow').on('click', function () {

    gaugeno = $("#gaugeno").val();
    lat = $("#lat").val();
    long = $("#long").val();

    resTitle = 'AHPS flow information for site ' + gaugeno;
    resAbstr = 'This resource contains a WaterML generated by the Gaugeviewer WaterML application representing the observed and forecasted flow data for gauge number ' + gaugeno + ', which is located at lat: ' + lat + ' long: ' + long;
    resKwds ='Flow, AHPS';

    $("#resource-title").val(resTitle);
    $("#resource-abstract").val(resAbstr);
    $("#resource-keywords").val(resKwds);
    displayStatus.html('');
    resource_url = $("#AHPS_waterml_Flow-link").attr("href");
});

$('#btnUploadstage').on('click', function () {

    gaugeno = $("#gaugeno").val();
    lat = $("#lat").val();
    long = $("#long").val();

    resTitle = 'AHPS stage information for site ' + gaugeno;
    resAbstr = 'This resource contains a WaterML generated by the Gaugeviewer WaterML application representing the observed and forecasted stage data for gauge number ' + gaugeno + ', which is located at lat: ' + lat + ' long: ' + long;
    resKwds ='Stage, AHPS';

    $("#resource-title").val(resTitle);
    $("#resource-abstract").val(resAbstr);
    $("#resource-keywords").val(resKwds);
    displayStatus.html('');
    resource_url = $("#AHPS_waterml_Stage-link").attr("href");
    console.log(typeof resource_url)
});


// USGS Upload to HS Controls
$('#btnUploadinst').on('click', function () {

    gaugeno = $("#gaugeid").val();
    lat = $("#lat").val();
    long = $("#long").val();

    resTitle = 'USGS discharge information for site ' + gaugeno;
    resAbstr = 'This resource contains a WaterML retrieved from the USGS IV service by the Gaugeviewer WaterML application representing observed discharge data for gauge number ' + gaugeno + ', which is located at lat: ' + lat + ' long: ' + long;
    resKwds ='Discharge, USGS';
    USGS_type = 'inst';

    $("#resource-title").val(resTitle);
    $("#resource-abstract").val(resAbstr);
    $("#resource-keywords").val(resKwds);
    displayStatus.html('');
    resource_url = $("#USGS_waterml_inst-link").attr("href");
    displayed_inst_url = resource_url;
});

$('#btnUploaddv').on('click', function () {

    gaugeno = $("#gaugeid").val();
    lat = $("#lat").val();
    long = $("#long").val();

    resTitle = 'USGS discharge information for site ' + gaugeno;
    resAbstr = 'This resource contains a WaterML generated by the Gaugeviewer WaterML application representing the observed discharge data for gauge number ' + gaugeno + ', which is located at lat: ' + lat + ' long: ' + long;
    resKwds ='Discharge, USGS';
    USGS_type = 'dv';

    $("#resource-title").val(resTitle);
    $("#resource-abstract").val(resAbstr);
    $("#resource-keywords").val(resKwds);
    displayStatus.html('');
    resource_url = $("#USGS_waterml_dv-link").attr("href");
    displayed_dv_url = resource_url;
});


$('#hydroshare-proceed').on('click', function ()  {
    //This function only works on HTML5 browsers.
//    console.log('running hydroshare-proceed!!');

    if ($("#time_selection").length > 0) {
        if ($("input[name='time_period']:checked").val() == 'preceding') {
            period = $("input[name='period']").val();
            units = $('#time_period_units').val();
            span = period + '-' + units;
            if (USGS_type == 'inst') {
                resource_url = "/apps/gaugeviewwml/waterml/?type=usgsiv&gaugeid=" + gaugeno + "&span=" + span;
            }
            else {
                resource_url = "/apps/gaugeviewwml/waterml/?type=usgsdv&gaugeid=" + gaugeno + "&span=" + span + "&lat=" + lat + "&long=" + long;
            }
        }
        else if ($("input[name='time_period']:checked").val() == 'all') {
            if (USGS_type == 'inst') {
                resource_url = "/apps/gaugeviewwml/waterml/?type=usgsiv&gaugeid=" + gaugeno + "&span=all";
            }
            else {
                resource_url = "/apps/gaugeviewwml/waterml/?type=usgsdv&gaugeid=" + gaugeno + "&span=all&lat=" + lat + "&long=" + long;
            }
        }
        else {
            if (USGS_type == 'inst') {
                resource_url = displayed_inst_url;
            }
            else {
                resource_url = displayed_dv_url;
        }
    };
    };

    //now we construct the WaterML..
    var waterml_link = resource_url;
    var upload_link = '/apps/gaugeviewwml/upload-to-hydroshare/';

    displayStatus.removeClass('error');
    displayStatus.addClass('uploading');
    displayStatus.html('<em>Uploading...</em>');

    var resourceAbstract = $('#resource-abstract').val();
    var resourceTitle = $('#resource-title').val();
    var resourceKeywords = $('#resource-keywords').val() ? $('#resource-keywords').val() : "";
//    var resourceType = $('#resource-type').val();
//    var resourceType = 'RefTimeSeriesResource'
    var resourcePublic = $("#resource-public").prop("checked");

    if (!resourceTitle || !resourceKeywords || !resourceAbstract)
    {
        displayStatus.removeClass('uploading');
        displayStatus.addClass('error');
        displayStatus.html('<em>You must provide all metadata information.</em>');
        return
    }

    var csrf_token = getCookie('csrftoken');
    $(this).prop('disabled', true);
    $.ajax({
        type: 'POST',
        url: upload_link,
        headers:{'X-CSRFToken':csrf_token},
        dataType:'json',
        data: {'title':resourceTitle, 'abstract': resourceAbstract,
            'keyword': resourceKeywords, 'waterml_link': waterml_link, 'public': resourcePublic},
        success: function (data) {
//            debugger;
            $('#hydroshare-proceed').prop('disabled', false);
            if ('error' in data) {
                displayStatus.removeClass('uploading');
                displayStatus.addClass('error');
                displayStatus.html('<em>' + data.error + '</em>');
            }
            else
            {
                displayStatus.removeClass('uploading');
                displayStatus.addClass('success');
                displayStatus.html('<em>' + data.success + ' View in HydroShare <a href="https://www.hydroshare.org/resource/' + data.newResource +
                    '" target="_blank">HERE</a></em>');
            }
        },
        error: function (jqXHR, textStatus, errorThrown) {
//            alert("Error");
//            debugger;
            $('#hydroshare-proceed').prop('disabled', false);
//            console.log(jqXHR + '\n' + textStatus + '\n' + errorThrown);
            displayStatus.removeClass('uploading');
            displayStatus.addClass('error');
            displayStatus.html('<em>' + errorThrown + '</em>');
        }
    });
});

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