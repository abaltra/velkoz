from riot import Riot
from redisHelper import RedisHelper
from queueHelper import QueueHelper
from errors import RiotRateError, RiotInvalidKeyError, RiotDataNotFoundError, RiotDataUnavailable
import argparse
import time
import sys
import traceback
import logging

def run():

	logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.DEBUG)
	riotHelper = Riot('RIOT KEY')
	redis = RedisHelper()
	queue = QueueHelper()

	#queue.put_player(accountId=406869, summonerId=411969, region='las')

	for summoner in queue.summoners_list.consume():
		accountid, summonerid, region = summoner.split(':')
		
		try:
			# update profile data. If there's only account id, or only summoner id, then it's a new player. Return the missing data if that's the case
			#  - use leagues endpoint to get more players
			accountId, summonerId = riotHelper.update_player_profile(accountId=accountid, summonerId=summonerid, region=region)

			# get recent matches
			#  - use recent matches to get more players
			riotHelper.get_recent_matches(accountId=accountId, summonerId=summonerId, region=region)
		except (RiotRateError, RiotInvalidKeyError, RiotDataNotFoundError, RiotDataUnavailable) as ex:
			logging.warning("Could not update %s because %s. Skipping and adding to back of the queue" % (summoner, ex.message))
			queue.put_player(accountid, summonerid, region)	

		#sys.exit(0)	


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="A tool for getting summoners data")
	run()
