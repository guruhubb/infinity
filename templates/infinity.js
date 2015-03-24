/**
 * Created by saswata_basu on 3/23/15.
 */

    var	map1,
        map2,
        bigButton = false,
        refreshIntervalId,
        refreshIntervalIdSite,
        deviceTypes = [],
        markers = [],
        circles = [],
	    lines = [],
        links = [],
        sites = [],
        links_data = [],
        devices_data = [],
        fromTime = {{fromTime}},
        toTime = {{ toTime }},
        popup = L.popup(),
        test = true,
        onSite = false,
        cap_limit = 2,
        data_cap = {{ data.cap }},
        data_data = {{ data.data }},
        data_distance = {{ data.distance }},
        stream_cap = {{ stream.cap }},
        stream_data = {{ stream.data }},
        stream_distance = {{ stream.distance }},
        hist_cap = {{ histogram.avg_cap }},
        hist_freq = {{ histogram.records }},
        hist_distance = {{ histogram.distance }}
        path_cap = {{ path.cap }},
        path_lng = {{ path.lng }},
        path_lat = {{ path.lat }},
        path_time = {{ path.time }},
        path_dist = {{ path.dist }},
        path_cov = {{ path.cov }},
        site = '{{ site }}',
        link = '{{ link }}',
        deviceType = '{{ type }}',
        streamInterval = '{{ streamInterval }}',
        updateInterval = '{{ updateInterval }}';
        lastTime = (new Date).getTime();

    function loadDevicesAndLinks() {

        var devices_url = '{{ devices_url }}';
        var links_url = '{{ links_url }}';
        var time = lastTime;
        $.post(devices_url, function(data) {
            if (data) {
                clearPlacemarks();
                var length = data.length;
                var noDevicePosition = true;
                for (var i=0; i<length; i++) {
                    var device = data[i];
                    var lat = device.lat;
                    var lng = device.lng;
                    time = device.time;
                    if (lat && lng) {
                        noDevicePosition = false;
                        addMarker(device, lat, lng);
                    }
                }
                aj = $.ajax({
                    type: "GET",
                    url: '{{ links_url }}',
                    async: true,
                    data: { time: time},
                    contentType: "application/json; charset=utf-8",
                    dataType: "json"});
                aj.done(function (response, textStatus, jqXHR) {
                    if (response) {
                        clearLines(); // Remove old placemarks
                        var length = response.length;
                        var noDevicePosition = true;
                        for (var i=0; i<length; i++) {
                            var link = response[i];
                            var lat = link.lat;
                            var lng = link.lng;
                            if (lat && lng) {
                                noDevicePosition = false;
                                addLink(link);
                            }
                        }
                    }
                });
                aj.fail(function (jqXHR, textStatus, errorThrown) {
                });
            }

        });
    }
    function loadDevices() {
        clearPlacemarks(); // Remove old placemarks

	    var url = '{{ devices_url }}';
	    $.post(url, function(data) {
            if (data) {
                var length = data.length;
                var noDevicePosition = true;
                for (var i=0; i<length; i++) {
                    var device = data[i];
                    var lat = device.lat;
                    var lng = device.lng;
                    if (lat && lng) {
                        noDevicePosition = false;
                        addMarker(device, lat, lng);
                    }
                }
            }
	    });
    }

    function loadLinks() {
	    var url = '{{ links_url }}';
	    $.post(url, function(data) {
            if (data) {
                clearLines(); // Remove old placemarks
                var length = data.length;
                for (var i=0; i<length; i++) {
                    var link = data[i];
                        addLink(link);
                }
            }
	    });
    }

    function addMarker(device, lat, lng) {
        var title = device.site;
            var d = new Date(device.time);
            title = title + '<br>' + device.type ;
            title = title + '<br> Tx: ' + device.tx + ' Mbps ';
            title = title + '<br> Rx: ' + device.rx + ' Mbps ';
            title = title + '<br> Capacity: ' + device.cap + " Mbps ";
            title = title + '<br> Traffic: ' + device.data + " Mbps ";
            title = title + '<br> Time: ' + d.toLocaleString();
        var color, circle, cap;
        cap = device.cap;
            if (cap > 500) {
                color = '#0ca35f';
            }
            else if (cap > 450) {
                color = '#3cb57e';
            }
            else if (cap > 400) {
                color = '#6dc79f';
            }
            else if (cap > 350) {
                color = '#9ddabf';
            }
            else if (cap > 300) {
                color = '#ceecdf';
            }
            else if (cap > 100) {
                color = '#d7efe5';
            }
            else {
                color = 'red';
            }
        marker = L.circle([lat, lng], 5000, {
            color: color,
            fillColor: color,
            fillOpacity: 1.0
        });
        marker.addTo(map1);
        marker.bindPopup(title);
        marker.on('click', onMarkerClick);
        markers.push(marker);
        deviceTypes.push(device.type);
        sites.push(device.site);
    }
    function addLink(link) {
        var title = link.connId;
        if (link.cap > cap_limit) {
            var d = new Date(link.time);
            title = title + '<br> Tx: ' + link.tx + ' Mbps ';
            title = title + '<br> Rx: ' + link.rx + ' Mbps ';
            title = title + '<br> Distance: ' + link.distance + " miles ";
            title = title + '<br> Capacity: ' + link.cap + " Mbps ";
            title = title + '<br> Traffic: ' + link.data + " Mbps ";
            title = title + '<br> Time: ' + d.toLocaleString();
        }
        else { // the device is not online
            title = title + ' is offline';
        }
        var color, circle,cap ;
        cap = link.cap;
        if (link.cap > cap_limit) {
            if (cap > 500) {
                color = '#0ca35f';
            }
            else if (cap > 450) {
                color = '#3cb57e';
            }
            else if (cap > 400) {
                color = '#6dc79f';
            }
            else if (cap > 350) {
                color = '#9ddabf';
            }
            else if (cap > 300) {
                color = '#ceecdf';
            }
            else {
                color = '#d7efe5';
            }
        } else {
            if (device.distance < TYPICAL_COVERAGE_MILES) {
                color = 'red';
            } else {
                color = 'orange';
            }
        }
        var pointA = new L.LatLng(link.lat, link.lng);
        var pointB = new L.LatLng(link.lat1,link.lng1);
        var pointList = [pointA, pointB];

        var line = new L.Polyline(pointList, {
                                    color: color,
                                    weight: 5,
                                    opacity: 0.5,
                                    smoothFactor: 1
                                });
        line.addTo(map1);
        lines.push(line);
        line.bindPopup(title);
        line.on('click', onLinkClick);
        links.push(link.connId);
    }
    function clearPlacemarks() {
        for (var i = 0; i < markers.length; i++) {
            map1.removeLayer(markers[i]);
        }
        markers = [];
        sites = [];
        deviceTypes = [];
    }
    function clearLines() {
        for (var i = 0; i < lines.length; i++) {
            map1.removeLayer(lines[i]);
        }
        lines = [];
        links = [];
    }
    function addCircle(lng, lat, cap, time, dist, cov) {
        var color, circle,d ;
        if (cov) {
            if (cap > 500) {
                color = '#0ca35f';
            }
            else if (cap > 450) {
                color = '#3cb57e';
            }
            else if (cap > 400) {
                color = '#6dc79f';
            }
            else if (cap > 350) {
                color = '#9ddabf';
            }
            else if (cap > 300) {
                color = '#ceecdf';
            }
            else {
                color = '#d7efe5';
            }
        } else {
            if (dist < TYPICAL_COVERAGE_MILES) {
                color = 'red';
            } else {
                color = 'orange';
            }
        }
        circle = L.circle([lat, lng], 250, {
                color: color,
                fillColor: color,
                fillOpacity: 0.5
            });
        circle.addTo(map2);
        d = new Date(time);
        title = site;
        title = title + '<br> Lat: ' + lat ;
        title = title + '<br> Lng: ' + lng ;
        title = title + '<br> Distance: ' + dist + " miles ";
        title = title + '<br> Capacity: ' + cap + " Mbps ";
        title = title + '<br> Time: ' + d.toLocaleString();
        circle.bindPopup(title);
        circles.push(circle);
    }
    function addCircle_site(lng, lat, cap, time) {
        var color, circle,d ;
            if (cap > 40) {
                color = '#0ca35f';
            }
            else if (cap > 30) {
                color = '#3cb57e';
            }
            else if (cap > 20) {
                color = '#6dc79f';
            }
            else if (cap > 10) {
                color = '#9ddabf';
            }
            else if (cap > 5) {
                color = '#ceecdf';
            }
            else if (cap > 1){
                color = '#d7efe5';
            } else {
                color = 'red';
            }
        circle = L.circle([lat, lng], 250, {
                color: color,
                fillColor: color,
                fillOpacity: 0.5
            });
        circle.addTo(map2);
        d = new Date(time);
        title = site;
        title = title + '<br> Lat: ' + lat ;
        title = title + '<br> Lng: ' + lng ;
        title = title + '<br> Capacity: ' + cap + " Mbps ";
        title = title + '<br> Time: ' + d.toLocaleString();
        circle.bindPopup(title);
        circles.push(circle);
    }


    function clearCircles() {
        var len = circles.length;
        for (var i=0; i<len; i++) {
            var circle = circles[i];
            map2.removeLayer(circle);
        }
        circles = [];
    }

    function addConnectionLine(lat1, lng1, lat2, lng2, color) {
        var pointA = new L.LatLng(lat1, lng1);
        var pointB = new L.LatLng(lat2, lng2);
        var pointList = [pointA, pointB];

        var firstpolyline = new L.Polyline(pointList, {
                                    color: color,
                                    weight: 3,
                                    opacity: 0.5,
                                    smoothFactor: 1
                                });
        firstpolyline.addTo(map);
        lines.push(firstpolyline);
    }
    function firstMap(){
        map1 = L.map('map1').setView([33.732124, -117.900595], 8);
        L.tileLayer('http://{s}.tiles.mapbox.com/v3/infinity.k4e0f93f/{z}/{x}/{y}.png', {maxZoom: 18}).addTo(map1);
        map1.attributionControl.setPrefix(false);
        // Disable drag and zoom handlers.
        map1.dragging.disable();
        map1.touchZoom.disable();
        map1.doubleClickZoom.disable();
        map1.scrollWheelZoom.disable();

        // Disable tap handler, if present.
        if (map1.tap) map1.tap.disable();
        loadDevicesAndLinks();
    }
    function secondMap(){

        map2 = L.map('map2').setView(medLatLng(path_lat, path_lng), 9);
        L.tileLayer('http://{s}.tiles.mapbox.com/v3/saswata.jldkb3nl/{z}/{x}/{y}.png', {maxZoom: 18}).addTo(map2);
        map2.attributionControl.setPrefix(false);
        map2.touchZoom.disable();
        map2.dragging.disable();
        if (map2.tap) map2.tap.disable();
        map2.doubleClickZoom.disable();
        map2.scrollWheelZoom.disable();
        clearCircles();
        for (i=0; i< path_cap.length; i+=1) {
            addCircle(path_lng[i], path_lat[i], path_cap[i], path_time[i], path_dist[i], path_cov[i])
        }
    }
    function medLatLng (path_lat, path_lng){
        var min_lat = Math.min.apply(null, path_lat),
            max_lat = Math.max.apply(null, path_lat),
            med_lat = (max_lat+min_lat)/ 2,
            min_lng = Math.min.apply(null, path_lng),
            max_lng = Math.max.apply(null, path_lng),
            med_lng = (max_lng+min_lng)/2;
        return [med_lat, med_lng];
    }
    function onMapClick1(e) {
        popup
            .setLatLng(e.latlng)
            .setContent("You clicked the map at " + e.latlng.toString())
            .openOn(map1);
        map1.panTo(e.latlng);
    }
    function onMapClick2(e) {
        popup
            .setLatLng(e.latlng)
            .setContent("You clicked the map at " + e.latlng.toString())
            .openOn(map2);
        map2.panTo(e.latlng);
    }
    function onMarkerClick(e) {
        map1.panTo(e.latlng);
        for (i = 0; i < markers.length; i++) {
            if (markers[i]._leaflet_id == this._leaflet_id) {
               site = sites[i];
               deviceType = deviceTypes[i];
            }
        }
        onSite = true;
        window.clearInterval(refreshIntervalIdSite);
        getDataMarker();
        lastPointDataMarker();
    }
    function onLinkClick(e) {
        map1.panTo(e.latlng);
        for (i = 0; i < lines.length; i++) {
            if (lines[i]._leaflet_id == this._leaflet_id) {
                site = links[i];
                deviceType = deviceTypes[i*2];
            }
        }
        onSite = false;
        window.clearInterval(refreshIntervalId);
        getData();
        lastPointData();

    }
    function lastPointDataMarker() {
        refreshIntervalIdSite = window.setInterval(function(){
            var stream = $('#stream').highcharts();
            aj = $.ajax({
                type: "GET",
                url: '{{ lastpoint_url_site }}',
                async: true,
                data: { site: site, lastTime: lastTime,type:deviceType},
                contentType: "application/json; charset=utf-8",
                dataType: "json"});
            aj.done(function (response, textStatus, jqXHR) {
                var totalPoints = response.cap.length;
                if (totalPoints > 0) {
                    lastTime = response.cap[totalPoints - 1][0];
                }
                for (i = 0; i < totalPoints; i++) {

                    if ((stream.series[0].points.length) <80){
                        stream.series[0].addPoint(response.data[0], false);
                        stream.series[1].addPoint(response.cap[0], false);
                        stream.series[2].addPoint(response.distance[0], true);
                    } else {
                        stream.series[0].addPoint(response.data[0], false, true);
                        stream.series[1].addPoint(response.cap[0], false, true);
                        stream.series[2].addPoint(response.distance[0], true, true);
                    }
                }
            });
            aj.fail(function (jqXHR, textStatus, errorThrown) {
            });
        }, streamInterval);
        }
    function getDataMarker() {
        aj = $.ajax({
                type: "GET",
                url: '{{ stream_url_site }}',
                async: true,
                data: { site:site, type:deviceType },
                contentType: "application/json; charset=utf-8",
                dataType: "json"});
        aj.done(function (response, textStatus, jqXHR) {
            var stream = $('#stream').highcharts();

                stream.series[0].setData(response.data, false);
                stream.series[1].setData(response.cap, false);

                stream.series[2].setData(response.distance,true);
                stream.setTitle(null, { text: site });

        });
        aj.fail(function (jqXHR, textStatus, errorThrown) {
        });

        aj = $.ajax({
                type: "GET",
                url: '{{ chart_url_site }}',
                async: true,
                data: { site:site, fromTime:fromTime, toTime:toTime,type:deviceType },
                contentType: "application/json; charset=utf-8",
                dataType: "json"});
        aj.done(function (response, textStatus, jqXHR) {
                var chart = $('#chart').highcharts();
                chart.series[0].setData(response.data,false);
                chart.series[1].setData(response.cap,false);
                chart.series[2].setData(response.distance, true);
                chart.setTitle(null, { text: site });

        });
        aj.fail(function (jqXHR, textStatus, errorThrown) {
        });

        aj1 = $.ajax({
                type: "GET",
                url: '{{ histogram_url_site }}',
                async: true,
                data: { site:site, fromTime:fromTime, toTime:toTime,type:deviceType },
                contentType: "application/json; charset=utf-8",
                dataType: "json"});
        aj1.done(function (response, textStatus, jqXHR) {
                var hist = $('#histogram').highcharts();
                hist.xAxis[0].setCategories(response.distance, false);
                hist.series[0].setData(response.avg_cap, false);
                hist.series[1].setData(response.records, true);
                hist.setTitle(null, { text: site });


        });
        aj1.fail(function (jqXHR, textStatus, errorThrown) {
        });

        aj2 = $.ajax({
                type: "GET",
                url: '{{ path_url_site }}',
                async: true,
                data: { site:site, fromTime:fromTime, toTime:toTime,type:deviceType },
                contentType: "application/json; charset=utf-8",
                dataType: "json"});
        aj2.done(function (response, textStatus, jqXHR) {
            if (response.lat.length > 0) {
                map2.panTo(medLatLng(response.lat, response.lng));
                clearCircles();
                for (i = 0; i < response.cap.length; i++) {
                    addCircle_site(response.lng[i], response.lat[i], response.cap[i], response.time[i])
                }
            }
            else clearCircles();
        });
        aj2.fail(function (jqXHR, textStatus, errorThrown) {
        });
    }
    function lastPointData() {
        refreshIntervalId = window.setInterval(function(){
            var stream = $('#stream').highcharts();
            aj = $.ajax({
                type: "GET",
                url: '{{ lastpoint_url }}',
                async: true,
                data: { site: site, lastTime: lastTime,type:deviceType},
                contentType: "application/json; charset=utf-8",
                dataType: "json"});
            aj.done(function (response, textStatus, jqXHR) {
                var totalPoints = response.cap.length;
                if (totalPoints > 0) {
                    lastTime = response.cap[totalPoints - 1][0];
                }
                for (i = 0; i < totalPoints; i++) {
                    if ((stream.series[0].points.length) <80){
                        stream.series[0].addPoint(response.data[0], false);
                        stream.series[1].addPoint(response.cap[0], false);
                        stream.series[2].addPoint(response.distance[0], true);
                    } else {
                        stream.series[0].addPoint(response.data[0], false, true);
                        stream.series[1].addPoint(response.cap[0], false, true);
                        stream.series[2].addPoint(response.distance[0], true, true);
                    }
                }
            });
            aj.fail(function (jqXHR, textStatus, errorThrown) {
            });
        }, streamInterval);
        }
    function getData() {
        aj = $.ajax({
                type: "GET",
                url: '{{ stream_url }}',
                async: true,
                data: { site:site, type:deviceType },
                contentType: "application/json; charset=utf-8",
                dataType: "json"});
        aj.done(function (response, textStatus, jqXHR) {
                var stream = $('#stream').highcharts();

                stream.series[0].setData(response.data,false);
                stream.series[1].setData(response.cap, false);
                stream.series[2].setData(response.distance,true);
                stream.setTitle(null, { text: site });
        });
        aj.fail(function (jqXHR, textStatus, errorThrown) {
        });

        aj = $.ajax({
                type: "GET",
                url: '{{ chart_url }}',
                async: true,
                data: { site:site, fromTime:fromTime, toTime:toTime,type:deviceType },
                contentType: "application/json; charset=utf-8",
                dataType: "json"});
        aj.done(function (response, textStatus, jqXHR) {
                var chart = $('#chart').highcharts();
                chart.series[0].setData(response.data,false);
                chart.series[1].setData(response.cap,false);
                chart.series[2].setData(response.distance,true);
                chart.setTitle(null, { text: site });
        });
        aj.fail(function (jqXHR, textStatus, errorThrown) {
        });

        aj1 = $.ajax({
                type: "GET",
                url: '{{ histogram_url }}',
                async: true,
                data: { site:site, fromTime:fromTime, toTime:toTime,type:deviceType },
                contentType: "application/json; charset=utf-8",
                dataType: "json"});
        aj1.done(function (response, textStatus, jqXHR) {
                var hist = $('#histogram').highcharts();
                hist.xAxis[0].setCategories(response.distance, false);
                hist.series[0].setData(response.avg_cap, false);
                hist.series[1].setData(response.records, true);
                hist.setTitle(null, { text: site });

        });
        aj1.fail(function (jqXHR, textStatus, errorThrown) {
        });

        aj2 = $.ajax({
                type: "GET",
                url: '{{ path_url }}',
                async: true,
                data: { site:site, fromTime:fromTime, toTime:toTime, type:deviceType },
                contentType: "application/json; charset=utf-8",
                dataType: "json"});
        aj2.done(function (response, textStatus, jqXHR) {
            if (response.lat.length > 0) {
                map2.panTo(medLatLng(response.lat, response.lng));
                clearCircles();
                for (i = 0; i < response.cap.length; i++) {
                    addCircle(response.lng[i], response.lat[i], response.cap[i], response.time[i], response.dist[i],
                    response.cov[i])
                }
            }
            else clearCircles();
        });
        aj2.fail(function (jqXHR, textStatus, errorThrown) {
        });
    }

        $(window).on("blur focus", function(e) {
            var prevType = $(this).data("prevType");

            if (prevType != e.type) {   //  reduce double fire issues
                switch (e.type) {
                    case "blur":
                        // do work
                        break;
                    case "focus":
                            window.location.reload();
                        // do work
                        break;
                }
            }

            $(this).data("prevType", e.type);
        })
function getDataNoStream() {
        aj = $.ajax({
                type: "GET",
                url: '{{ chart_url }}',
                async: true,
                data: { site:site, fromTime:fromTime, toTime:toTime,type:deviceType },
                contentType: "application/json; charset=utf-8",
                dataType: "json"});
        aj.done(function (response, textStatus, jqXHR) {
                var chart = $('#chart').highcharts();
                chart.series[0].setData(response.data,false);
                chart.series[1].setData(response.cap,false);
                chart.series[2].setData(response.distance,true);
                chart.setTitle(null, { text: site });
        });
        aj.fail(function (jqXHR, textStatus, errorThrown) {
        });

        aj1 = $.ajax({
                type: "GET",
                url: '{{ histogram_url }}',
                async: true,
                data: { site:site, fromTime:fromTime, toTime:toTime,type:deviceType },
                contentType: "application/json; charset=utf-8",
                dataType: "json"});
        aj1.done(function (response, textStatus, jqXHR) {
                var hist = $('#histogram').highcharts();
                hist.xAxis[0].setCategories(response.distance, false);
                hist.series[0].setData(response.avg_cap, false);
                hist.series[1].setData(response.records, true);
                hist.setTitle(null, { text: site });

        });
        aj1.fail(function (jqXHR, textStatus, errorThrown) {
        });

        aj2 = $.ajax({
                type: "GET",
                url: '{{ path_url }}',
                async: true,
                data: { site:site, fromTime:fromTime, toTime:toTime, type:deviceType },
                contentType: "application/json; charset=utf-8",
                dataType: "json"});
        aj2.done(function (response, textStatus, jqXHR) {
            if (response.lat.length > 0) {
                map2.panTo(medLatLng(response.lat, response.lng));
                clearCircles();
                for (i = 0; i < response.cap.length; i++) {
                    addCircle(response.lng[i], response.lat[i], response.cap[i], response.time[i], response.dist[i],
                    response.cov[i])
                }
            }
            else clearCircles();
        });
        aj2.fail(function (jqXHR, textStatus, errorThrown) {
        });
    }

   function getDataMarkerNoStream() {
        aj = $.ajax({
                type: "GET",
                url: '{{ chart_url_site }}',
                async: true,
                data: { site:site, fromTime:fromTime, toTime:toTime,type:deviceType },
                contentType: "application/json; charset=utf-8",
                dataType: "json"});
        aj.done(function (response, textStatus, jqXHR) {
                var chart = $('#chart').highcharts();
                chart.series[0].setData(response.data,false);
                chart.series[1].setData(response.cap,false);
                chart.series[2].setData(response.distance, true);
                chart.setTitle(null, { text: site });
        });
        aj.fail(function (jqXHR, textStatus, errorThrown) {
        });

        aj1 = $.ajax({
                type: "GET",
                url: '{{ histogram_url_site }}',
                async: true,
                data: { site:site, fromTime:fromTime, toTime:toTime,type:deviceType },
                contentType: "application/json; charset=utf-8",
                dataType: "json"});
        aj1.done(function (response, textStatus, jqXHR) {
                var hist = $('#histogram').highcharts();
                hist.xAxis[0].setCategories(response.distance, false);
                hist.series[0].setData(response.avg_cap, false);
                hist.series[1].setData(response.records, true);
                hist.setTitle(null, { text: site });
        });
        aj1.fail(function (jqXHR, textStatus, errorThrown) {
        });

        aj2 = $.ajax({
                type: "GET",
                url: '{{ path_url_site }}',
                async: true,
                data: { site:site, fromTime:fromTime, toTime:toTime,type:deviceType },
                contentType: "application/json; charset=utf-8",
                dataType: "json"});
        aj2.done(function (response, textStatus, jqXHR) {
            if (response.lat.length > 0) {
                map2.panTo(medLatLng(response.lat, response.lng));
                clearCircles();
                for (i = 0; i < response.cap.length; i++) {
                    addCircle_site(response.lng[i], response.lat[i], response.cap[i], response.time[i])
                }
            }
            else clearCircles();
        });
        aj2.fail(function (jqXHR, textStatus, errorThrown) {
        });
    }
    $('#datetimepicker1').datetimepicker({
              format:'unixtime',
              inline:true,
              scrollMonth:false,
              scrollTime:false,
              onChangeDateTime:function(dp,$input){
                 tempTime = Number($input.val()*1000);
                 if (tempTime != toTime) {
                      fromTime = tempTime;
                 }
                }
            });
    $('#datetimepicker2').datetimepicker({
              format:'unixtime',
              inline:true,
              scrollMonth:false,
              scrollTime:false,
              onChangeDateTime:function(dp,$input){
                 tempTime = Number($input.val()*1000);
                 if (tempTime != fromTime) {
                      toTime = tempTime;
                 }
              }
            });

 $('#bigbutton').click(function () {
         if (onSite) {
                window.clearInterval(refreshIntervalIdSite);
                getDataMarkerNoStream();
                lastPointDataMarker();
            } else {
                window.clearInterval(refreshIntervalId);
                getDataNoStream();
                lastPointData();
            }
    });

    $(function() {
        firstMap();
        secondMap();
        Highcharts.setOptions({
            global : {
                useUTC : false
            }
        });
        var streamOptions = {

                chart: {
                 //   zoomType: 'x',
                    events : {
                        load : function () { if (onSite) {lastPointDataMarker();}else{lastPointData();} }
                    }
                },
                title: {
                    text: 'Streaming Traffic, Capacity, Distance'
                },
                subtitle: {
                    text: site
                },
                xAxis: {
                    type: 'datetime',
                    minRange: 1000, // 15 s
                    tickInterval: 10000  // 10s
                },
                yAxis: [
                        { // Tertiary yAxis
                        gridLineWidth: 0,
                        title: {
                            text: 'Distance',
                            style: {
                                color: Highcharts.getOptions().colors[2]
                            }
                        },
                        labels: {
                            format: '{value} miles',
                            style: {
                                color: Highcharts.getOptions().colors[2]
                            }
                        },
                        opposite: false,
                        floor:0
                    },{ // Primary yAxis
                        labels: {
                            format: '{value}Mbps',
                            style: {
                                color: Highcharts.getOptions().colors[0]
                            }
                        },
                        title: {
                            text: 'Traffic, Capacity',
                            style: {
                                color: Highcharts.getOptions().colors[0]
                            }
                        },
                        opposite: true,
                        floor:0

                    }],
                tooltip: {
                    shared: true,
                    valueDecimals: 2,
                    formatter: function () {
                        var s = '<b>' + Highcharts.dateFormat('%A, %b %e, %Y, %H:%M:%S', this.x) + '</b>';
                        index=0;
                        $.each(this.points, function (index) {
                            if (index == 0) {
                                s += '<br/><span style="color:#6EA3ED; font-weight:bold;"> Traffic: ' + this.y + '  Mbps';
                            }
                            if (index == 1) {

                                s += '<br/><span style="color:#333338; font-weight:bold;"> Capacity: ' + this.y + '  Mbps';
                            }
                            if (index == 2) {
                                s += '<br/><span style="color:#88EF57; font-weight:bold;"> Distance: ' + this.y + '  miles';
                            }
                            if (index <2) {
                                index = +1;
                            } else {
                                index = 0;
                            }
                        });
                        return s;
                    }

                },
                exporting: false,
                credits: false,
                legend: {
                    layout: 'vertical',
                    align: 'left',
                    x: 120,
                    verticalAlign: 'top',
                    y: 80,
                    floating: true,
                    backgroundColor: (Highcharts.theme && Highcharts.theme.legendBackgroundColor) || '#FFFFFF'
                },
                series:[{
                    name: 'Traffic',
                    type: 'spline',
                    yAxis:1,
                    data: stream_data,
                    dashStyle: 'shortdot',
                    tooltip: {
                        valueSuffix: ' Mbps'
                    }
                },
                    {
                    name: 'Capacity',
                    type: 'spline',
                    yAxis:1,
                    data: stream_cap,
                    tooltip: {
                        valueSuffix: ' Mbps'
                    }
                }, {
                    name: 'Distance',
                    type: 'spline',
                    yAxis: 0,
                    data: stream_distance,
                    marker: {
                        enabled: false
                    },
                    tooltip: {
                        valueSuffix: ' miles'
                    }

                }]
            };
        var chartOptions = {
             //   chart: {
               //     zoomType: 'x'
             //   },
                title: {
                    text: 'Traffic, Capacity, Distance'
                },
                subtitle: {
                    text: site
                },
                xAxis: {
                    type: 'datetime',
                    minRange: 60000, // 1 min
                    tickInterval: 120000  // 2 min
              //     events: {
              //          afterSetExtremes: afterSetExtremes
              //      }
                },
                yAxis: [
                    { // Tertiary yAxis
                    gridLineWidth: 0,
                    title: {
                        text: 'Distance',
                        style: {
                            color: Highcharts.getOptions().colors[2]
                        }
                    },
                    labels: {
                        format: '{value} miles',
                        style: {
                            color: Highcharts.getOptions().colors[2]
                        }
                    },
                    opposite: false,
                    floor:0
                },{ // Primary yAxis
                    labels: {
                        format: '{value}Mbps',
                        style: {
                            color: Highcharts.getOptions().colors[0]
                        }
                    },
                    title: {
                        text: 'Traffic, Capacity',
                        style: {
                            color: Highcharts.getOptions().colors[0]
                        }
                    },
                    opposite: true,
                    floor:0

                }],
                tooltip: {
                    shared: true,
                    valueDecimals: 2,
                    formatter: function () {
                        var s = '<b>' + Highcharts.dateFormat('%A, %b %e, %Y, %H:%M:%S', this.x) + '</b>';
                        index=0;
                        $.each(this.points, function (index) {
                            if (index == 0) {
                                s += '<br/><span style="color:#6EA3ED; font-weight:bold;"> Traffic: ' + this.y + '  Mbps';
                            }
                            if (index == 1) {
                                s += '<br/><span style="color:#333338; font-weight:bold;"> Capacity: ' + this.y + '  Mbps';
                            }
                            if (index == 2) {
                                s += '<br/><span style="color:#88EF57; font-weight:bold;"> Distance: ' + this.y + '  miles';
                            }
                            if (index <2) {
                                index = +1;
                            } else { index = 0;
                            }
                        });
                        return s;
                    }

                },
                exporting: false,
                credits: false,
                legend: {
                    layout: 'vertical',
                    align: 'left',
                    x: 120,
                    verticalAlign: 'top',
                    y: 80,
                    floating: true,
                    backgroundColor: (Highcharts.theme && Highcharts.theme.legendBackgroundColor) || '#FFFFFF'
                },
                series:[{
                    name: 'Traffic',
                    type: 'spline',
                    yAxis:1,
                    data: data_data,
                    dashStyle: 'shortdot',
                    tooltip: {
                        valueSuffix: ' Mbps'
                    }
                },
                    {
                    name: 'Capacity',
                    type: 'spline',
                    yAxis:1,
                    data: data_cap,
                    tooltip: {
                        valueSuffix: ' Mbps'
                    }
                },
                    {
                    name: 'Distance',
                    type: 'spline',
                    yAxis: 0,
                    data: data_distance,
                    marker: {
                        enabled: false
                    },
                    tooltip: {
                        valueSuffix: ' miles'
                    }

                }]
            };
        var histOptions = {
                title: {
                    text: 'Capacity vs Distance'
                },
                subtitle: {
                    text: site
                },
                navigator: {
                    enabled: false
                },
                rangeSelector : {
                    enabled: false
                },
                xAxis: [{
                    categories: hist_distance
                    },{
                    title: {
                        text: 'Distance',
                        style: {
                            color: Highcharts.getOptions().colors[3]
                        }
                    }
                }],
                yAxis: [{ // Primary yAxis

                    title: {
                        text: 'Capacity',
                        style: {
                            color: Highcharts.getOptions().colors[0]
                        }
                    },
                    labels: {
                        format: '{value} Mbps',
                        style: {
                            color: Highcharts.getOptions().colors[0]
                        }
                    },
                    opposite: true

                }, { // Secondary yAxis
                    gridLineWidth: 0,
                    title: {
                        text: 'Frequency',
                        style: {
                            color: Highcharts.getOptions().colors[1]
                        }
                    },
                    labels: {
                        format: '{value} %',
                        style: {
                            color: Highcharts.getOptions().colors[1]
                        }
                    }

                }],
                tooltip: {
                    shared: true,
                    valueDecimals: 2,
                    formatter: function () {
                        var s = '<span style="color:#88EF57; font-weight:bold;"> Distance: ' + this.x + '  miles';
                        index=0;
                        $.each(this.points, function (index) {
                            if (index == 0) {
                                s += '<br/><span style="color:#6EA3ED; font-weight:bold;"> Traffic: ' + this.y + '  Mbps';
                            }
                            if (index == 1) {
                                s += '<br/><span style="color:#333338; font-weight:bold;"> Capacity: ' + this.y + '  Mbps';
                            }
                            if (index <1) {
                                index = +1;
                            } else { index = 0;
                            }
                        });
                        return s;
                    }

                },
                exporting: false,
                credits: false,
                legend: {
                    layout: 'vertical',
                    align: 'left',
                    x: 120,
                    verticalAlign: 'top',
                    y: 80,
                    floating: true,
                    backgroundColor: (Highcharts.theme && Highcharts.theme.legendBackgroundColor) || '#FFFFFF'
                },
                series: [
                    {
                    name: 'Capacity',
                    type: 'column',
                    yAxis: 0,
                    data: hist_cap,
                }, {
                    name: 'Frequency',
                    type: 'column',
                    yAxis: 1,
                    data: hist_freq,
                    marker: {
                        enabled: false
                    },
                }]
            };
        $('#stream').highcharts(streamOptions);
        $('#chart').highcharts(chartOptions);
        $('#histogram').highcharts(histOptions);
        window.setInterval(function() {
              loadDevicesAndLinks();
            }, updateInterval);
    });

