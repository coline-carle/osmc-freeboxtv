# -*- coding: utf-8 -*-
from resources.lib.handler.exceptions import FreeboxHandlerError
from resources.lib.channel import Channel as cChannel
from distutils.version import LooseVersion
import requests, json, xbmc, codecs

class Freebox:

    def __init__(self, appId, appName, appVersion, deviceName):
        self.apiUrl = 'https://mafreebox.freebox.fr/api/v4/'
        self.certPath = '/home/osmc/.kodi/addons/script.module.freeboxtv/resources/certificate/freebox.crt'
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

    def _getLowerQuality(self, quality):
        if quality == 'hd':
            return 'auto'
        if quality == 'auto':
            return 'sd'
        if quality == 'sd':
            return 'ld'
        return 'hd' # some channel only have hd so fallback if we found nothing else

    def checkApiVersion(self):
        apiResponse = requests.get(self.apiUrl + 'api_version', verify=self.certPath)
        jData = json.loads(apiResponse.content)
        if apiResponse.ok and format(len(jData)) > 0:
            jData = json.loads(apiResponse.content)
            if LooseVersion(jData['api_version']) >= '4.0':
                return True
            raise FreeboxHandlerError('[PLUGIN] freeboxTV: FreeBox API not compatible')
            return False
        else:
            raise FreeboxHandlerError('[PLUGIN] freeboxTV: FreeBox API not responded')
            return False

    def pairingWithFreebox(self):
        import socket
        payload = {'app_id': self.appId,
           'app_name': self.appName,
           'app_version': self.appVersion,
           'device_name': self.deviceName
           }
        payload = json.dumps(payload)
        apiResponse = requests.post(self.apiUrl + 'login/authorize/', data=payload, verify=self.certPath)
        jData = json.loads(apiResponse.content)
        if not apiResponse.ok and jData['success'] == True:
            raise FreeboxHandlerError('ERROR: ' + jData['msg'])
        self.appToken = jData['result']['app_token']
        self.trackId = jData['result']['track_id']
        return (
         self.appToken, self.trackId)

    def checkPairing(self, trackId):
        apiResponse = requests.get(self.apiUrl + 'login/authorize/' + trackId, verify=self.certPath)
        jData = json.loads(apiResponse.content)
        if not apiResponse.ok and jData['success'] == True:
            raise FreeboxHandlerError('ERROR: ' + jData['msg'])
            return 1
        if jData['result']['status'] == 'granted':
            self.challenge = jData['result']['challenge']
            return True
        if jData['result']['status'] == 'unknown' or jData['result']['status'] == 'denied':
            raise FreeboxHandlerError('[PLUGIN] freeboxTV: Pairing Revoked')
        if jData['result']['status'] == 'pending' or jData['result']['status'] == 'timeout':
            raise FreeboxHandlerError('[PLUGIN] freeboxTV: User not confirmed authorization')
        return False

    def getSession(self):
        hashed = hmac.new(self.appToken, self.challenge, sha1)
        payload = {'app_id': '%s','password': '%s'} % (self.appId, hashed)
        apiResponse = requests.post(self.apiUrl + '/api/v4/login/session/', verify=self.certPath)
        jData = json.loads(apiResponse.content)
        if jData['success'] == True:
            self.session = jData['result']['session_token']
            return True
        raise FreeboxHandlerError('[PLUGIN] freeboxTV: Get Session - ' + str(jData['error_code']))
        return False

    def getChannelsList(self, quality):
        channelsList = []
        apiResponse = requests.get(self.apiUrl + 'tv/channels', headers={'X-Fbx-App-Auth': self.session}, verify=self.certPath)
        jData = json.loads(apiResponse.content)
        if jData['success'] == True:
            for channelId in jData['result']:
                if jData['result'][channelId]['available'] == True:
                    rtsp, number = self._getChannelStream(jData['result'][channelId]['uuid'], quality)
                    if rtsp:
                        name = jData['result'][channelId]['name'].encode('ascii', 'replace')
                        shortname = jData['result'][channelId]['short_name'].encode('ascii', 'replace')
                        xbmc.log("collected uuid:"+jData['result'][channelId]['uuid'],xbmc.LOGERROR)
                        oChannel = cChannel(jData['result'][channelId]['uuid'], number, name, shortname, jData['result'][channelId]['logo_url'], rtsp, quality)
                        channelsList.append(oChannel)

            return channelsList
        raise FreeboxHandlerError("[PLUGIN] freeboxTV: API doesn't answer correctly for channelList")

    def _getChannelStream(self, uuid, quality):
        bouquetId = '107'
        apiResponse = requests.get(self.apiUrl + 'tv/bouquets/', headers={'X-Fbx-App-Auth': self.session}, verify=self.certPath)
        jData = json.loads(apiResponse.content)
        if jData['success'] == True:
            for bouquet in jData['result']:
                if bouquet['name'] == 'Freebox TV':
                    bouquetId = bouquet['id']

        apiResponse = requests.get(self.apiUrl + 'tv/bouquets/107/channels', headers={'X-Fbx-App-Auth': self.session}, verify=self.certPath)
        jData = json.loads(apiResponse.content)
        channelNumber = ''
        rtspUrl = ''
        if jData['success'] == True:
            for channel in jData['result']:
                if channel['uuid'] == uuid and channel['pub_service'] == True:
                    channelNumber = channel['number']
                    streamsList = {}
                    for stream in channel['streams']:
                        streamsList[stream['quality']] = stream['rtsp']

                    tmpQuality = quality
                    while tmpQuality not in streamsList:
                        tmpQuality = self._getLowerQuality(tmpQuality)
                        if not tmpQuality:
                            xbmc.log("[PLUGIN] freeboxTV: prb quality ERROR with uuid:"+uuid,xbmc.LOGFATAL)
                            raise FreeboxHandlerError("[PLUGIN] freeboxTV: prb quality ERROR with uuid:"+uuid)
                            exit

                    rtspUrl = streamsList[tmpQuality]

            return (rtspUrl, channelNumber)
        raise FreeboxHandlerError("[PLUGIN] freeboxTV: API doesn't answer correctly for stream list")
