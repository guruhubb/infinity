/*!
 * Start Bootstrap - Agnecy Bootstrap Theme (http://startbootstrap.com)
 * Code licensed under the Apache License v2.0.
 * For details, see http://www.apache.org/licenses/LICENSE-2.0.
 */

// jQuery for page scrolling feature - requires jQuery Easing plugin
$(function() {
    $('a.page-scroll').bind('click', function(event) {
        var $anchor = $(this).attr('href');
        // get target div to scroll to

        var target;
        if ($anchor && $anchor.attr()) {
            target = $($anchor.attr('href'));
            // if target is valid, scroll to
            if (target && target.offset()) {
                $('html, body').stop().animate({
                    scrollTop: target.offset().top
                }, 1500, 'easeInOutExpo');
            }
        }
//        $('html, body').stop().animate({
//            scrollTop: $($anchor.attr('href')).offset().top
//        }, 1500, 'easeInOutExpo');
        event.preventDefault();
    });
});

// Highlight the top nav as scrolling occurs
$('body').scrollspy({
    target: '.navbar-fixed-top'
})

// Closes the Responsive Menu on Menu Item Click
$('.navbar-collapse ul li a').click(function() {
    $('.navbar-toggle:visible').click();
});