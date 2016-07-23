from django.shortcuts import render, render_to_response
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from datetime import datetime, timedelta
import urllib2
from tethys_sdk.gizmos import TimeSeries
import xml.etree.ElementTree as ElTree
from tethys_sdk.gizmos import DatePicker
from tethys_sdk.gizmos import Button
from tethys_sdk.gizmos import TextInput
from tethys_sdk.gizmos import SelectInput
import os
import shutil
import json
import urllib
import tempfile
import traceback
from django.http import JsonResponse
from hs_restclient import HydroShare, HydroShareAuthBasic
from oauthlib.oauth2 import TokenExpiredError
from hs_restclient import HydroShare, HydroShareAuthOAuth2, HydroShareNotAuthorized, HydroShareNotFound
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

hs_hostname = "www.hydroshare.org"

@login_required()
def home(request):
    """
    This is the controller for the app homepage
    :param request: This is the request from the URL map in app.py
    :return: This will render the html page
    """
    context = {}

    return render(request, 'gaugeviewwml/home.html', context)


def get_usgs_iv_data(gauge_id, start, end):
    """
    :param gauge_id: This is the USGS Id of the gauge
    :param start: This is the properly formatted beginning date YYYY-MM-DD
    :param end: This is the properly formatted end date YYYY-MM-DD
    :return: This returns a USGS rdb file of streamflow in cfs for the selected gauge and time
    """
    url = ('http://nwis.waterdata.usgs.gov/usa/nwis/uv/?cb_00060=on&format=rdb&site_no={0}'
           '&period=&begin_date={1}&end_date={2}'.format(gauge_id, start, end))
    response = urllib2.urlopen(url)
    data = response.read()
    return data


def get_usgs_dv_data(gauge_id, start, end):
    """
    :param gauge_id: This is the USGS Id of the gauge
    :param start: This is the properly formatted beginning date YYYY-MM-DD
    :param end: This is the properly formatted end date YYYY-MM-DD
    :return: This returns a USGS rdb file of streamflow in cfs for the selected gauge and time
    """
    url = ('http://nwis.waterdata.usgs.gov/usa/nwis/dv/?cb_00060=on&format=rdb&site_no={0}'
           '&period=&begin_date={1}&end_date={2}'.format(gauge_id, start, end))
    response = urllib2.urlopen(url)
    data = response.read()
    return data


def get_usgs_xml(gauge_id, start, end):
    """
    The URL generated here is described at: http://waterservices.usgs.gov/rest/IV-Test-Tool.html and can be edited
    for a WML 2.0 format, as well as others.
    :param gauge_id: This is the USGS Id of the gauge
    :param start: This is the properly formatted beginning date YYYY-MM-DD
    :param end: This is the properly formatted end date YYYY-MM-DD
    :return: This returns a USGS rdb file of streamflow in cfs for the selected gauge and time
    """
    url = ('http://nwis.waterservices.usgs.gov/nwis/iv/?format=waterml,1.1&sites={0}&startDT={1}&endDT={2}&'
           'parameterCd=00060'.format(gauge_id, start, end))
    response = urllib2.urlopen(url)
    data = response.read()
    return data


def get_ahps_data(gaugeno):
    """
    :param gaugeno: This is the AHPS Gauge Number that was selected
    :return: This returns an .xml file with the required gauge information, streamflow and stage, as applicable
    """
    url = 'http://water.weather.gov/ahps2/hydrograph_to_xml.php?gage={0}&output=xml'.format(gaugeno.lower())
    response = urllib2.urlopen(url)
    data = response.read()
    return data


def convert_to_utc(time, tz):
    """
    :param time: this is a python datetime object
    :param tz: this is the stated timezone for the object
    :return: This will return the UTC (GMT) time of the observation, and the numerical time offset
    """
    tz = tz.upper()

    if tz == "EGST" or tz == "GMT":
        time_change = timedelta(hours=0)
    elif tz == "EGT":
        time_change = timedelta(hours=1)
    elif tz == "PMDT" or tz == "WGST":
        time_change = timedelta(hours=2)
    elif tz == "NDT" or tz == "HAT":
        time_change = timedelta(hours=2.5)
    elif tz == "ADT" or tz == "HAA" or tz == "PMST" or tz == "WGT" or tz == "AT":
        time_change = timedelta(hours=3)
    elif tz == "NST" or tz == "HNT":
        time_change = timedelta(hours=3.5)
    elif tz == "AST" or tz == "HNA" or tz == "EDT" or tz == "HAE" or tz == "ET":
        time_change = timedelta(hours=4)
    elif tz == "CDT" or tz == "EST" or tz == "CT" or tz == "HAC" or tz == "HNE":
        time_change = timedelta(hours=5)
    elif tz == "CST" or tz == "MDT" or tz == "MT" or tz == "HNC" or tz == "HAR":
        time_change = timedelta(hours=6)
    elif tz == "MST" or tz == "PDT" or tz == "PT" or tz == "HNR" or tz == "HAP":
        time_change = timedelta(hours=7)
    elif tz == "AKDT" or tz == "PST" or tz == "HNP":
        time_change = timedelta(hours=8)
    elif tz == "AKST" or tz == "HADT":
        time_change = timedelta(hours=9)
    elif tz == "HAST":
        time_change = timedelta(hours=10)
    else:
        time_change = timedelta(hours=0)

    utc_time = time + time_change
    time_offset = 0 - time_change.seconds / (60 * 60)
    return utc_time, time_offset


def check_digit(num):
    """
    Check digits in month and day (i.e. 2016-05-09, not 2016-5-9)
    :param num: input of number that is supposed to be two digits long
    :return: returns a number that is two digits long
    """
    num_str = str(num)
    if len(num_str) < 2:
        num_str = '0' + num_str
    return num_str


def convert_usgs_iv_to_python(data):
    """
    This will convert the entire USGS instantaneous file to a python object
    :param data: USGS rdb data file
    :return:
    """
    python_data_list = []
    metadata = []
    python_metadata = []
    contact = None
    retrieval_date = None
    for line in data.splitlines():
        if line.startswith("#"):
            metadata.append(line)
        if line.startswith("USGS"):
            data_array = line.split('\t')
            agency_code = data_array[0]
            site_code = data_array[1]
            time_str = data_array[2]
            time_zone = data_array[3]
            value_str = data_array[4]
            value_code = data_array[5]

            time_str = time_str.replace(" ", "-")
            time_str_array = time_str.split("-")
            year = int(time_str_array[0])
            month = int(time_str_array[1])
            day = int(time_str_array[2])
            hour, minute = time_str_array[3].split(":")
            hour_int = int(hour)
            minute_int = int(minute)
            time = datetime(year, month, day, hour_int, minute_int)
            utctime, time_offset = convert_to_utc(time, time_zone)

            if value_str == "Ice":
                value_str = "0"

            if value_str == '':
                continue

            python_data_list.append([agency_code, site_code, time, time_offset, utctime, float(value_str), value_code])

    for i in metadata:
        i = i[1:].strip()
        if 'Contact:' in i:
            contact = i[9:].strip()
            continue
        if 'retrieved:' in i:
            retrieval_date = i[10:35].strip()
            continue
    python_metadata.append({'Contact': contact, 'Retrieved': retrieval_date})

    return python_metadata, python_data_list


def convert_usgs_dv_to_python(data):
    """
    This will convert the entire USGS instantaneous file to a python object
    :param data: USGS rdb data file
    :return:
    """
    python_data_list = []
    metadata = []
    data_list = []
    contact = None
    retrieval_date = None
    site_name = ""
    for line in data.splitlines():
        if line.startswith("#"):
            metadata.append(line)
        if line.startswith("USGS"):
            data_list.append(line)

    for line in data_list:
        data_array = line.split('\t')
        agency_code = data_array[0]
        site_code = data_array[1]
        time_str = data_array[2]
        value_str = data_array[3]
        value_code = data_array[4]

        time_str_array = time_str.split("-")
        year = int(time_str_array[0])
        month = int(time_str_array[1])
        day = int(time_str_array[2])
        date = datetime(year, month, day)

        if value_str == "Ice":
            value_str = "-9999"
        if value_str == "":
            value_str = "-9999"

        python_data_list.append([agency_code, site_code, date, float(value_str), value_code])

    for i in metadata:
        # print i
        i = i[1:].strip()
        # print i
        if 'Contact:' in i:
            contact = i[9:].strip()
            continue
        if 'retrieved:' in i:
            retrieval_date = i[10:35].strip()
            continue
        if i.startswith("USGS "):
            site_name = i[14:]
            continue

    python_metadata = {'Contact': contact, 'Retrieved': retrieval_date, 'SiteName': site_name}

    return python_metadata, python_data_list


def convert_ahps_to_python(data):
    """
    :param data: Input the XML file returned from the AHPS website
    :return: return a Python list object with time-series data from the XML returned. The python list returned will be
    formatted as: [(observed or forecast), datetime, stage, stage units, flow, flow_units]
    """
    site = ElTree.fromstring(data)
    python_data = []
    # These variables are defined now to account for when one of them is not present in AHPS data.
    stage = 0
    stage_units = ''
    flow = 0
    flow_units = ''

    for child in site:
        if child.tag == "observed" or child.tag == "forecast":
            for datum in child:
                for field in datum:
                    if field.get('timezone') == "UTC":
                        time = field.text
                        time1 = time.replace("T", "-")
                        time_split = time1.split("-")
                        year = int(time_split[0])
                        month = int(time_split[1])
                        day = int(time_split[2])
                        hour_minute = time_split[3].split(":")
                        hour = int(hour_minute[0])
                        minute = int(hour_minute[1])
                    elif field.get('name') == "Stage":
                        stage = float(field.text)
                        stage_units = field.get('units')
                    elif field.get('name') == "Flow":
                        if field.get('units') == "kcfs":
                            flow = float(field.text) * 1000
                            flow_units = 'cfs'
                            # total += flow
                        elif field.get('units') == "cfs":
                            flow = float(field.text)
                            flow_units = 'cfs'
                            # total += flow
                        else:
                            flow = float(field.text)
                            flow_units = field.get('units')
                python_data.append([child.tag, datetime(year, month, day, hour, minute), stage, stage_units, flow,
                                    flow_units])

        # Input XML requires sorting by date to get in proper order
        python_data.sort(key=lambda x: x[1])

    return python_data


def format_ahps_ts(time_series, time_offset, var_code):
    """
    :param time_series: This is a python time series created with convert_ahps_to_python(data) function
    :param time_offset: This is an integer of the timezone offset
    :param var_code: this is an integer representing whether Flow or Stage has been requested
    :return: This returns a list of lists formatted as [localtime, time_offset, UTCtime, (observed or forecast), Value],
                and units
    """

    formatted_ts = []
    units = ""
    for item in time_series:
        time_change = timedelta(hours=time_offset)
        localtime = item[1] + time_change
        localtime = localtime.strftime("%Y-%m-%dT%H:%M")
        item[1] = item[1].strftime("%Y-%m-%dT%H:%M")
        if item[0] == 'observed':
            quality_code = 1
        elif item[0] == 'forecast':
            quality_code = 3
        if var_code == 0:  # FLOW
            formatted_ts.append([localtime, time_offset, item[1], item[0], item[4], quality_code])
            units = item[5]
        elif var_code == 1:  # STAGE
            formatted_ts.append([localtime, time_offset, item[1], item[0], item[2], quality_code])
            units = item[3]

    return formatted_ts, units


def create_time_series_usgs(data, values='iv'):
    """
    :param data: Python Data list of USGS NWIS stream gauge observations
    :param values: Is
    :return: Time series list of all datetime and values for highcharts plotting
    """
    time_series_list = []
    if values == 'iv':
        for i in data:
            time_series_list.append([i[4], i[5]])
    elif values == 'dv':
        for i in data:
            time_series_list.append([i[4], i[3]])
    return time_series_list


# This function was a previous helper function in creating WML 1.1 documents
def format_ts_usgs_dv(data):
    """
    This is to make a format that Django can recognize and use while building the WaterML
    :param data: This is a list object containing all USGS observation data returned from NWIS
    :return: This returns a list that has been formatted to be used as context when passed to the WaterML doc
    """
    good_data = []
    for val in data:
        good_data.append({'AgencyCode': val[0], 'SiteCode': val[1], 'Date': val[2].strftime("%Y-%m-%dT%H:%M"),
                          'TimeOffset': "0", 'UTCTime': val[2].strftime("%Y-%m-%dT%H:%M"), 'Value': val[3],
                          'ValueCode': val[4]})
    return good_data


@login_required()
def ahps(request):
    """
    Controller for the AHPS.html page
    :param request: URL request for the page, including GET information
    :return: Returns a rendering of the page with AHPS data available displayed
    """

    # REFACTOR TO "This + 2"
    t_now = datetime.now()
    now_str = "{0}-{1}-{2}".format(t_now.year, check_digit(t_now.month), check_digit(t_now.day))

    # Get values for gauge_id and waterbody
    gauge_id = request.GET['gaugeno']
    waterbody = request.GET['waterbody']
    latitude = request.GET['lat']
    longitude = request.GET['long']

    # Get AHPS data using a dedicated function
    data = get_ahps_data(gauge_id)  # data will be in a string, but is an xml document

    # Get Closest COMID to gauge
    comid_filler = str(json.loads(urllib2.urlopen('https://ofmpub.epa.gov/waters10/PointIndexing.Service?pGeometry=POINT(' + longitude + '+' + latitude + ')').read())['output']['ary_flowlines'][0]['comid'])

    # Convert AHPS stage and flow data to a usable string format (NOT INCLUDING METADATA)
    # print data
    python_data = convert_ahps_to_python(data)

    flow_data = []
    flow = float()
    stage_data = []
    stage = float()

    for item in python_data:
        flow_data.append([item[1], item[4]])
        flow += item[4]
        stage_data.append([item[1], item[2]])
        stage += item[2]

    # Check if AHPS flow data exists
    gotdata_flow = False
    if flow > 0:
        gotdata_flow = True

    # REFACTOR TO LINE 'This + 50'
    # URL for getting forecast data and in a list
    time_series_list_api = []
    gotComid = False
    comid = None
    forecast_range = None
    comid_time = None
    forecast_date = None
    if request.GET.get('comid'):
        comid = request.GET['comid']
    if comid is not None and len(comid) > 0:
        gotComid = True
        forecast_size = request.GET['forecast_range']
        forecast_date = request.GET['forecast_date']
        comid_time = "06"
        if forecast_size == "short":
            comid_time = request.GET['comid_time']
        forecast_date_end = "2016-06-02"
        if forecast_range == "analysis_assim":
            forecast_date_end = request.GET['forecast_date_end']
        url = 'https://apps.hydroshare.org/apps/nwm-forecasts/api/GetWaterML/?config={0}&geom=channel_rt&variable=streamflow&COMID={1}&lon=&lat=&startDate={2}&endDate={3}&time={4}&lag='.format(
            forecast_size, comid, forecast_date, forecast_date_end, comid_time)

        url_api = urllib2.urlopen(url)
        data_api = url_api.read()
        # print data_api
        x = data_api.split('dateTimeUTC=')
        x.pop(0)

        for elm in x:
            info = elm.split(' ')
            time1 = info[0].replace('T', ' ')
            time2 = time1.replace('"', '')
            time3 = time2[:-3]
            time4 = time3.split(' ')
            time5 = time4[0].split('-')
            timedate = time5
            year = int(timedate[0])
            month = int(timedate[1])
            day = int(timedate[2])
            timetime = time4[1]
            time_split = timetime.split(':')
            time_minute = time_split[1].replace(':', '')
            hour = time_split[0]
            minute = time_minute[1]
            hourInt = int(hour)
            minuteInt = int(minute)
            value = info[7].split('<')
            value1 = value[0].replace('>', '')
            value2 = float(value1)
            time_series_list_api.append([datetime(year, month, day, hourInt, minuteInt), value2])

    # Plot AHPS flow data
    timeseries_plot = TimeSeries(
        height='500px',
        width='500px',
        engine='highcharts',
        title='Streamflow Plot',
        y_axis_title='Flow',
        y_axis_units='cfs',
        series=[{
            'name': 'Streamflow',
            'data': flow_data
        }, {
            'name': 'Forecasted Streamflow',
            'data': time_series_list_api
        }]
    )

    # Check if AHPS stagedata exists
    gotdata_stage = False
    if stage > 0:
        gotdata_stage = True

    # Plot AHPS stage data
    timeseries_plot_stage = TimeSeries(
        height='500px',
        width='500px',
        engine='highcharts',
        title='Stage Plot',
        y_axis_title='Stage',
        y_axis_units='ft',
        series=[{
            'name': 'Stage',
            'data': stage_data
        }]
    )

    generate_graphs_button = Button(display_text='Generate New Graphs',
                                    name='generate_graphs',
                                    attributes={""},
                                    submit=True)

    comid_input = TextInput(display_text='COMID',
                            name='comid',
                            initial=comid_filler,
                            classes='form-control')

    forecast_date_picker = DatePicker(name='forecast_date',
                                      display_text='Forecast Date Start',
                                      end_date='0d',
                                      autoclose=True,
                                      format='yyyy-mm-dd',
                                      start_view='month',
                                      today_button=True,
                                      initial=now_str)

    forecast_date_end_picker = DatePicker(name='forecast_date_end',
                                          display_text='Forecast Date End',
                                          end_date='0d',
                                          autoclose=True,
                                          format='yyyy-mm-dd',
                                          start_view='month',
                                          today_button=True,
                                          initial=now_str)

    forecast_range_select = SelectInput(display_text='Forecast Size',
                                        name='forecast_range',
                                        multiple=False,
                                        options=[('Analysis and Assimilation', 'analysis_assim'),
                                                 ('Short', 'short_range'), ('Medium', 'medium_range')],
                                        initial=['analysis_assim'],
                                        original=['analysis_assim'])

    forecast_time_select = SelectInput(display_text='Start Time',
                                       name='comid_time',
                                       multiple=False,
                                       options=[('12:00 am', "00"), ('1:00 am', "01"), ('2:00 am', "02"),
                                                ('3:00 am', "03"), ('4:00 am', "04"), ('5:00 am', "05"),
                                                ('6:00 am', "06"), ('7:00 am', "07"), ('8:00 am', "08"),
                                                ('9:00 am', "09"), ('10:00 am', "10"), ('11:00 am', "11"),
                                                ('12:00 pm', "12"), ('1:00 pm', "13"), ('2:00 pm', "14"),
                                                ('3:00 pm', "15"), ('4:00 pm', "16"), ('5:00 pm', "17"),
                                                ('6:00 pm', "18"), ('7:00 pm', "19"), ('8:00 pm', "20"),
                                                ('9:00 pm', "21"), ('10:00 pm', "22"), ('11:00 pm', "23")],
                                       initial=['12'],
                                       original=['12'])

    context = ({"gaugeno": gauge_id, "waterbody": waterbody, "timeseries_plot": timeseries_plot,
                "gotdata_flow": gotdata_flow, "timeseries_plot_stage": timeseries_plot_stage,
                "gotdata_stage": gotdata_stage, "lat": latitude, "long": longitude,
                "generate_graphs_button": generate_graphs_button, "comid_input": comid_input,
               "forecast_date_picker": forecast_date_picker, "forecast_date_end_picker": forecast_date_end_picker,
               "forecast_range_select": forecast_range_select, "forecast_time_select": forecast_time_select,
               "comid": comid, "gotComid": gotComid})

    return render(request, 'gaugeviewwml/ahps.html', context)


@login_required()
def usgs(request):
    """
    Controller for the app usgs page.
    :param request: Is the URL request of the page
    :return: renders the page with context available
    """
    # DETERMINE WHAT DATA IS NEEDED (GaugeViewer 308)...
    do_forecast = request.GET.get("forecast_range", None)
    comid = None
    forecast_range = None
    forecast_date = None

    if do_forecast is None:
        do_forecast = None
    else:
        forecast_range = request.GET['forecast_range']
        comid = request.GET['comid']
        forecast_date = request.GET['forecast_date']
        comid_time = request.GET['comid_time']

    gauge_id = request.GET['gaugeid']
    waterbody = request.GET['waterbody']
    start = request.GET['start']
    end = request.GET['end']
    lat = request.GET['lat']
    long = request.GET['long']

    # Get Closest COMID to gauge
    comid_filler = str(json.loads(urllib2.urlopen('https://ofmpub.epa.gov/waters10/PointIndexing.Service?pGeometry=POINT(' + long + '+' + lat + ')').read())['output']['ary_flowlines'][0]['comid'])

    inst_data = get_usgs_iv_data(gauge_id, start, end)
    metadata, inst_data = convert_usgs_iv_to_python(inst_data)
    inst_time_series_list = create_time_series_usgs(inst_data)

    # Check if USGS instantaneous data exists for time frame
    gotinstdata = False
    if len(inst_time_series_list) > 0:
        gotinstdata = True

    # REFACTOR TO LINE "This + 40"
    # URL for getting forecast data and in a list
    time_series_list_api = []
    gotComid = False
    if comid is not None and len(comid) > 0:
        print 'in loop'
        gotComid = True
        forecast_size = request.GET['forecast_range']
        comid_time = "06"
        if forecast_size == "short":
            comid_time = request.GET['comid_time']
        forecast_date_end = "2016-06-02"
        if forecast_range == "analysis_assim":
            forecast_date_end = request.GET['forecast_date_end']
        url = 'https://apps.hydroshare.org/apps/nwm-forecasts/api/GetWaterML/?config={0}&geom=channel_rt&variable=streamflow&COMID={1}&lon=&lat=&startDate={2}&endDate={3}&time={4}&lag='.format(forecast_range, comid, forecast_date, forecast_date_end, comid_time)
        print url
        url_api = urllib2.urlopen(url)
        data_api = url_api.read()
        x = data_api.split('dateTimeUTC=')
        x.pop(0)

        for elm in x:
            info = elm.split(' ')
            time1 = info[0].replace('T',' ')
            time2 = time1.replace('"','')
            time3 = time2[:-3]
            time4 = time3.split(' ')
            time5 = time4[0].split('-')
            timedate = time5
            year = int(timedate[0])
            month = int(timedate[1])
            day = int(timedate[2])
            timetime = time4[1]
            time_split = timetime.split(':')
            time_minute = time_split[1].replace(':', '')
            hour = time_split[0]
            minute = time_minute[1]
            hourInt = int(hour)
            minuteInt = int(minute)
            value = info[7].split('<')
            value1 = value[0].replace('>','')
            value2 = float(value1)
            time_series_list_api.append([datetime(year, month, day, hourInt, minuteInt), value2])

    # Plot USGS data
    usgs_inst_plot = TimeSeries(
        height='500px',
        width='500px',
        engine='highcharts',
        title='Instantaneous Values Streamflow Plot',
        y_axis_title='Flow',
        y_axis_units='cfs',
        series=[{
            'name': 'Streamflow',
            'data': inst_time_series_list,
        }, {
            'name': 'Forecasted Streamflow',
            'data': time_series_list_api
        }]
    )


    # Plot forecast data
    nwm_forecast_plot = TimeSeries(
        height='500px',
        width='500px',
        engine='highcharts',
        title='Streamflow Forecast',
        y_axis_title='Streamflow',
        y_axis_units='cfs',
        series=[{
            'name': 'Streamflow',
            'data': time_series_list_api
        }]
    )


    dv_data = get_usgs_dv_data(gauge_id, start, end)
    metadata, dv_data = convert_usgs_dv_to_python(dv_data)
    dv_time_series_list = create_time_series_usgs(dv_data, 'dv')

    # Check if USGS daily data exists for time frame
    gotdvdata = False
    if len(dv_time_series_list) > 0:
        gotdvdata = True

    # Plot USGS data
    usgs_dv_plot = TimeSeries(
        height='500px',
        width='500px',
        engine='highcharts',
        title='Daily Average Streamflow Values Plot',
        y_axis_title='Flow',
        y_axis_units='cfs',
        series=[{
            'name': 'Streamflow',
            'data': dv_time_series_list,
        }]
    )

    # Gizmos
    usgs_start_date_picker = DatePicker(name='start',
                                        display_text='Start Date',
                                        end_date='0d',
                                        autoclose=True,
                                        format='yyyy-mm-dd',
                                        start_view='month',
                                        today_button=True,
                                        initial=start)

    usgs_end_date_picker = DatePicker(name='end',
                                      display_text='End Date',
                                      end_date='0d',
                                      autoclose=True,
                                      format='yyyy-mm-dd',
                                      start_view='month',
                                      today_button=True,
                                      initial=end)

    generate_graphs_button = Button(display_text='Update Graph',
                                    submit=True)

    comid_input = TextInput(display_text='COMID',
                            name='comid',
                            initial=comid_filler,
                            classes='form-control')


    forecast_date_picker = DatePicker(name='forecast_date',
                                      display_text='Forecast Date Start',
                                      end_date='0d',
                                      autoclose=True,
                                      format='yyyy-mm-dd',
                                      start_view='month',
                                      today_button=True,
                                      initial=end)

    forecast_date_end_picker = DatePicker(name='forecast_date_end',
                                          display_text='Forecast Date End',
                                          end_date='0d',
                                          autoclose=True,
                                          format='yyyy-mm-dd',
                                          start_view='month',
                                          today_button=True,
                                          initial=end)

    forecast_range_select = SelectInput(display_text='Forecast Size',
                                        name='forecast_range',
                                        multiple=False,
                                        options=[('Analysis and Assimilation', 'analysis_assim'),
                                                 ('Short', 'short_range'), ('Medium', 'medium_range')],
                                        initial=['analysis_assim'],
                                        original=['analysis_assim'])

    forecast_time_select = SelectInput(display_text='Start Time',
                                       name='comid_time',
                                       multiple=False,
                                       options=[('12:00 am', "00"), ('1:00 am', "01"), ('2:00 am', "02"),
                                                ('3:00 am', "03"), ('4:00 am', "04"), ('5:00 am', "05"),
                                                ('6:00 am', "06"), ('7:00 am', "07"), ('8:00 am', "08"),
                                                ('9:00 am', "09"), ('10:00 am', "10"), ('11:00 am', "11"),
                                                ('12:00 pm', "12"), ('1:00 pm', "13"), ('2:00 pm', "14"),
                                                ('3:00 pm', "15"), ('4:00 pm', "16"), ('5:00 pm', "17"),
                                                ('6:00 pm', "18"), ('7:00 pm', "19"), ('8:00 pm', "20"),
                                                ('9:00 pm', "21"), ('10:00 pm', "22"), ('11:00 pm', "23")],
                                       initial=['12'],
                                       original=['12'])

    context = {"gaugeid": gauge_id, "waterbody": waterbody, "generate_graphs_button": generate_graphs_button,
               "usgs_inst_plot": usgs_inst_plot, "got_inst_data": gotinstdata, "usgs_dv_plot": usgs_dv_plot,
               "got_dv_data": gotdvdata, "usgs_start_date_picker": usgs_start_date_picker,
               "usgs_end_date_picker": usgs_end_date_picker, "start": start, "end": end, "lat": lat, "long": long,
               "comid_input": comid_input, "forecast_date_picker": forecast_date_picker,
               "forecast_date_end_picker": forecast_date_end_picker, "forecast_range_select": forecast_range_select,
               "forecast_time_select": forecast_time_select, "forecast_range": forecast_range, "comid": comid,
               "nwm_forecast_plot": nwm_forecast_plot, "gotComid": gotComid}

    return render(request, 'gaugeviewwml/usgs.html', context)


def get_water_ml(request):
    """
    :param request: This URL request for the page includes GET information
    :return: This will return an XML file as a download, including all necessary information
    """
    gauge_type = request.GET['type']

    if gauge_type == 'usgsiv':
        gauge_id = request.GET['gaugeid']
        if request.GET.get('span'):
            span = request.GET['span']
            if span == 'all':
                start = '1900-01-01'
                end = '2100-01-01'
            else:
                period, units = span.split('-')
                span = int(period)
                t_now = datetime.now()
                if units == 'y':
                    span *= 365
                    time_period = timedelta(days=span)
                elif units == 'm':
                    span *= 31
                    time_period = timedelta(days=span)
                else:
                    time_period = timedelta(days=span)
                t_start = t_now - time_period
                start = "{0}-{1}-{2}".format(t_start.year, check_digit(t_start.month), check_digit(t_start.day))
                end = "{0}-{1}-{2}".format(t_now.year, check_digit(t_now.month), check_digit(t_now.day))
        else:
            start = request.GET['start']
            end = request.GET['end']

        # Use the USGS IV Web Services Rest endpoint to download the proper xml document
        data = get_usgs_xml(gauge_id, start, end)
        xml_response = HttpResponse(data, content_type='text/xml')
        xml_response['Content-Disposition'] = "attachment; filename=output-time-series.xml"

    elif gauge_type == 'usgsdv':
        gauge_id = request.GET['gaugeid']
        latitude = request.GET['lat']
        longitude = request.GET['long']
        if request.GET.get('span'):
            span = request.GET['span']
            if span == 'all':
                start = '1900-01-01'
                end = '2100-01-01'
            else:
                period, units = span.split('-')
                span = int(period)
                t_now = datetime.now()
                if units == 'y':
                    span *= 365
                    time_period = timedelta(days=span)
                elif units == 'm':
                    span *= 31
                    time_period = timedelta(days=span)
                else:
                    time_period = timedelta(days=span)
                t_start = t_now - time_period
                start = "{0}-{1}-{2}".format(t_start.year, check_digit(t_start.month), check_digit(t_start.day))
                end = "{0}-{1}-{2}".format(t_now.year, check_digit(t_now.month), check_digit(t_now.day))
        else:
            start = request.GET['start']
            end = request.GET['end']
        
        data = get_usgs_dv_data(gauge_id, start, end)
        metadata, data = convert_usgs_dv_to_python(data)
        time_series = format_ts_usgs_dv(data)
        metadata.update({'GaugeID': gauge_id, "Lat": latitude, "Long": longitude})

        context = {"metadata": metadata, "time_series": time_series}

        xml_response = render_to_response('gaugeviewwml/usgsdvwaterml.xml', context)
        xml_response['Content-Type'] = 'application/xml'
        # The following line can be uncommented to cause an XML to be downloaded...
        xml_response['content-disposition'] = "attachment; filename=output-time-series.xml"

    elif gauge_type == 'ahps':
        gauge_id = request.GET['gaugeid']
        latitude = request.GET['lat']
        longitude = request.GET['long']
        variable = request.GET['var']

        data = get_ahps_data(gauge_id)
        time_series = convert_ahps_to_python(data)

        site = ElTree.fromstring(data)
        name = site.get('name')
        request_time = site.get('generationtime')
        timezone_full = site.get('timezone')
        time_offset = ''

        for i in timezone_full:
            if i.isdigit():
                time_offset += i

        time_offset = int(time_offset)
        time_offset = 0 - time_offset

        # metadata = [gauge_id, name, request_time, latitude, longitude]
        metadata = {"GaugeID": gauge_id, "SiteName": name, "ReqTime": request_time, "Lat": latitude, "Long": longitude}

        if variable == 'flow':
            time_series, units = format_ahps_ts(time_series, time_offset, 0)
            metadata.update({"VarCode": 0, "VarName": 'Flow', "UnitName": 'Cubic Feet per Second', "UnitAbbv": units})
        elif variable == 'stage':
            time_series, units = format_ahps_ts(time_series, time_offset, 1)
            metadata.update({"VarCode": 1, "VarName": 'Stage', "UnitName": 'Feet', "UnitAbbv": units})

        context = {"metadata": metadata, "time_series": time_series}

        xml_response = render_to_response('gaugeviewwml/ahpswaterml.xml', context)
        xml_response['Content-Type'] = 'application/xml'
        # The following line can be uncommented to cause an XML to be downloaded...
        xml_response['content-disposition'] = "attachment; filename=output-time-series.xml"

    return xml_response


def getOAuthHS(request):

    client_id = getattr(settings, "SOCIAL_AUTH_HYDROSHARE_KEY", "None")
    client_secret = getattr(settings, "SOCIAL_AUTH_HYDROSHARE_SECRET", "None")

    # this line will throw out from django.core.exceptions.ObjectDoesNotExist if current user is not signed in via HydroShare OAuth
    token = request.user.social_auth.get(provider='hydroshare').extra_data['token_dict']
    auth = HydroShareAuthOAuth2(client_id, client_secret, token=token)
    hs = HydroShare(auth=auth, hostname=hs_hostname)

    return hs


@login_required()
def upload_to_hydroshare(request):

    # print "running upload_to_hydroshare!"
    temp_dir = None
    try:
        return_json = {}
        if request.method == 'POST':
            post_data = request.POST

            if request.is_secure():
                front_end = 'https://'
            else:
                front_end = 'http://'

            waterml_url = front_end + request.get_host() + post_data['waterml_link']

            r_title = post_data['title']
            r_abstract = post_data['abstract']
            r_keywords_raw = post_data['keyword']
            r_keywords = r_keywords_raw.split(',')
            r_type = 'RefTimeSeriesResource'

            r_public = post_data['public']

            res_id = None
            hs = getOAuthHS(request)

            ref_type = "rest"
            metadata = []
            metadata.append({"referenceurl":
                         {"value": waterml_url,
                          "type": ref_type}})
            # print metadata
            res_id = hs.createResource(r_type,
                                       r_title,
                                       resource_file=None,
                                       keywords=r_keywords,
                                       abstract=r_abstract,
                                       metadata=json.dumps(metadata))

            if res_id is not None:
                if r_public.lower() == 'true':
                    hs.setAccessRules(res_id, public=True)
                return_json['success'] = 'File uploaded successfully!'
                return_json['newResource'] = res_id
            else:
                raise

    except ObjectDoesNotExist as e:
        # print ("ObjectDoesNotExist")
        # print str(e)
        return_json['error'] = 'Login timed out! Please re-sign in with your HydroShare account.'
    except TokenExpiredError as e:
        # print str(e)
        return_json['error'] = 'Login timed out! Please re-sign in with your HydroShare account.'
    except Exception, err:
        if "401 Unauthorized" in str(err):
            return_json['error'] = 'Username or password invalid.'
        elif "400 Bad Request" in str(err):
            return_json['error'] = 'File uploaded successfully despite 400 Bad Request Error.'
        else:
            traceback.print_exc()
            return_json['error'] = 'HydroShare rejected the upload for some reason.'
    finally:
        if temp_dir != None:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        return JsonResponse(return_json)
