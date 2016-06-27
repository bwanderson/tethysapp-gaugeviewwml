$(function() { //wait for page to load
    $('#comid_time').parent().addClass('hidden');

//inputs on usgs menu appear/disappear for analysis & assimilation, short, and mediumm
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