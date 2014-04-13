$(document).ready(function() {

  var map_options = {
    center: new google.maps.LatLng(39.951600,-75.197794),
    zoom: 16,
    mapTypeId: google.maps.MapTypeId.ROADMAP,
    zoomControl: true,
    scrollwheel: false
  };

  var station_counts = {};
  var map = new google.maps.Map(document.getElementById("map"), map_options);
  var infoWindow = null;      

  $.getJSON("/mobile/station_data/", function(stations) {
    $.getJSON("/mobile/bike_data/", function(bikes) {
      var available_bikes = new Array();
      var curr;
      for (var i = bikes.length - 1; i >= 0; i--) { 
        curr = bikes[i];
        if (curr.status == "available" || curr.status == "Available") { 
          available_bikes.push({name:curr.name, location:curr.location});
        }
      }
      infoWindow = new google.maps.InfoWindow({
        content: "loading..."
      });    
      var content_string = " ";  
      for (var j = stations.length - 1; j >= 0; j--) {
        station = stations[j];
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
        content_string = "Available bikes: ";
        var hasBike = false;
        for (var k = available_bikes.length - 1; k >= 0; k--) { 
          var this_bike = available_bikes[k];
          if (this_bike.location == station.name) { 
            content_string += this_bike.name.toString() + " ";
            hasBike = true;
          } 
        }
        if (hasBike) { 
          bindInfoWindow(marker, map, infoWindow, content_string);
        } else { 
          bindInfoWindow(marker, map, infoWindow, "Available bikes: none");
        }
      }
    });
  });

  function bindInfoWindow(marker, map, infowindow, strDescription) {
    google.maps.event.addListener(marker, 'mouseover', function() {
        infowindow.setContent(strDescription);
        infowindow.open(map, marker);
    });  
  }
  // $.getJSON("/mobile/bike_data/", function(bikes) {
  //   for (var i = bikes.length - 1; i >= 0; i--) {
  //     bike = bikes[i];
  //     if (bike.status == "available" || bike.status == "Available") {
  //       available_bikes.push({
  //         name:bike.name,
  //         location:bike.location
  //       });        

  //       lat = bike.latitude - 0.0002;
  //       lng = bike.longitude - 0.0001;
  //       station = bike.location;
  //       if (station_counts[station]) {
  //         lng += 0.0002 * (station_counts[station] % 5);
  //         lat -= 0.0002 * Math.floor(station_counts[station] / 5);
  //         station_counts[station] += 1;
  //       } else {
  //         station_counts[station] = 1;
  //       }
  //       pos = new google.maps.LatLng(lat, lng);
  //       var marker = new MarkerWithLabel({
  //         position: pos,
  //         map: map,
  //         icon: "https://s3.amazonaws.com/penncycle/img/bike_icon.png",
  //         labelContent: bike.name,
  //         labelClass: "marker"
  //       }); 
  //     }
  //   }
  // });
});
