var EventRegistry = []

var Router = {
    showPage:function(id){
        $('.page').hide();
        $('#'+ id).show();

        $('.nav li').removeClass('active');
        var li = $('#'+ id).data('active-menu-item');
        $('#'+ li).addClass('active');
    }

}

var User = {
    updateDetails:function(){
        $.getJSON('/user', function(json){
            $('#pendingFunds').html('£'+json.pendingFunds);
            $('#totalFunds').html('£'+json.totalFunds);
            $('#usernameContainer').html(json.username);
        })        
    },

    logout:function(params, callback){
        $.get('/logout', function(json){
            window.location = '/frontend/login.html';
        })
    },

    attachEvents:function(){
        var self = this;

        if(EventRegistry.indexOf("logoutLink") == -1){            
            EventRegistry.push("logoutLink");

            $('#logoutLink').on('click', function(ev){
                ev.preventDefault();

                self.logout();
            })
        }
    }
}

var Odds = {
    odds:null,

    getDropdown:function(callback){

        if(!this.odds){
            var self = this;

            $.getJSON('/odds', function(json){
                self.odds = json;

                self.getDropdown(callback);
            })
        } else {
            var html = Util.Html.select({
                name:'odds[]',
                content:this.odds,
                valueKey:'_id',
                nameKey:'name',
            });

            callback(html);
        }
    }
}

var Community = {
    dropdown:null,

    getAll:function(callback){
        var self = this;

        $.getJSON('/communities', function(json){
            Util.Templating.renderTemplate('communityListTpl', {'communities':json}, 'communityListContainer');

            if(callback) callback();
        })
    },

    getDropdown:function(callback){

        if(!this.dropdown){
            var self = this;

            $.getJSON('/communities', function(json){
                
                self.dropdown = [{
                    '_id':0,
                    'name':'Public'
                }];

                $.each(json, function(i, el){
                    self.dropdown.push(el);
                })

                self.getDropdown(callback);
            })
        } else {
            var html = Util.Html.select({
                id:'inputCommunity',
                name:'communityId',
                content:this.dropdown,
                valueKey:'_id',
                nameKey:'name',
            });

            callback(html);
        }
    },

    save:function(params, callback){
        $.post('/community', params, function(){
            if(callback) callback();
        })
    },

    attachEvents:function(){
        var self = this;

        if(EventRegistry.indexOf("formAddCommunity") == -1){            
            EventRegistry.push('formAddCommunity');

            $('#formAddCommunity').on('submit', function(ev){
                ev.preventDefault();

                var params = $(this).serialize();

                self.save(params, function(){
                    window.location = '/frontend/index.html#/communities';
                });

            })
        }
    }
}

var Event = {
    choicesContent:null,

    getAll:function(callback){
        var self = this;

        $.getJSON('/event', function(json){
            Util.Templating.renderTemplate('eventListTpl', {'events':json}, 'events');

            if(callback) callback();
        })
    },

    getOne:function(eventId, callback){
        var self = this;

        $.getJSON('/event/'+ eventId, function(json){
            Util.Templating.renderTemplate('eventTpl', json, 'singleEventContainer');

            if(callback) callback();
        })
    },

    save:function(params, callback){
        $.post('/event/save', params, function(json){
            if(callback) callback(json);
        })
    },

    addChoice:function(){
        if(!this.choicesContent) this.choicesContent = $('#choicesContent').html();

        $('#choicesContainer').append(Util.Html.div({content:this.choicesContent}));
    },

    placeBet:function(params, callback){
        $.post('/bet/add', params, function(json){
            if(callback) callback(json);
        })
    },

    attachEvents:function(){
        var self = this;

        var eventName = "formAddEvent";

        if(EventRegistry.indexOf(eventName) == -1){            
            EventRegistry.push(eventName);

            $('.datepicker').datepicker().datepicker('option', 'dateFormat', 'dd/mm/yy');

            $('#formAddEvent').on('submit', function(ev){
                ev.preventDefault();

                var params = $(this).serialize();

                self.save(params, function(json){
                    if(json.success==1){
                        window.location = '/frontend/index.html';
                    } else {
                        Util.flashMessage('error', json.error);
                    }
                });

            })
        }

        if(EventRegistry.indexOf('addChoiceAnchor') == -1){            
            EventRegistry.push('addChoiceAnchor');

            $('#addChoiceAnchor').on('click', function(ev){
                ev.preventDefault();
                self.addChoice();
            })
        }

        if(EventRegistry.indexOf('formAddBet') == -1){            
            EventRegistry.push('formAddBet');

            $('#formAddBet').on('submit', function(ev){
                ev.preventDefault();

                var params = $(this).serialize();

                self.placeBet(params, function(json){
                    if(json.success==1){
                        window.location = '/frontend/index.html';
                    } else {
                        Util.flashMessage('error', json.error);
                    }
                });

            })
        }
    }
}



var Result = {

    getAll:function(callback){
        var self = this;

        $.getJSON('/result', function(json){
            Util.Templating.renderTemplate('resultListTpl', {'results':json}, 'results');

            if(callback) callback();
        })
    },

    getOne:function(eventId, callback){
        var self = this;

        $.getJSON('/event/'+ eventId, function(json){
            Util.Templating.renderTemplate('eventResultTpl', json, 'singleResultContainer');

            if(callback) callback();
        })
    },

    getEventDetails:function(eventId, callback){
        var self = this;

        $.getJSON('/event/'+ eventId, function(json){
            Util.Templating.renderTemplate('resultTpl', json, 'singleEventResultContainer');

            if(callback) callback(json);
        })
    },

    save:function(eventId, params, callback){
        $.post('/event/'+eventId+'/result/add', params, function(json){
            if(callback) callback(json);
        })
    },

    attachEvents:function(){
        var self = this;

        var eventName = "formAddResult";

        if(EventRegistry.indexOf(eventName) == -1){            
            EventRegistry.push(eventName);

            $('#formAddResult').on('submit', function(ev){
                ev.preventDefault();

                var params = Util.querystringToObject( $(this).serialize() );

                self.save(params.eventId, params, function(json){
                    if(json.success==1){
                        window.location = '/frontend/index.html';
                    } else {
                        Util.flashMessage('error', json.error);
                    }
                });

            })
        }

    }
}


$(document).ajaxError(function(event, jqxhr){
    if(jqxhr.status == 403){
        window.location = '/frontend/login.html';
    } else {
        Util.flashMessage('error', 'An error has occured');
    }
})

$(document).ready(function(){
    User.updateDetails();
    User.attachEvents();
});

Path.map("#/home").to(function(){
    Event.getAll();
    Router.showPage('pageHome');
});

Path.map("#/results").to(function(){
    Result.getAll();
    Router.showPage('pageResults');
});

Path.map("#/result/:id").to(function(){
    Result.getOne(this.params["id"], function(){        
        Router.showPage('pageSingleResult');
    });
});

Path.map("#/event/add").to(function(){
    Event.attachEvents();

    Odds.getDropdown(function(html){
        $('#oddsContainer').html(html);
    })

    Community.getDropdown(function(html){
        $('#communitiesContainer').html(html);
    })

    Router.showPage('pageAddEvent');
});

Path.map("#/event/:id").to(function(){
    Event.getOne(this.params["id"], function(){
        Event.attachEvents();   
        
        Router.showPage('pageSingleEvent');
    });
});

Path.map("#/event/:id/result/add").to(function(){
    Result.getEventDetails(this.params["id"], function(){        
        Router.showPage('pageSingleEventResult');
        Result.attachEvents();
    });
});

Path.map("#/communities").to(function(){
    Community.getAll();
    Router.showPage('pageCommunities');
});

Path.map("#/community").to(function(){
    Community.attachEvents();

    Router.showPage('pageAddCommunity');
});


Path.root("#/home");

Path.listen();
