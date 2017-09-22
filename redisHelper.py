import redis
import time
import sys
import logging

class RedisHelper(object):
	'''
	We'll be using Redis for different things, so it's better to wrap the bootstrap in a base class and just inherit as needed
	'''
	def __init__(self, redis_creds=None):
		self.test = 'las pelotas'
		self.redis = None
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

class QueueRedisHelper(RedisHelper):
	'''
	All queue related Redis interactions should be coded here
	'''
	def __init__(self, redisCreds=None, key='defaultkey'):
		self.key = key
		super(RiotRedisHelper, self).__init__(redisCreds)

	def put(self, *values):
		self.redis.rpush(self.key, *values)

	def consume(self):
		try:
		    while True:
		        msg = self.get(self.key)
		        if msg is None:
		            break
		        yield msg
		except KeyboardInterrupt:
		    print; return

	def get(self, block=False, timeout=None):
		if block:
		    if timeout is None:
		        timeout = 0
		    msg = self.redis.blpop(self.key, timeout=timeout)
		    if msg is not None:
		        msg = msg[1]
		else:
		    msg = self.redis.lpop(self.key)

		return msg

class RiotRedisHelper(RedisHelper):
	'''
	All Riot-related redis interactions should be here
	'''
	def __init__(self, redisCreds=None):
		super(RiotRedisHelper, self).__init__(redisCreds)

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
