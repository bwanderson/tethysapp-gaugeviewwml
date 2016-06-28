//This function is ran to set a listener to update the map size when the navigation pane is opened or closed
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