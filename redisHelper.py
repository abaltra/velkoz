import redis
import time
import sys
import logging

class RedisHelper:
	def __init__(self, redis_creds=None):
		try:
			if redis_creds:
				self.redis = redis.StrictRedis(
	                host=redis_creds['host'],
	                port=redis_creds['host'],
	                password=redis_creds['pass'])
			else:
				self.redis = redis.StrictRedis(
					host='localhost',
					port=6379)
		except:
			logging.error('Could not connect to Redis')
			sys.exit(-2)

	def set_property_last_seen(self, prop, ttl):
		p = self.redis.pipeline()
		p.set(prop, 1)
		p.expire(prop, ttl)
		p.execute()

	def should_get_property(self, prop):
		return self.redis.get(prop) != 1

	def should_get_player_profile(self, accountId, summonerId, region):
		return self.should_get_property('profileflags:%s:%s:%s' % (accountId, summonerId, region))

	def player_profile_updated(self, accountId, summonerId, region, ttl=60): #default to a minute for now
		self.set_property_last_seen('profileflags:%s:%s:%s' % (accountId, summonerId, region), ttl)

	def should_get_player_league(self, summonerId, region):
		return self.should_get_property('leagueflags:%s:%s' % (summonerId, region))

	def player_league_updated(self, summonerId, region, ttl=60): #default to a minute for now
		self.set_property_last_seen('leagueflags:%s:%s' % (summonerId, region), ttl)

	def should_get_player_matches(self, accountId, region):
		return self.should_get_property('recentmatchesflags:%s:%s' % (accountId, region))

	def player_recent_matches_updated(self, accountId, region, ttl=60): #default to a minute for now
		self.set_property_last_seen('recentmatchesflags:%s:%s' % (accountId, region), ttl)
		
	def get_player_last_seen_match(self, accountId, region):
		return self.redis.get('lastseenmatches:%s:%s' % (accountId, region))

	def set_player_last_seen_match(self, accountId, region, matchid):
		self.redis.set('lastseenmatches:%s:%s' % (accountId, region), matchid)

