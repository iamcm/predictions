import os, sys
sys.path.append(os.path.abspath( os.path.join(__file__,'../..')))

from bson import ObjectId
from db import _DBCON
from models.EntityManager import EntityManager

from models.Models import *

	
for c in EntityManager(_DBCON).get_all(Community, filter_criteria={
                                                                        '$or':[
                                                                            {'public':True},
                                                                            {'_id':{'$in':['51ba38726e955250610deebe'] }},
                                                                            {'_id':ObjectId('51ba38726e955250610deebe') },
                                                                        ]
                                                                    }
                                                                    , sort_by=[('name',1)]
                                                                    ):
	print(str(c.public)+':'+c.name+':'+str(c._id))

"""
u = EntityManager(_DBCON).get_all(PredictionsUser, filter_criteria={'username':'Chris'})

uc = User4Community(_DBCON)
uc.user = u
uc.approved = True
uc.communityId = '51ba38726e955250610deebe'
uc.save()

"""