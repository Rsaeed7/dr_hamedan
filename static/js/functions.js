(function ($) {

	"use strict";

	// Preload
    $(window).on("load", function (){  // makes sure the whole site is loaded
		'use strict';
		$('[data-loader="circle-side"]').fadeOut(); // will first fade out the loading animation
		$('#preloader').delay(350).fadeOut('slow'); // will fade out the white DIV that covers the website.
		$('body').delay(350).css({
			'overflow': 'visible'
		});
		var $hero= $('.hero_home .content');
		var $hero_v= $('#hero_video .content ');
		$hero.find('h3, p, form').addClass('fadeInUp animated');
		$hero.find('.btn_1').addClass('fadeIn animated');
		$hero_v.find('.h3, p, form').addClass('fadeInUp animated');
		$(window).scroll();
	})

	// Sticky nav + scroll to top
	var $headerStick = $('.header_sticky');
	var $toTop = $('#toTop');
	$(window).on("scroll", function () {
		if ($(this).scrollTop() > 1) {
			$headerStick.addClass("sticky");
		} else {
			$headerStick.removeClass("sticky");
		};
		if ($(this).scrollTop() != 0) {
			$toTop.fadeIn();
		} else {
			$toTop.fadeOut();
		}
	});
	$toTop.on("click", function () {
		$('body,html').animate({
			scrollTop: 0
		}, 500);
	});


	var $headerStick = $('.header_sticky');
	var $online_visit = $('#online_visit');
	$(window).on("scroll", function () {
		if ($(this).scrollTop() > 1) {
			$headerStick.addClass("sticky");
		} else {
			$headerStick.removeClass("sticky");
		}
		;
		if ($(this).scrollTop() == 0) {
			$online_visit.fadeIn();
		} else {
			$online_visit.fadeOut();
		}
	});
	// Menu
	$('a.open_close').on("click", function () {
		$('.main-menu').toggleClass('show');
		$('.layer').toggleClass('layer-is-visible');
		$('header.static').toggleClass('header_sticky sticky');
		$('body').toggleClass('body_freeze');
	});
	$('a.show-submenu').on("click", function () {
		$(this).next().toggleClass("show_normal");
	});


	function toggleHandler(toggle) {
		toggle.addEventListener("click", function (e) {
			e.preventDefault();
			(this.classList.contains("active") === true) ? this.classList.remove("active"): this.classList.add("active");
		});
	};

	// WoW - animation on scroll
	var wow = new WOW({
		boxClass: 'wow',
		animateClass: 'animated',
		offset: 0, //
		mobile: true,
		live: true,
		callback: function (box) {


		},
		scrollContainer: null
	});
	wow.init();



	// Selectbox
	$(".selectbox").selectbox();


	$("#results").stick_in_parent({
		offset_top: 0
	});


	$('#sidebar').theiaStickySidebar({
		additionalMarginTop: 95
	});


	$('[data-toggle="tooltip"]').tooltip();

		
		var $sticky_nav= $('#secondary_nav');
		$sticky_nav.stick_in_parent();
		$sticky_nav.find('ul li a').on('click', function(e) {
			e.preventDefault();
			var target = this.hash;
			var $target = $(target);
			$('html, body').animate({
				'scrollTop': $target.offset().top - 95
			}, 800, 'swing');
		});
		$sticky_nav.find('ul li a').on('click', function() {
		$sticky_nav.find('.active').removeClass('active');
		$(this).addClass('active');
		});
	

	// Accordion
	function toggleChevron(e) {
		$(e.target)
			.prev('.card-header')
			.find("i.indicator")
			.toggleClass('icon_minus_alt2 icon_plus_alt2');
	}
	$('.accordion').on('hidden.bs.collapse shown.bs.collapse', toggleChevron);
		function toggleIcon(e) {
        $(e.target)
            .prev('.panel-heading')
            .find(".indicator")
            .toggleClass('icon_minus_alt2 icon_plus_alt2');
    }
    $('.panel-group').on('hidden.bs.collapse', toggleIcon);
    $('.panel-group').on('shown.bs.collapse', toggleIcon);


})(window.jQuery);


