import requests as r
import json
import logging
import time
import datetime
from redisHelper import RiotRedisHelper
from mongoHelper import MongoHelper
from queueHelper import QueueHelper
from errors import RiotRateError, RiotInvalidKeyError, RiotDataNotFoundError, RiotDataUnavailable

QUEUE_ID_TO_VALUE_MAP = {
	0: "CUSTOM", 8: "NORMAL_3x3", 2: "NORMAL_5x5_BLIND", 14: "NORMAL_5x5_DRAFT",
	4: "RANKED_SOLO_5x5", 6: "RANKED_PREMADE_5x5", 42: "RANKED_TEAM_5x5",
	410: "TEAM_BUILDER_DRAFT_RANKED_5x5", 420: "TEAM_BUILDER_RANKED_SOLO",
	440: "RANKED_FLEX_SR", 9: "RANKED_FLEX_TT", 41: "RANKED_TEAM_3x3",
	16: "ODIN_5x5_BLIND", 17: "ODIN_5x5_DRAFT", 25: "BOT_ODIN_5x5", 31: "BOT_5x5_INTRO",
	32: "BOT_5x5_BEGINNER", 33: "BOT_5x5_INTERMEDIATE", 52: "BOT_TT_3x3",
	61: "GROUP_FINDER_5x5", 65: "ARAM_5x5", 70: "ONEFORALL_5x5", 72: "FIRSTBLOOD_1x1", 73: "FIRSTBLOOD_2x2", 75: "SR_6x6",
	76: "URF_5x5", 78: "ONEFORALL_MIRRORMODE_5x5", 83: "BOT_URF_5x5",
	91: "NIGHTMARE_BOT_5x5_RANK1", 92: "NIGHTMARE_BOT_5x5_RANK2", 93: "NIGHTMARE_BOT_5x5_RANK5",
	96: "ASCENSION_5x5", 98: "HEXAKILL", 100: "BILGEWATER_ARAM_5x5", 300: "KING_PORO_5x5",
	310: "COUNTER_PICK", 313: "BILGEWATER_5x5", 315: "SIEGE", 317: "DEFINITELY_NOT_DOMINION_5x5",
	318: "ARURF_5X5", 325: "ARSR_5x5", 400: "TEAM_BUILDER_DRAFT_UNRANKED_5x5",
	430: "TB_BLIND_SUMMONERS_RIFT_5x5", 600: "ASSASSINATE_5x5", 610: "DARKSTAR_3x3"
}

TRACKED_QUEUE_IDS = {
	8: "NORMAL_3x3", 2: "NORMAL_5x5_BLIND", 14: "NORMAL_5x5_DRAFT",
	4: "RANKED_SOLO_5x5", 6: "RANKED_PREMADE_5x5", 42: "RANKED_TEAM_5x5",
	410: "TEAM_BUILDER_DRAFT_RANKED_5x5", 420: "TEAM_BUILDER_RANKED_SOLO",
	440: "RANKED_FLEX_SR", 9: "RANKED_FLEX_TT", 41: "RANKED_TEAM_3x3"
}

MARKSMEN_IDS = {
	22: 'ASHE', 268: 'AZIR', 42: 'CORKI', 119: 'DRAVEN', 81: 'EZREAL', 104: 'GRAVES', 126: 'JAYCE', 202: 'JHIN', 222: 'JINX', 429: 'KALISTA', 85: 'KENNEN', 203: 'KINDRED', 96: 'KOGMAW', 236: 'LUCIAN', 21: 'MISSFORTUNE', 133: 'QUINN', 15: 'SIVIR', 17: 'TEEMO', 18: 'TRISTANA', 29: 'TWITCH', 6: 'URGOT', 110: 'VARUS', 67: 'VAYNE', 51: 'CAITLYN'
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

	def get_match(self, matchId, region):
		logging.info('Getting match %s from %s' % (matchId, region))
		try:
			region = REGIONS_TO_ENDPOINTS_MAP[region.lower()]
			return self.call_riot('https://%s.api.riotgames.com/lol/match/v3/matches/%s?api_key=%s' % (region, matchId, self.key))
		except Exception as ex:
			raise


	def retrieve_and_parse_match(self, summonerId, matches, region):
		stats_to_aggregate = ['kills', 'deaths', 'assists', 'totalDamageDealt', 'magicDamageDealt', 'physicalDamageDealt', 'trueDamageDealt', 'totalDamageDealtToChampions', 'magicDamageDealtToChampions', 'physicalDamageDealtToChampions', 'trueDamageDealtToChampions', 'timeCCingOthers', 'totalDamageTaken', 'magicalDamageTaken', 'physicalDamageTaken', 'trueDamageTaken', 'totalHeal', 'totalUnitsHealed', 'damageSelfMitigated', 'damageDealtToObjectives', 'damageDealtToTurrets', 'goldEarned', 'goldSpent', 'turretKills', 'inhibitorKills', 'totalMinionsKilled', 'neutralMinionsKilled', 'neutralMinionsKilledTeamJungle', 'neutralMinionsKilledEnemyJungle', 'totalTimeCrowdControlDealt', 'visionWardsBoughtInGame', 'sightWardsBoughtInGame', 'wardsPlaced', 'wardsKilled']
		for match in matches:
			try:
				if match['queue'] in QUEUE_ID_TO_VALUE_MAP and match['queue'] in TRACKED_QUEUE_IDS:
					m = self.get_match(match['gameId'], region)
					participant_identity = None
					participant = None
					match_doc = dict()
					totals_incs = dict()
					team_incs = dict()
					match_incs = dict()
					match_doc['day'] = datetime.datetime.fromtimestamp(m['gameCreation'] / 1000).strftime('%y:%m:%d')
					match_doc['region'] = region
					match_doc['queueId'] = match['queue']
					match_doc['lane'] = match['lane']
					if match['lane'] == 'BOTTOM' and match['role'] == 'DUO':
						match_doc['role'] = 'DUO_CARRY' if MARKSMEN_IDS.get(match['champion'], None) is None else 'DUO_SUPPORT'
					else:
						match_doc['role'] = match['role']
					match_doc['championId'] = match['champion']
					match_doc['season'] = match['season']

					for _participant_identity in m['participantIdentities']:
						if 'player' in _participant_identity and _participant_identity['player']['summonerId'] == summonerId:
							#Found the player we are gathering data for
							participant_identity = _participant_identity
							break #no need to keep looking
					if participant_identity is None:
						raise ValueError('Summoner %s not found in match %s from %s' % (summonerId, match['matchId'], region))

					for _participant in m['participants']:
						#We need to find the correct participant's team first
						if _participant['participantId'] == participant_identity['participantId']:
							participant = _participant
							break #no need to keep going

					if participant is None:
						raise ValueError('Participant %s not found in match %s from %s' % (participant_id, match['matchId'], region))

					for _participant in m['participants']:
						#now that we have the team, we loop through all of them again, aggregating
						if _participant['teamId'] == participant['teamId']:
							#teammate or same player, we aggregate to team stats
							pstats = _participant['stats']
							for stat in stats_to_aggregate:
								team_incs[stat + 'ByTeam'] = pstats.get(stat, 0) if team_incs.get(stat + 'ByTeam', None) is None else team_incs.get(stat + 'ByTeam') + pstats.get(stat, 0)

						if _participant['participantId'] == participant['participantId']:
							#lets add the aggregates specific to our guy
							pstats = _participant['stats']
							for stat in stats_to_aggregate:
								match_incs[stat] = pstats.get(stat, 0) if match_incs.get(stat, None) is None else match_incs.get(stat) + pstats.get(stat, 0)
							match_incs['firstBloodKills'] = 1 if pstats.get('firstBloodKill', False) else 0
							match_incs['firstBloodAssists'] = 1 if pstats.get('firstBloodAssist', False) else 0
							match_incs['firstTowerKills'] = 1 if pstats.get('firstTowerKill', False) else 0
							match_incs['firstTowerAssists'] = 1 if pstats.get('firstTowerAssist', False) else 0
							match_incs['firstInhibitorKills'] = 1 if pstats.get('firstInhibitorKill', False) else 0

						#now add them to the match total, regardless of team
						for stat in stats_to_aggregate:
							pstats = _participant['stats']
							totals_incs[stat + 'InMatch'] = pstats.get(stat, 0) if totals_incs.get(stat + 'InMatch', None) is None else totals_incs.get(stat + 'InMatch') + pstats.get(stat, 0)

					match_doc['summonerId'] = participant_identity['player']['summonerId']
					match_doc['accountId'] = participant_identity['player']['currentAccountId']


					for team in m['teams']:
						if team['teamId'] == participant['teamId']:
							match_incs['count'] = 1 #track of how many matches for this combination we've seen so far
							match_incs['redSideMatches'] = 1 if team['teamId'] == 100 else 0
							match_incs['blueSideMatches'] = 1 if team['teamId'] == 200 else 0
							match_incs['wins'] = 1 if team['win'] == 'Win' else 0

					full_incs = dict(match_incs.items() | team_incs.items() | totals_incs.items())

					self.mongo.save_match_agg(match_doc, full_incs)
					tmp = match_doc.pop('championId', None)

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
					self.retrieve_and_parse_match(summonerId, new_matches, region)

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
					if self.crawl is True and player['playerOrTeamId'] != summonerId and not self.mongo.player_exists(summonerId=player['playerOrTeamId'], region=region):
						self.queue.put_player(summonerId=player['playerOrTeamId'], region=region)
					elif player['playerOrTeamId'] == summonerId:
						meta = { 'tier': league['tier'], 'queue': league['queue'], 'name': league['name'] }
						self.mongo.update_leagues(summonerId=summonerId, league=player, meta=meta, region=region)

		return profile['accountId'], profile['id']
