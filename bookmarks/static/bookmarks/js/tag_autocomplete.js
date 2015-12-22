$(function(){
    $("#id_tags").autocomplete({
        source: '/ajax/tag/autocomplete/',
    });
});