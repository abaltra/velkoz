from pymongo import MongoClient
from pymongo.collection import ReturnDocument
from pymongo import UpdateOne, InsertOne
from pymongo import DESCENDING
import sys
import logging

class MongoHelper:
	def __init__(self, cstring='mongodb://localhost:27017'):
		try:
			db = MongoClient(cstring)
			self.db = db['loldata']
		except:
			logging.error('Could not connect to mongo')
			sys.exit(-1)

	def save_new_matches(self, accountId, region, matches):
		logging.info('Inserting %s new matches for %s:%s' % (len(matches), accountId, region))
		ops = []
		for match in matches:
			match['accountId'] = accountId
			match['region'] = region

			ops.append(InsertOne(match))

		self.db['matchlist'].bulk_write(ops)

	def update_profile(self, profile, region):
		logging.info('Updating profile for accountId: %s in %s' % ( profile['accountId'], region ))
		profile['cleanName'] = profile['name'].replace(' ', '').lower()
		self.db['summoner_profiles'].update({ 'accountId': profile['accountId'], 'region': region }, { '$set': profile }, upsert=True)

	def update_leagues(self, summonerId, league, meta, region):
		logging.info('Updating league for summonerId: %s in %s' % (summonerId, region))
		league['name'] = meta['name']
		league['tier'] = meta['tier']
		league['queue'] = meta['queue']
		league['region'] = region
		league['summonerId'] = summonerId

		league.pop('playerOrTeamId', None)
		self.db['summoner_leagues'].update({ 'summonerId': summonerId, 'region': region, 'queue': league['queue'] }, { '$set': league }, upsert=True)

	def get_player_profile(self, accountId=None, summonerId=None, region=None):
		if accountId is None and summonerId is None:
			raise ValueError('AccountId and SummonerId can\'t both be NoneType')

		if accountId is None:
			return self.get_player_by_summonerid(summonerId=summonerId, region=region)

		elif summonerId is None:
			return self.get_player_by_account(accountId=accountId, region=region)

	def get_player_by_accountid(self, accountId, region):
		return self.db['summoner_profiles'].find_one({ 'accountId': accountId, 'region': region })

	def get_player_by_summonerid(self, summonerId, region):
		return self.db['summoner_profiles'].find_one({ 'id': summonerId, 'region': region })

	def player_exists(self, accountId=None, summonerId=None, region=None):
		if accountId is None and summonerId is None:
			raise ValueError('AccountId and SummonerId can\'t both be NoneType')

		if accountId is None:
			return self.player_exists_by_summoner(summonerId=summonerId, region=region)

		elif summonerId is None:
			return player_exists_by_account(accountId=accountId, region=region)			

	def player_exists_by_summoner(self, summonerId, region):
		return self.db['summoner_profiles'].find_one({ 'id': summonerId, 'region': region }) != None

	def player_exists_by_account(self, accountId, region):
		return self.db['summoner_profiles'].find_one({ 'accountId': accountId, 'region': region }) != None