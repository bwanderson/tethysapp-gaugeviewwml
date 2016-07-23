//loads modal on page load
$(document).ready(function () {
    $("#welcome-popup").modal("show");
});

function dataCall(inputURL) {
    var result = null;
        $.ajax({
        url: inputURL,
        async: false,
        }).then(function(response) {
            result = response;
        });
        return result;
}


//Here we are declaring the projection object for Web Mercator
var projection = ol.proj.get('EPSG:3857');

// Define Basemap
// Here we are declaring the raster layer as a separate object to put in the map later
var baseLayer = new ol.layer.Tile({
    source: new ol.source.BingMaps({
        key: '5TC0yID7CYaqv3nVQLKe~xWVt4aXWMJq2Ed72cO4xsA~ApdeyQwHyH_btMjQS1NJ7OHKY8BK-W-EMQMrIavoQUMYXeZIQOUURnKGBOC7UCt4',
        imagerySet: 'AerialWithLabels' // Options 'Aerial', 'AerialWithLabels', 'Road'
        })
    });

// If you desired to use the OSM basemap
//var baseLayer = new ol.layer.Tile({
//    source: new ol.source.OSM({})
//});

// as of July 11, 2016 Mapquest is no longer accessible See: goo.gl/xB0xXt
//var baseLayer = new ol.layer.Tile({
//    source: new ol.source.MapQuest({layer: 'osm'})
//});


//Define all WMS Sources:

var AHPS_Source =  new ol.source.TileWMS({
        url:'http://geoserver.byu.edu/arcgis/services/NWC/AHPS_Gauges/MapServer/WmsServer?',
        params:{
            LAYERS:"0",
//            FORMAT:"image/png", //Not a necessary line, but maybe useful if needed later
        },
        crossOrigin: 'Anonymous' //This is necessary for CORS security in the browser
        });

var USGS_Source =  new ol.source.TileWMS({
        url:'http://geoserver.byu.edu/arcgis/services/NWC/USGS_Gauges/MapServer/WmsServer?',
        params:{
            LAYERS:"0",
//            FORMAT:"image/png", //Not a necessary line, but maybe useful if needed later
        },
        crossOrigin: 'Anonymous'
        });


//Define all WMS layers
//The gauge layers can be changed to layer.Image instead of layer.Tile (and .ImageWMS instead of .TileWMS) for a single tile
var AHPS_Gauges = new ol.layer.Tile({
    source:AHPS_Source
    }); //Thanks to http://jsfiddle.net/GFarkas/tr0s6uno/ for getting the layer working

var USGS_Gauges = new ol.layer.Tile({
    source:USGS_Source
    }); //Thanks to http://jsfiddle.net/GFarkas/tr0s6uno/ for getting the layer working

//Set opacity of layers
AHPS_Gauges.setOpacity(0.7);
USGS_Gauges.setOpacity(0.7);

sources = [AHPS_Source,USGS_Source];
layers = [baseLayer,AHPS_Gauges, USGS_Gauges];

//Establish the view area. Note the reprojection from lat long (EPSG:4326) to Web Mercator (EPSG:3857)
var view = new ol.View({
        center: [-11500000, 4735000],
        projection: projection,
        zoom: 4,
    })

//Declare the map object itself.
var map = new ol.Map({
    target: document.getElementById("map"),
    layers: layers,
    view: view,
});

//Zoom slider
map.addControl(new ol.control.ZoomSlider());

var element = document.getElementById('popup');

var popup = new ol.Overlay({
  element: element,
  positioning: 'bottom-center',
  stopEvent: true
});

map.addOverlay(popup);

function run_geocoder(){
        g = new google.maps.Geocoder();
        search_location = document.getElementById('location_input').value;
        g.geocode({'address':search_location},geocoder_success);
    };

function geocoder_success(results, status) {
    if (status == google.maps.GeocoderStatus.OK) {
        r=results;
        flag_geocoded=true;
        Lat = results[0].geometry.location.lat();
        Lon = results[0].geometry.location.lng();

        var dbPoint = {
            "type": "Point",
            "coordinates": [Lon, Lat]
        }

        var coords = ol.proj.transform(dbPoint.coordinates, 'EPSG:4326','EPSG:3857');
        addClickPoint(coords);
        CenterMap(Lat,Lon);
        //map.getView().setZoom(14);
        run_point_indexing_service([Lon,Lat]);
//        alert(results[0].formatted_address);
    } else {
        alert("Geocode was not successful for the following reason: " + status);
    }
};

function reverse_geocode(coord){
    var latlon = new google.maps.LatLng(coord[1],coord[0]);
    var g = new google.maps.Geocoder();
    g.geocode({'location':latlon}, reverse_geocode_success);
};

function reverse_geocode_success(results, status) {
    if (status == google.maps.GeocoderStatus.OK) {
        var location = results[1].formatted_address;
        if (gnis_name != null) {
            location = gnis_name + ", " + location;
        }

    } else {
        document.getElementById("location_input").value = "Location Not Available";
    }
};

function handle_search_key(e) {
    // Handle a key press in the location search text box.
    // This handles pressing the enter key to initiate the search.
    if (e.keyCode == 13) {
        run_geocoder();
    }
};

//find current date
var date = new Date();

var yyyy = date.getFullYear().toString();
var mm = (date.getMonth()+1).toString();
var dd  = date.getDate().toString();

var mmChars = mm.split('');
var ddChars = dd.split('');

var datestringnow = yyyy + '-' + (mmChars[1]?mm:"0"+mmChars[0]) + '-' + (ddChars[1]?dd:"0"+ddChars[0]);

//Find the gaugeid and waterbody when using the generate new graph button
$(function () {
    $('#gaugeid').val(window.location.search.split('&')[0].split('=')[1])
});

//Click funtion to choose gauge on map
map.on('singleclick', function(evt) {
    $(element).popover('destroy');
        if (map.getTargetElement().style.cursor == "pointer"){

            var clickCoord = evt.coordinate;
            popup.setPosition(clickCoord);

            var view = map.getView();
            var viewResolution = view.getResolution();

// NEED TO MAKE THIS ONLY CREATE URL IF NECESSARY!!!
            if (document.getElementById("ch_AHPS_Gauges").checked){
                var AHPS_url = AHPS_Source.getGetFeatureInfoUrl(evt.coordinate, viewResolution, view.getProjection(),
                  {'INFO_FORMAT': 'text/xml', 'FEATURE_COUNT': 50});
            };

            if (document.getElementById("ch_USGS_Gauges").checked){
                var USGS_url = USGS_Source.getGetFeatureInfoUrl(evt.coordinate, viewResolution, view.getProjection(),
                  {'INFO_FORMAT': 'text/xml', 'FEATURE_COUNT': 50});
              };
              
            var displayContent = '<table border="1"><tbody><tr><th>Gauge Type & ID</th><th>Waterbody</th><th>Info</th><th>Link</th></tr>';

            if (AHPS_url) {
                var AHPS_Data = dataCall(AHPS_url);
                var AHPS_Count = AHPS_Data.documentElement.childElementCount;

                //This is for AHPS Gauges
                for (i = 0; i < AHPS_Count; i++) {
                    var gaugeID = AHPS_Data.documentElement.children[i].attributes['GaugeLID'].value;
                    var waterbody = AHPS_Data.documentElement.children[i].attributes['Waterbody'].value;
                    var urlLink = AHPS_Data.documentElement.children[i].attributes['URL'].value;
                    var lat = AHPS_Data.documentElement.children[i].attributes['Latitude'].value;
                    var long = AHPS_Data.documentElement.children[i].attributes['Longitude'].value;
                    var ahpshtml = "/apps/gaugeviewwml/ahps/?gaugeno=" + gaugeID +"&waterbody=" + waterbody + "&lat=" + lat + "&long=" + long;
                    displayContent += '<tr><td>AHPS:\n'+gaugeID +'</td><td>'+ waterbody + '</td><td><a href="'+ahpshtml+'" target="_blank">View Data</a></td><td><a href="'+urlLink+'" target="_blank">Go to Website</a></td></tr>';
                    }
                };

            if (USGS_url) {
                var USGS_Data = dataCall(USGS_url);
                var USGS_Count = USGS_Data.documentElement.childElementCount;

                //find two weeks ago date
                var date_old = new Date();

                //document.write(date_old.toLocaleString());
                date_old.setDate(date_old.getDate() - 14);

                //document.write(date_old.toLocaleString());
                date_str = date_old.toISOString();
                var two_weeks_ago_str = date_str.split('T')[0]

                //console.log(date_old)

                //This is for USGS Gauges
                for (i = 0; i < USGS_Count; i++) {
                    var gaugeID = USGS_Data.documentElement.children[i].attributes['SITE_NO'].value;
                    var waterbody = USGS_Data.documentElement.children[i].attributes['STATION_NM'].value;
                    var urlLink = USGS_Data.documentElement.children[i].attributes['NWISWEB'].value;
                    var lat = USGS_Data.documentElement.children[i].attributes['LAT_SITE'].value;
                    var long = USGS_Data.documentElement.children[i].attributes['LON_SITE'].value;
                    var usgshtml = "/apps/gaugeviewwml/usgs/?gaugeid=" + gaugeID +"&waterbody=" + waterbody+"&start=" + two_weeks_ago_str + "&end=" + datestringnow + "&lat=" + lat + "&long=" + long;
                    displayContent += '<tr><td>USGS:\n'+gaugeID +'</td><td>'+ waterbody + '</td><td><a href="'+usgshtml+'" target="_blank">View Data</a></td><td><a href="'+urlLink+'" target="_blank">Go to Website</a></td></tr>';
                    }
                };
                    displayContent += '</table>';

                $(element).popover({
                'placement': 'top',
                'html': true,
                'content': displayContent
                  });

                $(element).popover('show');
                $(element).next().css('cursor','text');
//                console.log(displayContent);
            }
        });

  map.on('pointermove', function(evt) {
    if (evt.dragging) {
      return;
    }
    var pixel = map.getEventPixel(evt.originalEvent);
    var hit = map.forEachLayerAtPixel(pixel, function(layer) {
    if (layer != baseLayer){
      return true;}
    });
    map.getTargetElement().style.cursor = hit ? 'pointer' : '';
  });


//This function is ran to set a listener to update the map size when the navigation pane is opened or closed
(function () {
    var target, observer, config;
    // select the target node
    target = $('#app-content-wrapper')[0];

    observer = new MutationObserver(function () {
        window.setTimeout(function () {
            map.updateSize();
        }, 350);
    });

    config = {attributes: true};

    observer.observe(target, config);
}());

var trigger_search = document.getElementById("location_input");

trigger_search.addEventListener("keydown",function(e) {
    // Handle a key press in the location search text box.
    // This handles pressing the enter key to initiate the search.
    if (e.keyCode == 13) {
        run_geocoder();
    }
});

// ARE THESE TWO FUNCTIONS DUPLICATES???? WHY ARE THEY NEEDED???

function run_geocoder(){
        g = new google.maps.Geocoder();
        search_location = document.getElementById('location_input').value;
        g.geocode({'address':search_location},geocoder_success);
    };

function geocoder_success(results, status) {
    if (status == google.maps.GeocoderStatus.OK) {
        r=results;
        flag_geocoded=true;
        Lat = results[0].geometry.location.lat();
        Lon = results[0].geometry.location.lng();
        var dbPoint = {
            "type": "Point",
            "coordinates": [Lon, Lat]
        }

        var coords = ol.proj.transform(dbPoint.coordinates, 'EPSG:4326','EPSG:3857');
        map.getView().setCenter(coords);
        map.getView().setZoom(12);
    } else {
        alert("Geocode was not successful for the following reason: " + status);
    }
};
