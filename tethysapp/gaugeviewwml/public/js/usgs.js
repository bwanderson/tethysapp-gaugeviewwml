//This function is ran to set a listener to update the plot size when the navigation pane is opened or closed
(function () {
    var target, observer, config;
    // select the target node
    target = $('#app-content-wrapper')[0];

    observer = new MutationObserver(function () {
        window.setTimeout(function () {
            $('.highcharts-plot').highcharts().reflow();
        }, 350);
    });

    config = {attributes: true};

    observer.observe(target, config);
}());


$(function() { //wait for page to load
    $('#comid_time').parent().addClass('hidden');
    if ($('#forecast_range').val() === 'medium_range') {
        $('#comid_time').parent().addClass('hidden');
        $('#forecast_date_end').parent().addClass('hidden');
    } else if ($('#forecast_range').val() === 'short_range') {
        $('#comid_time').parent().removeClass('hidden');
        $('#forecast_date_end').parent().addClass('hidden');
    } else if ($('#forecast_range').val() === 'analysis_assim'){
        $('#comid_time').parent().addClass('hidden');
        $('#forecast_date_end').parent().removeClass('hidden');
    }

//inputs on usgs menu appear/disappear for analysis & assimilation, short, and medium
    $('#forecast_range').on('change', function () {
        if ($('#forecast_range').val() === 'medium_range') {
            $('#comid_time').parent().addClass('hidden');
            $('#forecast_date_end').parent().addClass('hidden');
        } else if ($('#forecast_range').val() === 'short_range') {
            $('#comid_time').parent().removeClass('hidden');
            $('#forecast_date_end').parent().addClass('hidden');
        } else if ($('#forecast_range').val() === 'analysis_assim'){
            $('#comid_time').parent().addClass('hidden');
            $('#forecast_date_end').parent().removeClass('hidden');
        }
    });
});

$(document).ready(function(){
  //document.getElementsByName('generate_graphs')[0].prop("disabled",false);
  var start_date = new Date($('#date_start').val());
  $('#date_end').datepicker('setStartDate',start_date);

  var end_date = new Date($('#date_end').val());
  $('#date_start').datepicker('setEndDate',end_date);

  $('#date_start').datepicker().on('changeDate', function(selected) {
        // Revalidate the start date field
        var startDate = new Date(selected.date.valueOf());
        var endDate = new Date($('#date_end').val());
        $('#date_end').datepicker('setStartDate',startDate);
        if(startDate > endDate){
          alert("Please check your dates. You start date cannot be after the end and the end date cannot be before your start date.");
        };

    }).on('clearDate',function(selected){$('#date_end').datepicker('setStartDate',null);
  });

  $('#date_end').datepicker().on('changeDate', function(selected) {
        // Revalidate the start date field
        var startDate = new Date($('#date_start').val());
        var endDate = new Date(selected.date.valueOf());
        $('#date_start').datepicker('setEndDate',endDate);
        if(startDate > endDate){
          alert("Please check your dates. You start date cannot be after the end and the end date cannot be before your start date.");
        };
    }).on('clearDate',function(selected){$('#date_start').datepicker('setEndDate',null);
  });

    //Forecast date
  $('#forecast_date').datepicker().on('changeDate', function(selected) {
        // Revalidate the start date field
        var startDate = new Date(selected.date.valueOf());
        var endDate = new Date($('#forecast_date_end').val());
        $('#forecast_date_end').datepicker('setStartDate',startDate);
        if(startDate > endDate){
          alert("Please check your dates. You start date cannot be after the end and the end date cannot be before your start date.");
        };
    });
  $('#forecast_date_end').datepicker().on('changeDate', function(selected) {
        // Revalidate the start date field
        var startDate = new Date($('#forecast_date').val());
        var endDate = new Date(selected.date.valueOf());
        $('#forecast_date').datepicker('setEndDate',endDate);
        if(startDate > endDate){
          alert("Please check your dates. You start date cannot be after the end and the end date cannot be before your start date.");
        };
    });
});