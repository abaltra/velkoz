from hotqueue import HotQueue
import logging

class QueueHelper:
	def __init__(self, host='localhost', port=6379, db=0):
		self.summoners_list = HotQueue('summonerslist', host=host, port=port, db=db)
		self.operations_list = HotQueue('operationslsit', host=host, port=port, db=db)

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