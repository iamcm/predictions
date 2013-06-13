import os, sys
sys.path.append(os.path.abspath( os.path.join(__file__,'../..')))

from db import _DBCON
from models.EntityManager import EntityManager

##############
# Odds
from models.Models import Odds


if EntityManager(_DBCON).get_all(Odds, count=True) == 0:
	ODDS = [
		('2/1',2),
		('5/1',5),
		('10/1',10),
	]

	for odd in ODDS:
		o = Odds(_DBCON)
		o.name = odd[0]
		o.multiplyBy = int(odd[1])
		o.save()



###############
# User
from models.Models import PredictionsUser

if EntityManager(_DBCON).get_all(PredictionsUser, count=True) == 0:
	u = PredictionsUser(_DBCON)
	u.email = 'i.am.chrismitchell@gmail.com'
	u.username = 'Chris'
	u.password = 'pass'
	u.valid = True
	u.save()

	u = PredictionsUser(_DBCON)
	u.email = 'milchardo@hotmail.co.uk'
	u.username = 'Mitchy'
	u.password = 'pass'
	u.valid = True
	u.save()
	
