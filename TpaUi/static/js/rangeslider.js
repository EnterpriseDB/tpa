$(function() {
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    $('.slider-block').each(function () {
        start = $(this).find('.hours-start').val();
        end = $(this).find('.hours-end').val();
        day_id = $(this).find('.hours-weekday').val();
        hidden_slider = $('#slider-block-hidden').clone();
        $(this).append(hidden_slider.find('.slider-end').text(end));
        $(this).append((slider = hidden_slider.find('.slider')));
        $(this).append(hidden_slider.find('.slider-start').text(start));
        $(this).append(hidden_slider.find('.slider-day').text(days[day_id]));
        slider.slider({
            orientation: "vertical",
            range: true,
            min: 0,
            max: 1440,
            step: 15,
            values: [ ttm(start), ttm(end) ],
            slide: function( event, ui ) {
                $(this).siblings('.slider-start').text(mtt(ui.values[0]));
                $(this).siblings('.slider-end').text(mtt(ui.values[1]));
            }
        });
    });
});