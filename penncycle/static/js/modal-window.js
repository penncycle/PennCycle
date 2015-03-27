$modal = (function() {
        var
        method = {},
        $overlay,
        $content,
        $close,
        $modal

        method.center = function() {
            var top, left;
            top = Math.max($(window).height() - $modal.outerHeight(), 0)/2;
            left = Math.max($(window).width() - $modal.outerWidth(), 0)/2;


            $modal.css({
               top: top + $(window).scrollTop(),
               left: left + $(window).scrollLeft()
               
            });

        };


        method.open = function(settings) {
            $content.empty().append(settings.content);
            $modal.css({
                width: settings.width || 'auto',
                height: settings.height || 'auto'
            });
            method.center();
            $(window).bind('resize.modal', method.center);

            $modal.show();
            $overlay.show();
           


        };

        method.close = function() {
            $content.empty();
            $modal.hide();
            $overlay.hide();
            $(window).unbind('resize.modal');
            location.reload();
        };


        $overlay = $('<div class="overlay_mymodal"></div>');
        $modal = $('<div class="mymodal"></div>');
        $content = $('<div class="content_mymodal"></div>');
        $close = $('<a class="close_mymodal" href="#">close</a>');
        $modal.append($content, $close);
        $overlay.hide();
        $modal.hide();

        $(document).ready(function() {
            $("body").append($overlay, $modal);
    
        });
      
        $close.click(function(e) {
            e.preventDefault();
            method.close();
        });
            
        return method;

    }());