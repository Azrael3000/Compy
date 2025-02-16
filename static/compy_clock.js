$(document).ready(function() {

    function updateTime() {
        let time = new Date();
        $('#time').text(time.toLocaleTimeString());
        window.requestAnimationFrame(updateTime);
    };

    updateTime();
});
