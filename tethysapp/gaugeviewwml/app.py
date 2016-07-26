from tethys_sdk.base import TethysAppBase, url_map_maker


class GaugeviewerWml(TethysAppBase):
    """
    Tethys app class for Gaugeviewer WML.
    """
    name = 'USGS and AHPS Gaugeviewer WML'
    index = 'gaugeviewwml:home'
    icon = 'gaugeviewwml/images/gauge_icon.png'
    package = 'gaugeviewwml'
    root_url = 'gaugeviewwml'
    color = '#e67e22'
    description = 'Allows for viewing USGS and AHPS gauges, downloading data as a WaterML file, uploading data ' \
                  'to HydroShare as a Referenced Time Series, launching data in the CUAHSI Time Series Viewer app, ' \
                  'and comparing to NWM forecasts.'
    enable_feedback = False
    feedback_emails = []

    def url_maps(self):
        """
        Add controllers
        """
        UrlMap = url_map_maker(self.root_url)

        url_maps = (UrlMap(name='home',
                           url='gaugeviewwml',
                           controller='gaugeviewwml.controllers.home'),
                    UrlMap(name='ahps',
                           url='gaugeviewwml/ahps',
                           controller='gaugeviewwml.controllers.ahps'),
                    UrlMap(name='usgs',
                           url='gaugeviewwml/usgs',
                           controller='gaugeviewwml.controllers.usgs'),
                    UrlMap(name='waterml',
                           url='gaugeviewwml/waterml',
                           controller='gaugeviewwml.controllers.get_water_ml'),
                    UrlMap(name='upload_to_hydroshare',
                           url='gaugeviewwml/upload-to-hydroshare',
                           controller='gaugeviewwml.controllers.upload_to_hydroshare'),
                    )

        return url_maps
