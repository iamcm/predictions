import random
import json
import datetime
import os 
import bottle
import settings
from bson import ObjectId
from db import _DBCON
from models import Util
from models.EntityManager import EntityManager
from models.Session import Session
from models.Email import Email
from models import Logger
from models.Models import Event, Choice, Bet, Odds, PredictionsUser, Community, User4Community



def checklogin(callback):
    def wrapper(*args, **kwargs):
        if bottle.request.get_cookie('token') or bottle.request.GET.get('token'):
            token = bottle.request.get_cookie('token') or bottle.request.GET.get('token')
            
            s = Session(_DBCON, publicId=token)
            if not s.valid or not s.check(bottle.request.get('REMOTE_ADDR'), bottle.request.get('HTTP_USER_AGENT')):
                return bottle.HTTPError(403, 'Access denied')
                
            else:
                bottle.request.session = s
                return callback(*args, **kwargs)
        else:
            return bottle.HTTPError(403, 'Access denied')
    return wrapper


def JSONResponse(callback):
    def wrapper(*args, **kwargs):
        bottle.response.content_type = 'text/json'
        return callback(*args, **kwargs)
    return wrapper


# static files
if settings.PROVIDE_STATIC_FILES:
    @bottle.route('/frontend/<filepath:path>')
    def index(filepath):
        return bottle.static_file(filepath, root=settings.ROOTPATH +'/frontend/')




# auth
def loginUser(userId):
    s = Session(_DBCON)
    s.userId = userId
    s.ip = bottle.request.get('REMOTE_ADDR')
    s.userAgent = bottle.request.get('HTTP_USER_AGENT')
    s.save()

    return s.publicId


@bottle.route('/login', method='POST')
@JSONResponse
def index():
    e = bottle.request.POST.get('email')
    p = bottle.request.POST.get('password')

    if e and p:
        u = PredictionsUser(_DBCON, email=e, password=p)

        if u._id and u.valid:
            loginUser(u._id)

            output = {'success':1}
        else:
            output = {
                'success':0,
                'error':'Login failed'
            }
    else:
        output = {
            'success':0,
            'error':'Login failed'
        }

    return json.dumps(output)



@bottle.route('/logout', method='GET')
@checklogin
def index():
    s = bottle.request.session
    s.destroy()
    
    return ''



@bottle.route('/register', method='POST')
@JSONResponse
def index():
    u = bottle.request.POST.get('username')
    e = bottle.request.POST.get('email')
    p = bottle.request.POST.get('password')
    p2 = bottle.request.POST.get('password2')

    error = None
    if u and e and p and p2:
        #recaptcha
        import requests

        response = requests.post('http://www.google.com/recaptcha/api/verify', data={
                'privatekey':'6LdPzuISAAAAANt0LHSTxwbZX2vUjePhLG41SiyQ',
                'remoteip':bottle.request.get('REMOTE_ADDR'),
                'challenge':bottle.request.POST.get('recaptcha_challenge_field'),
                'response':bottle.request.POST.get('recaptcha_response_field'),
            })

        if p != p2:
            error = 'Passwords do not match'

        elif EntityManager(_DBCON).get_all(PredictionsUser, filter_criteria={'username':u}, count=True) > 0:
            error = 'Username is already taken'

        elif EntityManager(_DBCON).get_all(PredictionsUser, filter_criteria={'email':e}, count=True) > 0:
            error = 'There is already an account registered to this email address'

        elif response.text.split('\n')[0] != 'true':
            failures = {
                'incorrect-captcha-sol':'The CAPTCHA solution was incorrect',
            }
            error = failures.get(response.text.split('\n')[1], 'An error has occurred')

        else:
            user = PredictionsUser(_DBCON)
            user.email = e
            user.password = p
            user.username = u
            user.valid = True
            user.save(newPassword=True)

            loginUser(user._id)

    else:
        error = 'Required data is missing'


    if not error:
        output = {'success':'1'}
    else:
        output = {
            'success':0,
            'error':error
            }

    return json.dumps(output)





#######################################################
# Main app routes
#######################################################
@bottle.route('/')
@checklogin
def index():
    return bottle.template('index')


@bottle.route('/event')
@checklogin
@JSONResponse
def index():

    if bottle.request.GET.get('communityId') \
        and EntityManager(_DBCON).get_all(User4Community, filter_criteria={
                                            'user._id':bottle.request.session.userId,
                                            'communityId':bottle.request.GET.get('communityId')
                                        }
                                        ,count=True
                                        ) == 0:
        return bottle.HTTPError(403)



    events = EntityManager(_DBCON).get_all(Event
                                            ,filter_criteria={
                                                'ended':False,
                                                'communityId':bottle.request.GET.get('communityId')
                                            }
                                            ,sort_by=[('ends', 1)]
                                        )

    bets = EntityManager(_DBCON).get_all(Bet
                                            ,filter_criteria={
                                                'userId':bottle.request.session.userId
                                            })

    betIds = []
    betLookup = {}
    
    for b in bets:
        betIds.append(b.eventId)
        betLookup[b.eventId] = b

    output = []
    for e in events:
        if type(e.ends) == datetime.datetime:
            e.ends = e.ends.strftime('%d %B %Y')
        else:
            e.ends = None

        thisevent = e.get_json_safe()

        if str(e._id) in betIds:
            thisevent['pendingBetAmount'] = betLookup[str(e._id)].amount

        output.append(thisevent)

    return json.dumps(output)



@bottle.route('/event/:eventId')
@checklogin
@JSONResponse
def index(eventId):
    e = Event(_DBCON, _id=eventId)

    output = {}

    output['event'] = e.get_json_safe()
    if e.ended:
        output['bets'] = [b.get_json_safe() for b in EntityManager(_DBCON).get_all(Bet,filter_criteria={'eventId':eventId})]

    if e.userId == bottle.request.session.userId:
        output['canAddResult'] = True

    return json.dumps(output)


@bottle.route('/event/:eventId/result/add', method='POST')
@checklogin
@JSONResponse
def index(eventId):
    e = Event(_DBCON, _id=eventId)

    if e.ended or e.userId != bottle.request.session.userId:
        return bottle.HTTPError(403)

    e.resultChoiceId = bottle.request.POST.choiceId
    e.ended = True
    e.save()

    for b in EntityManager(_DBCON).get_all(Bet, filter_criteria={'eventId':eventId}):

        u = PredictionsUser(_DBCON, _id=b.userId)
        u.pendingFunds -= b.amount

        if str(b.choice._id) == str(e.resultChoiceId):
            b.winnings =  b.amount * b.choice.odds.multiplyBy
            b.success = True

            u.totalFunds += b.amount + b.winnings

        else:
            success = False
            b.winnings = 0 - b.amount

        b.save()
        u.save()

    return {'success':1}


@bottle.route('/odds')
@checklogin
@JSONResponse
def index():
    odds = EntityManager(_DBCON).get_all(Odds
                                        ,sort_by=[('added', 1)]
                                        )

    output = []
    for o in odds:
        output.append(o.get_json_safe())

    return json.dumps(output)


@bottle.route('/event/save', method="POST")
@checklogin
@JSONResponse
def index():
    choices = []
    choiceTitles = bottle.request.POST.getall('choice[]')
    odds = bottle.request.POST.getall('odds[]')

    eventtitle = bottle.request.POST.title

    if eventtitle and len(choiceTitles) > 1:

        if bottle.request.POST.ends:
            try:
                day, month, year = bottle.request.POST.ends.split('/')
                enddate = datetime.datetime(int(year), int(month), int(day))
            except:
                return bottle.HTTPError(403)

        i = 0
        for choicetitle in choiceTitles:
            c = Choice(_DBCON)
            c.title = choicetitle
            c.odds = Odds(_DBCON, odds[i]) 
            c.userId = bottle.request.session.userId
            c.save()

            choices.append(c)
            i += 1


        e = Event(_DBCON)
        e.title = eventtitle
        e.description = bottle.request.POST.description
        e.choices = choices
        if bottle.request.POST.ends: e.ends = enddate
        e.userId = bottle.request.session.userId
        if bottle.request.POST.communityId and bottle.request.POST.communityId != '0':
            e.communityId = bottle.request.POST.communityId
        e.save()

        output = {'success':1}

    else:
        output = {
            'success':0,
            'error':'Required data is missing'
        }


    return json.dumps(output)




@bottle.route('/choice/add', method='POST')
@checklogin
@JSONResponse
def index():
    c = Choice(_DBCON)
    c.title = bottle.request.POST.title
    c.description = bottle.request.POST.description
    c.userId = bottle.request.session.userId
    c.save()

    return ''


@bottle.route('/bet/add', method='POST')
@checklogin
@JSONResponse
def index():
    betamount = bottle.request.POST.amount 
    if not betamount.isdigit():
        return bottle.HTTPError(403)


    e = Event(_DBCON, _id=bottle.request.POST.eventId)

    if e.ended or ( type(e.ends) == datetime.datetime and e.ends < datetime.datetime.now() ):
        return bottle.HTTPError(403)

    u = PredictionsUser(_DBCON, _id=bottle.request.session.userId)
    u.totalFunds -= int(betamount)

    if u.totalFunds < 0:
        output = {
            'success':0,
            'error':'You do not have enough funds available'
        }
    else:

        bets = EntityManager(_DBCON).get_all(Bet
                                            ,filter_criteria={
                                                'userId':bottle.request.session.userId,
                                                'eventId':bottle.request.POST.eventId,
                                            })

        if bets:
            #updating a previous bet so give back the original bet amount
            b = bets[0]
            u.pendingFunds -= b.amount
            u.totalFunds += b.amount

        else:
            b = Bet(_DBCON)

        b.eventId = bottle.request.POST.eventId
        b.choice = Choice(_DBCON, _id=bottle.request.POST.choiceId)
        b.amount = int(betamount)
        b.userId = bottle.request.session.userId
        b.username = PredictionsUser(_DBCON, _id=b.userId).username
        b.save()

        u.pendingFunds += int(betamount)
        u.save()

        output = {
            'success':1
        }

    return output



@bottle.route('/result')
@checklogin
@JSONResponse
def index():
    bets = EntityManager(_DBCON).get_all(Bet
                                            ,filter_criteria={
                                                'userId':bottle.request.session.userId
                                            }
                                            ,sort_by=[('added', -1)]
                                        )

    output = []
    for b in bets:
        b.added = b.added.strftime('%d %B %Y')

        thisbet = b.get_json_safe()
        thisbet['event'] = Event(_DBCON, _id=b.eventId).get_json_safe()
        output.append(thisbet)

    return json.dumps(output)



@bottle.route('/user')
@checklogin
@JSONResponse
def index():
    u = PredictionsUser(_DBCON, _id=bottle.request.session.userId)

    return {
        'pendingFunds':u.pendingFunds,
        'totalFunds':u.totalFunds,
        'username':u.username,
    }



@bottle.route('/communities')
@checklogin
@JSONResponse
def index():
    mycommunityIds = [ObjectId(uc.communityId) for uc in EntityManager(_DBCON).get_all(User4Community, filter_criteria={'user._id':bottle.request.session.userId})]
    
    coms = EntityManager(_DBCON).get_all(Community, filter_criteria={
                                                                        '$or':[
                                                                            {'public':True},
                                                                            {'_id':{'$in':mycommunityIds}},
                                                                        ]
                                                                    }
                                                                    , sort_by=[('name',1)]
                                                                    )


    return json.dumps([c.get_json_safe() for c in coms])



@bottle.route('/community', method='POST')
@checklogin
@JSONResponse
def index():
    name = bottle.request.POST.name

    if name:
        c = Community(_DBCON)
        c.name = name
        c.userId = bottle.request.session.userId
        c.public = bottle.request.POST.public == '1'
        c.save()

        for uid in bottle.request.POST.userIds:
            uc = User4Community(_DBCON)
            uc.user = User(_DBCON, _id=uid)
            uc.communityId = c._id
            uc.approved = True
            uc.save()

        output = {'success':1}

    else:
        output = {
            'success':0,
            'error':'Required data is missing'
        }


    return json.dumps(output)


#######################################################

if __name__ == '__main__':
    with open(settings.ROOTPATH +'/app.pid','w') as f:
        f.write(str(os.getpid()))

    if settings.DEBUG: 
        bottle.debug() 
        
    bottle.run(server=settings.SERVER, reloader=settings.DEBUG, host=settings.APPHOST, port=settings.APPPORT, quiet=(settings.DEBUG==False) )
