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

//Define Basemap
//Here we are declaring the raster layer as a separate object to put in the map later
var baseLayer = new ol.layer.Tile({
    source: new ol.source.MapQuest({layer: 'osm'})
});

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

sources = [AHPS_Source,USGS_Source];
layers = [baseLayer,AHPS_Gauges, USGS_Gauges];

//Establish the view area. Note the reprojection from lat long (EPSG:4326) to Web Mercator (EPSG:3857)
var view = new ol.View({
        center: [-11500000, 4735000],
        projection: projection,
        zoom: 4
    })

//Declare the map object itself.
var map = new ol.Map({
    target: document.getElementById("map"),
    layers: layers,
    view: view,
});

var element = document.getElementById('popup');

var popup = new ol.Overlay({
  element: element,
  positioning: 'bottom-center',
  stopEvent: true
});

map.addOverlay(popup);




map.on('singleclick', function(evt) {
    $(element).popover('destroy');
        if (map.getTargetElement().style.cursor == "pointer"){

            var clickCoord = evt.coordinate;
            popup.setPosition(clickCoord);

            var view = map.getView();
            var viewResolution = view.getResolution();
//            var source = AHPS_Gauges.get('visible') ? AHPS_Gauges.getSource() : USGS_Gauges.getSource();
//            var source = AHPS_Source;

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
//                var USGS_Data = dataCall(USGS_url);
//                var USGS_Count = USGS_Data.documentElement.childElementCount;
//
//                console.log(AHPS_url);
//                console.log(USGS_url);
//
//                console.log(AHPS_Data);
//                console.log(AHPS_Count);
//                console.log(USGS_Data);
//                console.log(USGS_Count);

                //This is for AHPS Gauges
                for (i = 0; i < AHPS_Count; i++) {
                    var gaugeID = AHPS_Data.documentElement.children[i].attributes['GaugeLID'].value;
                    var waterbody = AHPS_Data.documentElement.children[i].attributes['Waterbody'].value;
                    var urlLink = AHPS_Data.documentElement.children[i].attributes['URL'].value;
                    var ahpshtml = "http://127.0.0.1:8000/apps/gaugeviewer/ahps/?gaugeno=" + gaugeID +"&waterbody=" + waterbody;
                    displayContent += '<tr><td>AHPS:\n'+gaugeID +'</td><td>'+ waterbody + '</td><td><a href="'+ahpshtml+'">View Data</a></td><td><a href="'+urlLink+'" target="_blank">Go to Website</a></td></tr>';
                    }

//                //This is for USGS Gauges
//                for (i = 0; i < USGS_Count; i++) {
//                    var gaugeID = USGS_Data.documentElement.children[i].attributes['SITE_NO'].value;
//                    var waterbody = USGS_Data.documentElement.children[i].attributes['STATION_NM'].value;
//                    var urlLink = USGS_Data.documentElement.children[i].attributes['NWISWEB'].value;
//                    displayContent += '<tr><td>USGS:\n'+gaugeID +'</td><td>'+ waterbody + '</td><td><a href="'+urlLink+'" target="_blank">Go to Website</a></td></tr>';
//                    }
//
//                    displayContent += '</table>';
//
//                $(element).popover({
//                'placement': 'top',
//                'html': true,
//                'content': displayContent
//                  });
//                $(element).popover('show');
                };

            if (USGS_url) {
                var USGS_Data = dataCall(USGS_url);
                var USGS_Count = USGS_Data.documentElement.childElementCount;

//                console.log(USGS_url);
//
//                console.log(USGS_Data);
//                console.log(USGS_Count);

                //This is for USGS Gauges
                for (i = 0; i < USGS_Count; i++) {
                    var gaugeID = USGS_Data.documentElement.children[i].attributes['SITE_NO'].value;
                    var waterbody = USGS_Data.documentElement.children[i].attributes['STATION_NM'].value;
                    var urlLink = USGS_Data.documentElement.children[i].attributes['NWISWEB'].value;
                    var usgshtml = "http://127.0.0.1:8000/apps/gaugeviewer/usgs/?gaugeid=" + gaugeID +"&waterbody=" + waterbody;
                    displayContent += '<tr><td>USGS:\n'+gaugeID +'</td><td>'+ waterbody + '</td><td><a href="'+usgshtml+'">View Data</a></td><td><a href="'+urlLink+'" target="_blank">Go to Website</a></td></tr>';
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
/*
map.on('singleclick', function(evt) {
    $(element).popover('destroy');
        if (map.getTargetElement().style.cursor == "pointer"){
            var clickCoord = evt.coordinate;
            popup.setPosition(clickCoord);
            var view = map.getView();
            var viewResolution = view.getResolution();
//            var source = AHPS_Gauges.get('visible') ? AHPS_Gauges.getSource() : USGS_Gauges.getSource();
//            var source = AHPS_Source;
            var AHPS_url = AHPS_Source.getGetFeatureInfoUrl(evt.coordinate, viewResolution, view.getProjection(),
              {'INFO_FORMAT': 'text/xml', 'FEATURE_COUNT': 50});
            var USGS_url = USGS_Source.getGetFeatureInfoUrl(evt.coordinate, viewResolution, view.getProjection(),
              {'INFO_FORMAT': 'text/xml', 'FEATURE_COUNT': 50});
            if (AHPS_url || USGS_url) {
        //      console.log(url)
        //      document.getElementById('popup').innerHTML = '<iframe src="' + url + '"></iframe>';
        //        var parser = new ol.format.GeoJSON();
                var displayContent = '<table border="1"><tbody><tr><th>Gauge ID</th><th>Waterbody</th><th>Link</th></tr>';
                console.log(displayContent);
                $.ajax({
                  url: AHPS_url,
//                  dataType: 'html'
                }).then(function(response) {
//                console.log(response);
//                The following 3 lines are to remove the included header if an html is returned
//                var start = response.indexOf('<h5>');
//                var end = response.indexOf('</h5>');
//                response = response.substring(0,start-1)+response.substring(end+5)
//                The following console.log commands were used in determining how to parse the returned XML
                console.log(response);
//                console.log(response.documentElement);
//                console.log(response.documentElement.nodeName);
//                console.log(response.documentElement.childElementCount);
//                console.log(response.documentElement.children);
//                console.log(response.documentElement.children[0].attributes['GaugeLID'].value);
//                var displayContent = "Gauge ID     Waterbody     Link\n";
//                var displayContent = '<table border="1"><tbody><tr><th>Gauge ID</th><th>Waterbody</th><th>Link</th></tr>';
                var xmlResponse = response.documentElement
                var gaugesSelected = xmlResponse.childElementCount;
//                console.log(gaugesSelected);
                //This is for AHPS Gauges
                for (i = 0; i < gaugesSelected; i++) {
                    var gaugeID = xmlResponse.children[i].attributes['GaugeLID'].value;
                    var waterbody = xmlResponse.children[i].attributes['Waterbody'].value;
                    var urlLink = xmlResponse.children[i].attributes['URL'].value;
//                    console.log(gaugeID);
//                    displayContent += gaugeID +'  '+ waterbody + '   Go to Website'.link(urlLink)+'\n';
//                    displayContent += gaugeID +'  '+ waterbody + '<a href="'+urlLink+'" target="_blank">     Go to Website</a>'+'\n';
                    displayContent += '<tr><td>'+gaugeID +'</td><td>'+ waterbody + '</td><td><a href="'+urlLink+'" target="_blank">Go to Website</a></td></tr>';
                    }
                    displayContent += '</table>';
                $(element).popover({
                'placement': 'top',
                'html': true,
                'content': displayContent
                  });
                $(element).popover('show');
                });
                console.log(displayContent);
            }
            if (USGS_url){
            }
        }
    });
*/

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