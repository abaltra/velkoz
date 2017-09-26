from riot import Riot
from queueHelper import QueueHelper
from errors import RiotRateError, RiotInvalidKeyError, RiotDataNotFoundError, RiotDataUnavailable
import argparse
import time
import sys
import traceback
import logging
import asyncio

async def run(key, crawl=False, firstUser=None):
	logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.DEBUG)
	riotHelper = Riot(key, crawl=crawl)
	queue = QueueHelper()

	if firstUser is not None:
		aId, sId, r = firstUser.split(':')
		queue.put_player(accountId=aId, summonerId=sId, region=r)

	for summoner in queue.summoners_list.consume():
		accountid, summonerid, region = summoner.split(':')

		try:
			# update profile data. If there's only account id, or only summoner id, then it's a new player. Return the missing data if that's the case
			#  - use leagues endpoint to get more players
			accountId, summonerId = await riotHelper.update_player_profile(accountId=accountid, summonerId=summonerid, region=region)

			# get recent matches
			#  - use recent matches to get more players
			await riotHelper.get_recent_matches(accountId=accountId, summonerId=summonerId, region=region)
			queue.put_player(accountId=accountId, summonerId=summonerId, region=region)
		except (RiotRateError, RiotInvalidKeyError, RiotDataNotFoundError, RiotDataUnavailable) as ex:
			#High level handling of errors should be added here
			logging.warning("Could not update %s because %s. Skipping and adding to the back of the queue" % (summoner, ex.message))
			queue.put_player(accountid, summonerid, region)

		#sys.exit(0)


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="A tool for getting summoners data", epilog="Remember to set your own API key!")
	parser.add_argument('key', help="Riot's API key")
	parser.add_argument('-c', '--crawl', action="store_true", help="True if we should crawl the matchlist for new players (defaults to False)", default=False)
	parser.add_argument('--first-user', help="If passed, insert this player in the queue before starting the loop, format is: AccountId:SummonerId:region", default=None)
	args = parser.parse_args()
	loop = asyncio.get_event_loop()
	try:
		loop.run_until_complete(run(args.key, args.crawl, args.first_user))
	except KeyboardInterrupt:
		loop.stop()
		sys.exit(0)
