from aiohttp import ClientSession
import asyncio
import json
import logging
import time
import datetime
import importlib
import plugins
import sys
import inspect
from redisHelper import RiotRedisHelper
from mongoHelper import MongoHelper
from queueHelper import QueueHelper
from errors import RiotRateError, RiotInvalidKeyError, RiotDataNotFoundError, RiotDataUnavailable

#All queues
QUEUE_ID_TO_VALUE_MAP = {
	0: "CUSTOM", 460: "NORMAL_3x3", 430: "NORMAL_5x5_BLIND", 14: "NORMAL_5x5_DRAFT",
	4: "RANKED_SOLO_5x5", 6: "RANKED_PREMADE_5x5", 42: "RANKED_TEAM_5x5",
	410: "TEAM_BUILDER_DRAFT_RANKED_5x5", 420: "TEAM_BUILDER_RANKED_SOLO",
	440: "RANKED_FLEX_SR", 470: "RANKED_FLEX_TT", 41: "RANKED_TEAM_3x3",
	16: "ODIN_5x5_BLIND", 17: "ODIN_5x5_DRAFT", 25: "BOT_ODIN_5x5", 830: "BOT_5x5_INTRO",
	840: "BOT_5x5_BEGINNER", 850: "BOT_5x5_INTERMEDIATE", 800: "BOT_TT_3x3",
	61: "GROUP_FINDER_5x5", 450: "ARAM_5x5", 70: "ONEFORALL_5x5", 72: "FIRSTBLOOD_1x1", 73: "FIRSTBLOOD_2x2", 75: "SR_6x6",
	76: "URF_5x5", 78: "ONEFORALL_MIRRORMODE_5x5", 83: "BOT_URF_5x5",
	91: "NIGHTMARE_BOT_5x5_RANK1", 92: "NIGHTMARE_BOT_5x5_RANK2", 93: "NIGHTMARE_BOT_5x5_RANK5",
	96: "ASCENSION_5x5", 98: "HEXAKILL", 100: "BILGEWATER_ARAM_5x5", 300: "KING_PORO_5x5",
	310: "COUNTER_PICK", 313: "BILGEWATER_5x5", 940: "SIEGE", 317: "DEFINITELY_NOT_DOMINION_5x5",
	318: "ARURF_5X5", 325: "ARSR_5x5", 400: "TEAM_BUILDER_DRAFT_UNRANKED_5x5",
	430: "TB_BLIND_SUMMONERS_RIFT_5x5", 600: "ASSASSINATE_5x5", 610: "DARKSTAR_3x3"
}

#Queues we care about
TRACKED_QUEUE_IDS = {
	8: "NORMAL_3x3", 2: "NORMAL_5x5_BLIND", 14: "NORMAL_5x5_DRAFT",
	4: "RANKED_SOLO_5x5", 6: "RANKED_PREMADE_5x5", 42: "RANKED_TEAM_5x5",
	410: "TEAM_BUILDER_DRAFT_RANKED_5x5", 420: "TEAM_BUILDER_RANKED_SOLO",
	440: "RANKED_FLEX_SR", 9: "RANKED_FLEX_TT", 41: "RANKED_TEAM_3x3"
}

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
	def __init__(self, api_key, redis_creds=None, crawl=False):
		self.key = api_key
		self.redis = RiotRedisHelper(redisCreds=redis_creds)
		self.mongo = MongoHelper()
		self.queue = QueueHelper()
		self.crawl = crawl
		# Make an array of methods to use on a match object. Extra functionality should be added there or follow a similar principle
		self.plugin_methods = []
		for pl in plugins.__all__:
			m = importlib.import_module('plugins.%s' % pl)
			self.plugin_methods.append(m)

	def throttle(self, headers):
		'''
			Throttle the calls if required. Riot enforces 2 limits per call, an API-wide one and a per-method one. We check all of them and sleep if we are close to offending one.
		'''
		current_m_limit = headers.get('X-Method-Rate-Limit')
		current_m_count = headers.get('X-Method-Rate-Limit-Count')
		current_a_limit = headers.get('X-App-Rate-Limit')
		current_a_count = headers.get('X-App-Rate-Limit-Count')

		#Riot has API wide limits and per-method limits. Check all of them.
		if current_m_limit is not None:
			current_m_limit = float(current_m_limit.split(',')[0].split(':')[0])

		if current_m_count is not None:
			current_m_count = float(current_m_count.split(',')[0].split(':')[0])

		if current_a_limit is not None:
			current_a_limit = float(current_a_limit.split(',')[0].split(':')[0])

		if current_a_count is not None:
			current_a_count = float(current_a_count.split(',')[0].split(':')[0])

		#if any of our counts are withing 15% of the it's rate limit, wait
		#TODO: tweak this variables to reach balance. It should be based on number of workers and size of limits. Also, experiment with using a redis check mechanism; if horizontal scalability is easy and cheap enough, we could ping redis a lot of times and it shouldn't be a problem. (or any other key-value storage service with high throughput.)
		if current_a_count is not None and current_a_limit is not None and current_m_count is not None and current_m_limit is not None:
			if (current_a_count / current_a_limit) >= 0.75 or (current_m_count / current_m_limit) >= 0.75:
				logging.info('Rate limit threshold reached. MethodLimit: %s, MethodCount: %s. AppLimit: %s, AppCount: %s. Sleeping for 5 seconds' % (current_m_limit, current_m_count, current_a_limit, current_a_count))
				time.sleep(5)

	async def call_riot(self, url):
		'''
			Centralized communications with Riot. All new methods calling new endpoints should wrap this.
			By default, all errors are bubbled up, if specific handling is required, it should be added here.
		'''
		async with ClientSession() as session:
			async with session.get(url) as response:
				status_code = response.status
				d = await response.read()
				self.throttle(response.headers)

				if status_code == 200:
					return json.loads(d.decode())

				#Any low-level handling of riot errors should be added here, right now it just bubbles up the appropriate exception
				elif status_code == 409:
					raise RiotRateError('Call to %s went over rate limit' % url)

				elif status_code == 403:
					raise RiotInvalidKeyError('Key %s is no longer valid' % self.key)

				elif status_code == 404:
					raise RiotDataNotFoundError('Call to %s 404d' % url)

				else:
					raise RiotDataUnavailable('Riot API unavailable for %s' % url)

	'''
	 ---- RIOT CALL WRAPPERS ----
	 All these methods are super simple wrappers over the centralized call_riot method. All new calls to Riot API should follow the same structure
	'''
	async def get_summoner_by_account(self, accountId, region):
		logging.info('Getting summoner info for accountId: %s in %s' % (accountId, region))
		try:
			region = REGIONS_TO_ENDPOINTS_MAP[region.lower()]
			return await self.call_riot('https://%s.api.riotgames.com/lol/summoner/v3/summoners/by-account/%s?api_key=%s' % (region, accountId, self.key))
		except Exception as ex:
			raise

	async def get_summoner_by_summonerid(self, summonerId, region):
		logging.info('Getting summoner info for summonerId: %s in %s' % (summonerId, region))
		try:
			region = REGIONS_TO_ENDPOINTS_MAP[region.lower()]
			return await self.call_riot('https://%s.api.riotgames.com/lol/summoner/v3/summoners/%s?api_key=%s' % (region, summonerId, self.key))
		except Exception as ex:
			raise

	async def get_summoner(self, accountId=None, summonerId=None, region=None):
		if accountId is None and summonerId is None:
			raise ValueError('accountId and summonerId can\' both be NoneType')
		try:
			if summonerId is None:
				return await self.get_summoner_by_account(accountId=accountId, region=region)
			else:
				return await self.get_summoner_by_summonerid(summonerId=summonerId, region=region)
		except Exception as ex:
			raise

	async def get_league(self, summonerId, region):
		logging.info('Getting summoner info for summonerId: %s in %s' % (summonerId, region))
		try:
			region = REGIONS_TO_ENDPOINTS_MAP[region.lower()]
			return await self.call_riot('https://%s.api.riotgames.com/lol/league/v3/leagues/by-summoner/%s?api_key=%s' % (region, summonerId, self.key))
		except Exception as ex:
			raise

	async def get_recent_matches_by_account(self, accountId, region):
		try:
			region = REGIONS_TO_ENDPOINTS_MAP[region.lower()]
			return await self.call_riot('https://%s.api.riotgames.com/lol/match/v3/matchlists/by-account/%s?api_key=%s' % (region, accountId, self.key))
		except Exception as ex:
			raise

	async def get_match(self, matchId, region):
		logging.info('Getting match %s from %s' % (matchId, region))
		try:
			region = REGIONS_TO_ENDPOINTS_MAP[region.lower()]
			return await self.call_riot('https://%s.api.riotgames.com/lol/match/v3/matches/%s?api_key=%s' % (region, matchId, self.key))
		except Exception as ex:
			raise
	'''
	---- END RIOT CALL WRAPPERS ----
	'''

	async def retrieve_and_parse_match(self, summonerId, matches, region):
		'''
			Example of stats being calculated. These code creates aggregates per player, per champ and per lane for each day. These could be used to track player participation with different champs on different aspects of the game (damage, vision, tankiness, etc) and follow up on progress.
			Different aggregates can be done using this as base.
		'''

		for match in matches:
			try:
				if match['queue'] in QUEUE_ID_TO_VALUE_MAP and match['queue'] in TRACKED_QUEUE_IDS:
					m = await self.get_match(match['gameId'], region)
					for p in self.plugin_methods:
						p.process(m, summonerId, self.mongo)

			except Exception as ex:
				raise

	async def get_recent_matches(self, accountId=None, summonerId=None, region=None):
		'''
			Get player's recent matches and parse/save/aggregate as necessary.
		'''
		logging.info('Getting recent matches for %s:%s:%s' % (accountId, summonerId, region))

		if accountId is None or region is None:
			raise ValueError('Invalid summoner data. Can\'t get matches')

		if self.redis.should_get_player_matches(accountId, region):
			try:
				matches = await self.get_recent_matches_by_account(accountId, region)
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
					await self.retrieve_and_parse_match(summonerId, new_matches, region)

				else:
					logging.info('No new matches for %s:%s:%s' % (accountId, summonerId, region))
			except:
				raise


	async def update_player_profile(self, accountId='', summonerId='', region=None):
		'''
			Keep the player profile we have in the DB up to date. It uses redis flags to minimize the calls to Riot. It defaults to 1 min until the profile has to be updated, but it can be tweaked using params.
			The profile, leagues and matches all use different flags to know if they should be updates.
		'''
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
					profile = await self.get_summoner(summonerId=summonerId, region=region)
				except Exception as ex:
					raise
				accountId = profile['accountId']

		elif summonerId == '':
			#same as above
			profile = self.mongo.get_player_profile(accountId=accountId, region=region)
			if profile is None:
				isNew = True
				try:
					profile = await self.get_summoner(accountId=accountId, region=region)
				except Exception as ex:
					raise
				summonerId = profile['id']

		# Yes, I know it's a double check, but checking for profile first saves a redis request
		if profile is not None or self.redis.should_get_player_profile(accountId, summonerId, region):
			if profile is None:
				try:
					profile = await self.get_summoner(accountId=accountId, region=region)
				except Exception as ex:
					raise
			self.redis.player_profile_updated(accountId, summonerId, region)
			self.mongo.update_profile(profile=profile, region=region)


		if self.redis.should_get_player_league(summonerId, region):
			try:
				leagues = await self.get_league(summonerId, region)
			except Exception as ex:
				raise
			for league in leagues:
				for player in league['entries']:
					if self.crawl is True and player['playerOrTeamId'] != summonerId and not self.mongo.player_exists(summonerId=player['playerOrTeamId'], region=region):
						self.queue.put_player(summonerId=player['playerOrTeamId'], region=region)
					elif player['playerOrTeamId'] == summonerId:
						meta = { 'tier': league['tier'], 'queue': league['queue'], 'name': league['name'] }
						self.mongo.update_leagues(summonerId=summonerId, league=player, meta=meta, region=region)


		return profile['accountId'], profile['id']
