class RiotError(Exception):
	''' Base Riot error '''
	def __init__(self, message, *args):
		pass

class RiotRateError(RiotError):
	''' Raise when getting 409s from Riot '''
	def __init__(self, message, *args):
		self.message = 'RiotRateError %s' % message
		super(RiotRateError, self).__init__(message, *args)

class RiotInvalidKeyError(RiotError):
	''' Raise when our key is expired or blacklisted '''
	def __init__(self, message, *args):
		self.message = 'RiotInvalidKey %s' % message
		super(RiotInvalidKeyError, self).__init__(message, *args)

class RiotDataNotFoundError(RiotError):
	''' Raise when data not found in Riot's API '''
	def __init__(self, message, *args):
		self.message = 'RiotDataNotFound %s' % message
		super(RiotDataNotFoundError, self).__init__(message, *args)

class RiotDataUnavailable(RiotError):
	''' Raise Riot's API is unavailable '''
	def __init__(self, message, *args):
		self.message = 'RiotDataUnvailable %s' % message
		super(RiotDataUnavailable, self).__init__(message, *args)
