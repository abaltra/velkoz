from redisHelper import QueueRedisHelper
import logging

class QueueHelper:
	def __init__(self, redisCreds=None):
		self.summoners_list = QueueRedisHelper(redisCreds=redisCreds, key='summonerslist')
		self.operations_list = QueueRedisHelper(redisCreds=redisCreds, key='operationslsit')

	def put_player(self, accountId=None, summonerId=None, region=None):
		if accountId is None and summonerId is None:
			# skip broken data
			return

		if accountId is None:
			key = ':%s:%s' % (summonerId, region)

		elif summonerId is None:
			key = '%s::%s' % (accountId, region)

		else:
			key = '%s:%s:%s' % (accountId, summonerId, region)

		logging.info('Putting player %s in the queue' % key)

		self.summoners_list.put(key)

	def put_operation(self, operation):
		self.operations_list.put(operation)
