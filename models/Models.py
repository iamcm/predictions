from models.User import User
from models.BaseModel import BaseModel
import datetime

class Event(BaseModel):    
    def __init__(self,_DBCON, _id=None):
        self.fields = [
        ('title', None),
        ('description', None),
        ('choices', []),
        ('ends', None),
        ('ended', False),
        ('communityId', None),
        ('resultChoiceId', None),
        ('added', datetime.datetime.now()),
        ('userId', None),
        ]
        super(self.__class__, self).__init__(_DBCON, _id)


class Choice(BaseModel):    
    def __init__(self,_DBCON, _id=None):
        self.fields = [
        ('title', None),
        ('description', None),
        ('odds', None),
        ('added', datetime.datetime.now()),
        ('userId', None),
        ]
        super(self.__class__, self).__init__(_DBCON, _id)


class Bet(BaseModel):    
    def __init__(self,_DBCON, _id=None):
        self.fields = [
        ('eventId', None),
        ('choice', None),
        ('amount', None),
        ('success', None),
        ('winnings', None),
        ('added', datetime.datetime.now()),
        ('userId', None),
        ('username', None),
        ]
        super(self.__class__, self).__init__(_DBCON, _id)


class Odds(BaseModel):    
    def __init__(self,_DBCON, _id=None):
        self.fields = [
        ('name', None),
        ('multiplyBy', None),
        ]
        super(self.__class__, self).__init__(_DBCON, _id)


class PredictionsUser(User):
    def __init__(self, _DBCON, _id=None, email=None, password=None):
        User.__init__(self, _DBCON, _id, email, password)

    def pre_init(self):
        self.fields.extend([
            ('username', None),
            ('totalFunds', 100),
            ('pendingFunds', 0),
        ])


class Community(BaseModel):
    def __init__(self,_DBCON, _id=None):
        self.fields = [
        ('name', None),
        ('public', False),
        ('added', datetime.datetime.now()),
        ('userId', None),
        ]
        super(self.__class__, self).__init__(_DBCON, _id)


class User4Community(BaseModel):
    def __init__(self,_DBCON, _id=None):
        self.fields = [
        ('communityId', None),
        ('user', None),
        ('approved', False),
        ('totalFunds', 100),
        ('pendingFunds', 0),
        ('added', datetime.datetime.now()),
        ]
        super(self.__class__, self).__init__(_DBCON, _id)
