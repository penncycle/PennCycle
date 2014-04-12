$(document).ready(function() {
  var map_options = {
    center: new google.maps.LatLng(39.951600,-75.197794),
    zoom: 17,
    mapTypeId: google.maps.MapTypeId.ROADMAP,
    zoomControl: true 
  };
  var station_counts = {};
  var map = new google.maps.Map(document.getElementById("map"), map_options);
  $.getJSON("/mobile/bike_data/", function(bikes) {
    for (var i = bikes.length - 1; i >= 0; i--) {
      bike = bikes[i];
      if (bike.status == "available") {
        lat = bike.latitude - 0.0002;
        lng = bike.longitude - 0.0001;
        station = bike.location;
        if (station_counts[station]) {
          lng += 0.0002 * (station_counts[station] % 5);
          lat -= 0.0002 * Math.floor(station_counts[station] / 5);
          station_counts[station] += 1;
        } else {
          station_counts[station] = 1;
        }
        pos = new google.maps.LatLng(lat, lng);
        var marker = new MarkerWithLabel({
          position: pos,
          map: map,
          icon: "https://s3.amazonaws.com/penncycle/img/bike_icon.png",
          labelContent: bike.name,
          labelClass: "marker"
        });
      }
    }
  });
  $.getJSON("/mobile/station_data/", function(stations) {
    for (var i = stations.length - 1; i >= 0; i--) {
      station = stations[i];
      lng = station.longitude;
      lat = station.latitude;
      pos = new google.maps.LatLng(lat, lng);
      var marker = new MarkerWithLabel({
        position: pos,
        map: map,
        icon: "https://s3.amazonaws.com/penncycle/img/station_icon.png",
        labelContent: station.name,
        labelClass: "marker"
      });
    }
  });
});
