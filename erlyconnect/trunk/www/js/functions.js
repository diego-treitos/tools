
function notify( data ) {
    if (data.status==0)
    {
        if ($("#note").hasClass("error")) {
            $("#note").removeClass("error");
        }
        $("#note").addClass("ok");
    } else {
        if ($("#note").hasClass("ok")) {
            $("#note").removeClass("ok");
        }
        $("#note").addClass("error");
    }
    $("#note").text(data["message"])
    $("#note").fadeIn('slow')
    setTimeout( function() {
            $("#note").fadeOut('slow')
            }, 8000 )
}

function refreshControls() {
    $.getJSON("/json/info", function(info) {
        if (info.started) {
            if ($("#start_toggle").hasClass("start")) {
                $("#start_toggle").removeClass("start");
            }
            $("#start_toggle").addClass("stop");
        } else {
            if ($("#start_toggle").hasClass("stop")) {
                $("#start_toggle").removeClass("stop");
            }
            $("#start_toggle").addClass("start");
        }
        $("#parent").val(info.parent);
        $("#son").val(info.son);
        $("#refresh_time").val(info.refresh_time);
        $("#mode").val(info.mode);
    })
}

function showErrors() {
        $.getJSON("/json/geterrors",
                function( data ) {
                if (data) {
                    notify({
                        "status":1,
                        "message":data
                        })
                    }
                });
        setTimeout( showErrors, 5000 )
}

function showStreams() {
        $.getJSON("/json/getstreams",
                function( data ) {
                    var l = String();
                    $.each(data, function(i,item){
                        if (item.started) {
                            l+='<li class="started"><button id="'+item.name+'" class="ministop"/>'+item.name+'</li>'
                        } else {
                            l+='<li class="stopped"><button id="'+item.name+'" class="ministart"/>'+item.name+'</li>'
                        }
                        })
                    $('#streams').html(l)
                    $(".ministop").click(function(){
                            manageStream("stop",this.id) 
                            });
                    $(".ministart").click(function(){
                            manageStream("start",this.id) 
                            });
                });
        setTimeout( showStreams, 3000 )
}

function manageStream(action,s_name) {
        $.getJSON("/manage",
            {
                "action":action,
                "name":s_name
                },
                function( data ) {
                    notify(data);
                });
}
