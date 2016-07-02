from django.shortcuts import render, render_to_response
from django.contrib.auth.decorators import login_required
from datetime import datetime, timedelta
import urllib2
from tethys_sdk.gizmos import TimeSeries
import xml.etree.ElementTree as ElTree
from tethys_sdk.gizmos import DatePicker
from tethys_sdk.gizmos import Button
from tethys_sdk.gizmos import TextInput
from tethys_sdk.gizmos import SelectInput


@login_required()
def home(request):
    """
    This is the controller for the app homepage
    :param request: This is the request from the URL map in app.py
    :return: This will render the html page
    """
    context = {}

    return render(request, 'gaugeviewwml/home.html', context)


# Check digits in month and day (i.e. 2016-05-09, not 2016-5-9) for use in gizmos
# This function is currently not needed, and will be needed if current_date() or date_two_wks_ago() are used
# def check_digit(num):
#     num_str = str(num)
#     if len(num_str) < 2:
#         num_str = '0' + num_str
#     return num_str


def get_usgs_data(gauge_id, start, end):
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


#  The following two functions determine the current and two weeks past date, and may not end up being used at all.
# def current_date():
#     t_now = datetime.now()
#     now_str = "{0}-{1}-{2}".format(t_now.year, check_digit(t_now.month), check_digit(t_now.day))
#     return now_str
#
#
# def date_two_wks_ago():
#     t_now = datetime.now()
#     two_weeks = timedelta(days=14)
#     t_2_weeks_ago = t_now - two_weeks
#     two_weeks_ago_str = "{0}-{1}-{2}".format(t_2_weeks_ago.year, check_digit(t_2_weeks_ago.month),
#                                              check_digit(t_2_weeks_ago.day))
#     return two_weeks_ago_str


def convert_usgs_to_python(data):
    """
    This will convert the entire USGS file to a python object
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

            if value_str == "Ice":
                value_str = "0"

            python_data_list.append([agency_code, site_code, datetime(year, month, day, hour_int, minute_int),
                                     time_zone, float(value_str), value_code])

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


def create_time_series(data):
    """
    :param data: Python Data list of USGS NWIS stream gauge observations
    :return: Time series list of all datetime and values for highcharts plotting
    """
    time_series_list = []
    for i in data:
        time_series_list.append([i[2], i[4]])
    return time_series_list


def format_time_series(data):
    """
    This is to make a format that Django can recognize and use while building the WaterML
    :param data: This is a list object containing all USGS observation data returned from NWIS
    :return: This returns a list that has been formatted to be used as context when passed to the WaterML doc
    """
    good_data = []
    for val in data:
        good_data.append({'AgencyCode': val[0], 'SiteCode': val[1], 'DateTime': val[2], 'TimeZone': val[3],
                          'Value': val[4], 'ValueCode': val[5]})
    return good_data


def ahps(request):
    # Controller for the app ahps page.

    # Get values for gauge_id and waterbody
    gauge_id = request.GET['gaugeno']
    waterbody = request.GET['waterbody']

    # URL for getting AHPS data
    url = 'http://water.weather.gov/ahps2/hydrograph_to_xml.php?gage={0}&output=xml'.format(gauge_id.lower())
    response = urllib2.urlopen(url)
    data = response.read()

    # Create AHPS list
    display_data = []  # Creates an empty list to contain data for later display
    value = float()
    total = float()
    site = ElTree.fromstring(data)
    # print site.tag

    # The following sections parse returned XML data to find observed and forecast information for display.
    # The XML data can be viewed by uncommenting the print url line and copying the url into a browser.
    for child in site:
        if child.tag == "observed":
            observed = child  # This is to add clarity in the next loop
            for datum in observed:
                # print datum[0].text
                # print datum[2].tag
                # print datum[2].text
                for field in datum:
                    # print field
                    # print field.tag, 'tag'
                    # print field.attrib, 'attrib'
                    # print field.text, 'text'
                    # print field.keys()
                    # print field.get('name')
                    if field.get('name') == "Flow":
                        if field.get('units') == "kcfs":
                            value = float(field.text) * 1000
                            # print value
                            total += value
                        if field.get('units') == "cfs":
                            value = float(field.text)
                            total += value
                        # print field.text
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
                display_data.append([datetime(year, month, day, hour, minute), value])
        if child.tag == "forecast":
            forecast = child
            for datum in forecast:
                for field in datum:
                    if field.get('name') == "Flow":
                        if field.get('units') == "kcfs":
                            value = float(field.text) * 1000

                        if field.get('units') == "cfs":
                            value = float(field.text)

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

                display_data.append([datetime(year, month, day, hour, minute), value])

        display_data.sort()  # Due to XML formatting the sheet must be sorted to place forecasts after observations

    # Check if AHPS flow data exists
    gotdata = False
    if total > 0:
        gotdata = True

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
            'data': display_data
        }]
    )

    # Gets stage data in a list
    observed_stage_data = []
    value_stage = float()
    total_stage = float()
    site = ElTree.fromstring(data)
    for child in site:
        if child.tag == "observed":
            observed = child  # This is to add clarity in the next loop
            for datum in observed:
                for field in datum:
                    if field.get('name') == "Stage":
                        if field.get('units') == "ft":
                            value_stage = float(field.text)
                            total_stage += value_stage

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

                observed_stage_data.append([datetime(year, month, day, hour, minute), value_stage])

    # Check if AHPS stagedata exists
    gotdata_stage = False
    if total_stage > 0:
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
            'data': observed_stage_data
        }]
    )

    context = ({"gaugeno": gauge_id, "waterbody": waterbody, "timeseries_plot": timeseries_plot, "gotdata": gotdata,
                "timeseries_plot_stage": timeseries_plot_stage, "gotdata_stage": gotdata_stage})

    return render(request, 'gaugeviewwml/ahps.html', context)


def usgs(request):
    """
    Controller for the app usgs page.
    :param request: Is the URL request of the page
    :return: renders the page with context available
    """
    # Get values from gizmos
    # start = request.GET.get("start", None)
    # comid = None
    # forecast_range = None
    # forecast_date = None

    # if start is None:
    #     gauge_id = request.GET['gaugeid']
    #     waterbody = request.GET['waterbody']
    #     date_start = request.GET['date_start']
    #     date_end = request.GET['date_end']
    #     # forecast_range = request.GET['forecast_range']
    #     # comid = request.GET['comid']
    #     # forecast_date = request.GET['forecast_date']
    #     # comid_time = request.GET['comid_time']
    # else:
    gauge_id = request.GET['gaugeid']
    waterbody = request.GET['waterbody']
    start = request.GET['start']
    end = request.GET['end']

    data = get_usgs_data(gauge_id, start, end)
    metadata, data = convert_usgs_to_python(data)
    time_series_list = create_time_series(data)

    # Check if USGS data exists for time frame
    gotdata = False
    if len(time_series_list) > 0:
        gotdata = True

    # URL for getting forecast data and in a list
    # time_series_list_api = []
    # got_comid = False
    # if comid is not None and len(comid) > 0:
    #     got_comid = True
    #     forecast_size = request.GET['forecast_range']
    #     comid_time = "06"
    #     if forecast_size == "short":
    #         comid_time = request.GET['comid_time']
    #     forecast_date_end = "2016-06-02"
    #     if forecast_range == "analysis_assim":
    #         forecast_date_end = request.GET['forecast_date_end']
    #     url = 'https://apps.hydroshare.org/apps/nwm-forecasts/api/GetWaterML/?config={0}&geom=channel_rt&' \
    #           'variable=streamflow&COMID={1}&lon=&lat=&startDate={2}&endDate={3}&time={4}&lag='\
    #         .format(forecast_range, comid, forecast_date, forecast_date_end, comid_time)
    #     print url
    #     url_api = urllib2.urlopen(url)
    #     data_api = url_api.read()
    #     # print data_api
    #     x = data_api.split('dateTimeUTC=')
    #     x.pop(0)
    #
    #     for elm in x:
    #         info = elm.split(' ')
    #         time1 = info[0].replace('T', ' ')
    #         time2 = time1.replace('"', '')
    #         time3 = time2[:-3]
    #         time4 = time3.split(' ')
    #         time5 = time4[0].split('-')
    #         timedate = time5
    #         year = int(timedate[0])
    #         month = int(timedate[1])
    #         day = int(timedate[2])
    #         timetime = time4[1]
    #         time_split = timetime.split(':')
    #         time_minute = time_split[1].replace(':', '')
    #         hour = time_split[0]
    #         minute = time_minute[1]
    #         hour_int = int(hour)
    #         minute_int = int(minute)
    #         value = info[7].split('<')
    #         value1 = value[0].replace('>', '')
    #         value2 = float(value1)
    #         time_series_list_api.append([datetime(year, month, day, hour_int, minute_int), value2])

    # Plot USGS data
    usgs_plot = TimeSeries(
        height='500px',
        width='500px',
        engine='highcharts',
        title='Streamflow Plot',
        y_axis_title='Flow',
        y_axis_units='cfs',
        series=[{
            'name': 'Streamflow',
            'data': time_series_list,
        }]
    )

    # Plot forecast data
    # nwm_forecast_plot = TimeSeries(
    #     height='500px',
    #     width='500px',
    #     engine='highcharts',
    #     title='Streamflow Forecast',
    #     y_axis_title='Streamflow',
    #     y_axis_units='cfs',
    #     series=[{
    #         'name': 'Streamflow',
    #         'data': time_series_list_api
    #     }]
    # )

    # Gizmos
    usgs_start_date_picker = DatePicker(name='start',
                                        display_text='Start Date',
                                        end_date='0d',
                                        autoclose=True,
                                        format='yyyy-mm-dd',
                                        # start_date='2015-12-01',
                                        start_view='month',
                                        today_button=True,
                                        # initial= t_2_weeks_ago.strftime('%Y-%m-%d'))
                                        initial=start)

    usgs_end_date_picker = DatePicker(name='end',
                                      display_text='End Date',
                                      end_date='0d',
                                      autoclose=True,
                                      format='yyyy-mm-dd',
                                      # start_date='2016-02-01',
                                      start_view='month',
                                      today_button=True,
                                      # initial=t_now.strftime('%Y-%m-%d'))
                                      initial=end)

    generate_graphs_button = Button(display_text='Update Graph',
                                    # name='Generate New Graph',
                                    # attributes={""},
                                    submit=True)

    # comid_input = TextInput(display_text='COMID',
    #                         name='comid',
    #                         initial='',
    #                         classes='form-control')
    #
    # forecast_date_picker = DatePicker(name='forecast_date',
    #                                   display_text='Forecast Date Start',
    #                                   end_date='0d',
    #                                   autoclose=True,
    #                                   format='yyyy-mm-dd',
    #                                   start_view='month',
    #                                   today_button=True,
    #                                   initial=now_str)
    #
    # forecast_date_end_picker = DatePicker(name='forecast_date_end',
    #                                       display_text='Forecast Date End',
    #                                       end_date='0d',
    #                                       autoclose=True,
    #                                       format='yyyy-mm-dd',
    #                                       start_view='month',
    #                                       today_button=True,
    #                                       initial=now_str)
    #
    # forecast_range_select = SelectInput(display_text='Forecast Size',
    #                                     name='forecast_range',
    #                                     multiple=False,
    #                                     options=[('Analysis and Assimilation', 'analysis_assim'),
    #                                              ('Short', 'short_range'), ('Medium', 'medium_range')],
    #                                     initial=['analysis_assim'],  # This line is an error in old Tethys versions
    #                                     original=['analysis_assim'])
    #
    # forecast_time_select = SelectInput(display_text='Start Time',
    #                                    name='comid_time',
    #                                    multiple=False,
    #                                    options=[('12:00 am', "00"), ('1:00 am', "01"), ('2:00 am', "02"),
    #                                             ('3:00 am', "03"), ('4:00 am', "04"), ('5:00 am', "05"),
    #                                             ('6:00 am', "06"), ('7:00 am', "07"), ('8:00 am', "08"),
    #                                             ('9:00 am', "09"), ('10:00 am', "10"), ('11:00 am', "11"),
    #                                             ('12:00 pm', "12"), ('1:00 pm', "13"), ('2:00 pm', "14"),
    #                                             ('3:00 pm', "15"), ('4:00 pm', "16"), ('5:00 pm', "17"),
    #                                             ('6:00 pm', "18"), ('7:00 pm', "19"), ('8:00 pm', "20"),
    #                                             ('9:00 pm', "21"), ('10:00 pm', "22"), ('11:00 pm', "23")],
    #                                    initial=['12'],  # This line may throw an error in older versions of Tethys
    #                                    original=['12'])
    #
    # context = {"gaugeid": gauge_id, "waterbody": waterbody, "comid_input": comid_input,
    #            "forecast_date_picker": forecast_date_picker, "forecast_date_end_picker": forecast_date_end_picker,
    #            "forecast_range_select": forecast_range_select, "forecast_time_select": forecast_time_select,
    #            "forecast_range": forecast_range, "comid": comid, "generate_graphs_button": generate_graphs_button,
    #            "usgs_plot": usgs_plot, "nwm_forecast_plot": nwm_forecast_plot, "gotdata": gotdata,
    #            "usgs_start_date_picker": usgs_start_date_picker, "usgs_end_date_picker": usgs_end_date_picker,
    #            "date_start": date_start, "date_end": date_end, "got_comid": got_comid}

    context = {"gaugeid": gauge_id, "waterbody": waterbody, "generate_graphs_button": generate_graphs_button,
               "usgs_plot": usgs_plot, "gotdata": gotdata, "usgs_start_date_picker": usgs_start_date_picker,
               "usgs_end_date_picker": usgs_end_date_picker, "start": start, "end": end}

    return render(request, 'gaugeviewwml/usgs.html', context)


def get_water_ml(request):

    gauge_id = request.GET['gaugeid']
    start = request.GET['start']
    end = request.GET['end']

    data = get_usgs_data(gauge_id, start, end)
    print data
    metadata, data = convert_usgs_to_python(data)
    print metadata
    print data
    time_series = format_time_series(data)
    print time_series

    context = {"gaugeid": gauge_id, "metadata": metadata, "time_series": time_series}

    xml_response = render_to_response('gaugeviewwml/waterml.xml', context)
    xml_response['Content-Type'] = 'application/xml'
    # The following line can be uncommented to cause an XML to be downloaded...
    # xml_response['content-disposition'] = "attachment; filename=output-time-series.xml"

    return xml_response
