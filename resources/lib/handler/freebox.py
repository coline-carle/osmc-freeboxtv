from resources.lib.handler.exceptions import FreeboxHandlerError 
from resources.lib.Channel import cChannel
import requests, json

# Class to manage freebox API calls
class Freebox:
	
	def __init__(self, appId, appName, appVersion, deviceName):
		self.apiUrl = 'https://http://mafreebox.freebox.fr/api/v4/'
		self.appId = appId
		self.appName = appName
		self.appVersion = appVersion
		self.deviceName = deviceName
		self.trackId = ''
		self.appToken = ''
		self.challenge = ''
		self.session = ''
		self.channelsList = []
		self.guidesList = []

    # useful if wanted quality is not available to get the lower one
    def _getLowerQuality(self, quality):
        if quality == 'hd': return 'auto'
        if quality == 'auto': return 'sd'
        if quality == 'sd': return 'ld'
        return false

	#check compatibility of the freebox with the script
	def checkApiVersion(self)
		apiResponse = requests.get(apiUrl+"api_version")
		if apiResponse.ok and format(len(jData)>0:
			jData = json.loads(apiResponse.content)
			if LooseVersion(jData['api_version']) >= '4.0':
				return True
			else:
				raise FreeboxHandlerError('[PLUGIN] freeboxTV: FreeBox API not compatible')
				return False
		else:
			raise FreeboxHandlerError('[PLUGIN] freeboxTV: FreeBox API not responded')
			return False

	# Ask freebox for pairing authorization
	def pairingWithFreeBox(self):
		import socket
		payload = {'app_id': '%s', 'app_name': '%s', 'app_version': '%s', 'device_name': '%s'} % (appId, appName, appVersion, deviceName)
		payload = json.dumps(payload)
		apiResponse = requests.post(apiUrl+"login/authorize/", data=payload)
		jData = json.loads(apiResponse.content)
		self.appToken = jData['result']['app_token']
		self.trackId = jData['result']['track_id']
		return True

    # check pair status
	def checkPairing(self, trackId):
		apiResponse = requests.get(apiUrl+"login/authorize/%d" %trackId)
		jData = json.loads(apiResponse.content)
		if jData['result']['status'] == 'granted':
			# all is ok
			self.challenge = jData['result']['challenge']
			return True
		else: 
			if (jData['result']['status'] == 'unknown') or (jData['result']['status'] == 'denied'):
				#token invalid or revoked
				raise FreeboxHandlerError('[PLUGIN] freeboxTV: Pairing Revoked)
		
			if (jData['result']['status'] == 'pending') or (jData['result']['status'] == 'timeout'):
				#the user has not confirmed the authorization request
				raise FreeboxHandlerError('[PLUGIN] freeboxTV: User not confirmed authorization')
		return False
	
	# get session/login token for futur requests	
	def getSession(self):
		hashed = hmac.new(self.appToken, self.challenge, sha1)
		payload = {'"app_id": "%s","password": "%s"} % (self.appId,hashed)
		apiResponse = request.post(apiUrl+"/api/v4/login/session/")
		jData = json.loads(apiResponse.content)
		if  jData['success'] == 'true':
			self.session = jData['result']['session_token']
			return True
		else:
			raise FreeboxHandlerError('[PLUGIN] freeboxTV: Get Session - '+str(jData['error_code']))
		return False
		
    # list all available channel
    def getChannelsList(self, quality):
        channelsList = []
        apiResponse = request.get(self.apiUrl+"tv/channels", headers={'X-Fbx-App-Auth':self.session})
        jData = json.loads(apiResponse.content)
        if jData['success'] == 'true':
            #crawl all channels returned
            for channel in jData['result']:
                # we take only available channel
                if channel['available'] == 'true':
                    rtsp, number = self._getChannelStream(channel['uuid'],quality)
                    #creating a list of channel objects
                    channelsList.append(
                        cChannel(
                            channel['uuid'],
                            number
                            channel['name'],
                            channel['shortname'],
                            channel['logo'],
                            rtsp
                            channel['quality']))
            return channelsList
        else:
            raise FreeboxHandlerError("[PLUGIN] freeboxTV: API doesn't answer correctly for channelList")

    # crawl API url to get all available channels stream
	def _getChannelStream(self, uuid, quality):
	    bouquetId = '107' # it should be the correct id
	    # but we will check the id of the bouquet, just to be sure
	    apiResponse = request.get(self.apiUrl+"tv/bouquets/", headers={'X-Fbx-App-Auth':self.session})
	    jData = json.loads(apiResponse.content)
	    if jData['success'] == 'true':
	        for bouqet = jData['result']:
	            if bouquet['Freebox TV']:
	                bouquetId = bouquet['id']
	    
	    # now get the channels list           
		apiResponse = request.get(self.apiUrl+"tv/bouquets/107/channels", headers={'X-Fbx-App-Auth':self.session})
		jData = json.loads(apiResponse.content)
		channelNumber = ''
		rtspUrl = ''
		if jData['success'] == 'true':
		    #crawl all channels returned
			for channel in jData['result']:
			    if channel['uuid'] == uuid:
			        channelNumber = channel['number']
					# create a temporary dict
					for stream in channel['streams']:
                       streams[stream['quality']] = stream['rtsp']
                    # check if the wanted quality exist, if not try to found the immediate available lower quality
                    tmpQuality = quality
					while not streams.has_keys(tmpQuality)):
                        tmpQuality = self._getLowerQuality(tmpQuality)
 			        rtspUrl = streams['tmpQuality']
            return rtspUrl, channelNumber
        else:
            raise FreeboxHandlerError("[PLUGIN] freeboxTV: API doesn't answer correctly for stream list")
