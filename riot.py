import requests as r
import json
import logging
import time
from redisHelper import RedisHelper
from mongoHelper import MongoHelper
from queueHelper import QueueHelper
from errors import RiotRateError, RiotInvalidKeyError, RiotDataNotFoundError, RiotDataUnavailable

REGIONS_TO_ENDPOINTS_MAP = {
	'na': 'na1',
	'ru': 'ru',
	'kr': 'kr',
	'br': 'br1',
	'oce': 'oc1',
	'jp': 'jp1',
	'eun': 'eun1',
	'euw': 'euw1',
	'tr': 'tr1',
	'lan': 'la1',
	'las': 'la2'
}

class Riot:
	def __init__(self, api_key, redis_creds=None):
		self.key = api_key
		self.redis = RedisHelper(redis_creds=redis_creds)
		self.mongo = MongoHelper()
		self.queue = QueueHelper()

	def get_match(self, gameId, region):
		region = REGIONS_TO_ENDPOINTS_MAP[region.lower()]
		m = r.get('https://%s.api.riotgames.com/lol/match/v3/matches/%s?api_key=%s' % (region, gameId, self.key))

		if m.status_code == 200:
			return m.json()

	def throttle(self, headers):
		current_m_limit = headers.get('X-Method-Rate-Limit')
		current_m_count = headers.get('X-Method-Rate-Limit-Count')
		current_a_limit = headers.get('X-App-Rate-Limit')
		current_a_count = headers.get('X-App-Rate-Limit-Count')

		if current_m_limit is not None:
			current_m_limit = float(current_m_limit.split(',')[0].split(':')[0])

		if current_m_count is not None:
			current_m_count = float(current_m_count.split(',')[0].split(':')[0])

		if current_a_limit is not None:
			current_a_limit = float(current_a_limit.split(',')[0].split(':')[0])

		if current_a_count is not None:
			current_a_count = float(current_a_count.split(',')[0].split(':')[0])
		
		#if any of our counts are withing 15% of the it's rate limit, wait
		#TODO: tweak this variables to reach balance. It should be based on number of workers and size of limits
		if current_a_count is not None and current_a_limit is not None and current_m_count is not None and current_m_limit is not None:
			if (current_a_count / current_a_limit) >= 0.75 or (current_m_count / current_m_limit) >= 0.75:
				logging.info('Rate limit threshold reached. MethodLimit: %s, MethodCount: %s. AppLimit: %s, AppCount: %s. Sleeping for 5 seconds' % (current_m_limit, current_m_count, current_a_limit, current_a_count))
				time.sleep(5)


	def call_riot(self, url):
		d = r.get(url)
		self.throttle(d.headers)

		if d.status_code == 200:
			return d.json()

		elif d.status_code == 409:
			raise RiotRateError('Call to %s went over rate limit' % url)

		elif d.status_code == 403:
			raise RiotInvalidKeyError('Key %s is no longer valid' % self.key)

		elif d.status_code == 404:
			raise RiotDataNotFoundError('Call to %s 404d' % url)

		else:
			raise RiotDataUnavailable('Riot API unavailable for %s' % url)

	def get_summoner_by_account(self, accountId, region):
		logging.info('Getting summoner info for accountId: %s in %s' % (accountId, region))
		try:
			region = REGIONS_TO_ENDPOINTS_MAP[region.lower()]
			return self.call_riot('https://%s.api.riotgames.com/lol/summoner/v3/summoners/by-account/%s?api_key=%s' % (region, accountId, self.key))
		except Exception as ex:
			raise

	def get_summoner_by_summonerid(self, summonerId, region):
		logging.info('Getting summoner info for summonerId: %s in %s' % (summonerId, region))
		try:
			region = REGIONS_TO_ENDPOINTS_MAP[region.lower()]
			return self.call_riot('https://%s.api.riotgames.com/lol/summoner/v3/summoners/%s?api_key=%s' % (region, summonerId, self.key))
		except Exception as ex:
			raise

	def get_summoner(self, accountId=None, summonerId=None, region=None):
		if accountId is None and summonerId is None:
			raise ValueError('accountId and summonerId can\' both be NoneType')
		try:
			if summonerId is None:
				return self.get_summoner_by_account(accountId=accountId, region=region)
			else:
				return self.get_summoner_by_summonerid(summonerId=summonerId, region=region)
		except Exception as ex:
			raise

	def get_league(self, summonerId, region):
		logging.info('Getting summoner info for summonerId: %s in %s' % (summonerId, region))
		try:
			region = REGIONS_TO_ENDPOINTS_MAP[region.lower()]
			return self.call_riot('https://%s.api.riotgames.com/lol/league/v3/leagues/by-summoner/%s?api_key=%s' % (region, summonerId, self.key))
		except Exception as ex:
			raise

	def get_recent_matches_by_account(self, accountId, region):
		try:
			region = REGIONS_TO_ENDPOINTS_MAP[region.lower()]
			return self.call_riot('https://%s.api.riotgames.com/lol/match/v3/matchlists/by-account/%s/recent?api_key=%s' % (region, accountId, self.key))
		except Exception as ex:
			raise


	def get_recent_matches(self, accountId=None, summonerId=None, region=None):
		logging.info('Getting recent matches for %s:%s:%s' % (accountId, summonerId, region))

		if accountId is None or region is None:
			raise ValueError('Invalid summoner data. Can\'t get matches')

		if self.redis.should_get_player_matches(accountId, region):
			try:
				matches = self.get_recent_matches_by_account(accountId, region)
				last_seen_match = self.redis.get_player_last_seen_match(accountId, region)

				new_matches = []
				for match in matches['matches']:
					if str(match['gameId']) == str(last_seen_match):
						break
					else:
						new_matches.append(match)

				if len(new_matches) > 0:
					#we have real new matches
					self.mongo.save_new_matches(accountId, region, new_matches)
					self.redis.set_player_last_seen_match(accountId, region, new_matches[0]['gameId'])

				else:
					logging.info('No new matches for %s:%s:%s' % (accountId, summonerId, region))
			except:
				raise



	def update_player_profile(self, accountId='', summonerId='', region=None):
		logging.info('Updating player profile for %s:%s:%s' % ( accountId, summonerId, region ))
		profile = None
		isNew = False
		if accountId == '' and summonerId == '':
			# broken player, log and skip
			raise ValueError('Invalid summoner data. Can\'t get profile.')

		elif accountId == '':
			#Try and fill data from mongo
			profile = self.mongo.get_player_profile(summonerId=summonerId, region=region)				
			if profile is None:
				# new player, get from riot
				isNew = True
				try:
					profile = self.get_summoner(summonerId=summonerId, region=region)
				except Exception as ex:
					raise
				accountId = profile['accountId']

		elif summonerId == '':
			#same as above
			profile = self.mongo.get_player_profile(accountId=accountId, region=region)
			if profile is None:
				isNew = True
				try:
					profile = self.get_summoner(accountId=accountId, region=region)
				except Exception as ex:
					raise
				summonerId = profile['id']

		# Yes, I know it's a double check, but checking for profile first saves a redis request
		if profile is not None or self.redis.should_get_player_profile(accountId, summonerId, region):
			if profile is None:
				try:
					profile = self.get_summoner(accountId=accountId, region=region)
				except Exception as ex:
					raise
			self.redis.player_profile_updated(accountId, summonerId, region)
			self.mongo.update_profile(profile=profile, region=region)

		if self.redis.should_get_player_league(summonerId, region):
			try:
				leagues = self.get_league(summonerId, region)
			except Exception as ex:
				raise
			for league in leagues:
				for player in league['entries']:
					if player['playerOrTeamId'] != summonerId and not self.mongo.player_exists(summonerId=player['playerOrTeamId'], region=region):
						self.queue.put_player(summonerId=player['playerOrTeamId'], region=region)
					elif player['playerOrTeamId'] == summonerId:
						meta = { 'tier': league['tier'], 'queue': league['queue'], 'name': league['name'] }
						self.mongo.update_leagues(summonerId=summonerId, league=player, meta=meta, region=region)

		return profile['accountId'], profile['id']
					

				




