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
      var bikeCount;
      marker_icon = new google.maps.MarkerImage(
        "https://s3.amazonaws.com/penncycle/img/PennCycle Logo 3 smallest-03.png", 
        undefined, undefined, undefined, 
        new google.maps.Size(50, 50)
      );
      empty_icon = new google.maps.MarkerImage(
        "https://s3.amazonaws.com/penncycle/img/empty_station.png", 
        undefined, undefined, undefined, 
        new google.maps.Size(50, 50)
      );
      for (var j = stations.length - 1; j >= 0; j--) {
        station = stations[j];
        lng = station.longitude;
        lat = station.latitude;
        pos = new google.maps.LatLng(lat, lng);

        content_string = station.name + ": ";
        bikeCount = 0;

        for (var k = available_bikes.length - 1; k >= 0; k--) { 
          var this_bike = available_bikes[k];
          if (this_bike.location == station.name) { 
            content_string += this_bike.name.toString() + " ";
            bikeCount++;
          } 
        }
        if (bikeCount != 0) { 
          icon = marker_icon;
        } else { 
          icon = empty_icon;
        }
        var marker = new MarkerWithLabel({
          position: pos,
          map: map,
          icon: marker_icon,
          labelContent: station.name,
          labelClass: "marker"
        });
        if (bikeCount != 0) { 
          bindInfoWindow(marker, map, infoWindow, content_string);
        } else { 
          bindInfoWindow(marker, map, infoWindow, "No available bikes");
        }
      }
    });
  });
  function bindInfoWindow(marker, map, infowindow, strDescription) {
    google.maps.event.addListener(marker, 'mouseover', function() {
        infowindow.setContent('<div class="scrollFix">' + strDescription + '</div>');
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
