# -*- coding: utf-8 -*-
from resources.lib.handler.exceptions import FreeboxHandlerError
from distutils.version import LooseVersion
import xbmc, os, requests, json, hmac, hashlib, time, io

class Freebox:

    # constructor initializ needed variables
    def __init__(self, appId, appName, appVersion, deviceName, appToken='', trackId=''):
        self.apiUrl = 'https://mafreebox.freebox.fr/api/v4'
        self.certPath = xbmc.translatePath('special://home/addons/script.module.freeboxtv/resources/certificate/freebox.crt')
        self.bouquetName = 'Freebox TV'
        self.bouquetId = ''
        self.appId = appId
        self.appName = appName
        self.appVersion = appVersion
        self.deviceName = deviceName
        self.quality = 'auto'
        self.trackId = trackId
        self.appToken = appToken
        self.challenge = ''
        self.session = ''
  
    
    # method for getting jsonData from API
    def _requestJsonData(self, url):
        apiResponse = requests.get(self.apiUrl + url , headers={'X-Fbx-App-Auth': self.session} , verify=self.certPath)
        if apiResponse.ok:
            jData = json.loads(apiResponse.content)
            if jData['success'] == True:
                return jData['result']
            raise FreeboxHandlerError('API '+url+' Not answered as intended - HTTP Status:'+str(apiResponse.status_code)+'-'+str(jData['msg'].encode('utf-8')))
        raise FreeboxHandlerError('API '+url+' Not answered as intended - HTTP Status:'+str(apiResponse.status_code))


    # check 'Freebox TV' bouquet id and memorize it
    def _checkBouquetId(self):
        try:
            jData = self._requestJsonData('/tv/bouquets/')
            for bouquet in jData:
                if bouquet['name'] == self.bouquetName:
                    self.bouquetId = bouquet['id']
            # if no ID returned, it must because they changed the name, so please report issue to update code
            if not self.bouquetId:
                raise FreeboxHandlerError('Bouquet Name seems to have changed report the issue this need to update code')
        except Exception as e:
            raise FreeboxHandlerError('jData:'+str(jData)+' bouquet:'+str(bouquet))


    # method usefull for fallback to immediatly lower quality available if the choosed one in config doesn't exist in stream channel list
    def _getLowerQuality(self, quality):
        if quality == 'hd':
            return 'auto'
        if quality == 'auto':
            return 'sd'
        if quality == 'sd':
            return 'ld'
        return 'hd' # some channel only have hd so fallback if we found nothing else


    # check if freeboxServer is compatible with this Addon, Freebox V1 & V2 are not
    def _checkApiVersion(self):
        apiResponse = requests.get(self.apiUrl + '/api_version', verify=self.certPath)
        jData = json.loads(apiResponse.content)
        if apiResponse.ok and format(len(jData)) > 0:
            jData = json.loads(apiResponse.content)
            if LooseVersion(jData['api_version']) >= '3.0':
                return True
            raise FreeboxHandlerError('FreeBox API not compatible')
            return False
        else:
            raise FreeboxHandlerError('FreeBox API not answered - HTTP Status:'+apiResponse.status_code)
            return False


    # pairing addon with Freebox, user need to validate manually on his freebox the pairing
    def _pairingWithFreebox(self):
        import socket
        payload = {'app_id': self.appId,
           'app_name': self.appName,
           'app_version': self.appVersion,
           'device_name': self.deviceName
           }
        payload = json.dumps(payload)
        apiResponse = requests.post(self.apiUrl + '/login/authorize/', data=payload, verify=self.certPath)
        jData = json.loads(apiResponse.content)
        if not apiResponse.ok and jData['success'] == True:
            raise FreeboxHandlerError('ERROR: ' + jData['msg'])
        self.appToken = jData['result']['app_token']
        self.trackId = jData['result']['track_id']
        return (self.appToken, self.trackId)


    # checking the pairing status, if the token was revoked, or in wait of manual validation
    def _checkPairing(self, trackId):
        apiResponse = requests.get(self.apiUrl + '/login/authorize/' + trackId, verify=self.certPath)
        jData = json.loads(apiResponse.content)
        if not apiResponse.ok and jData['success'] == True:
            raise FreeboxHandlerError(jData['msg'])
        # get the challenge token needed for getting login session
        if jData['result']['status'] == 'granted':
            self.challenge = jData['result']['challenge']
            return True
        if jData['result']['status'] == 'unknown' or jData['result']['status'] == 'denied':
            #TODO: return false to display a popup saying to user to authorize pairing on their freebox
            raise FreeboxHandlerError('Pairing Revoked')
        if jData['result']['status'] == 'pending' or jData['result']['status'] == 'timeout':
            #TODO: return false to display a popup saying to user to authorize pairing on their freebox
            raise FreeboxHandlerError('User not confirmed authorization')
        return False


    # get login session, needed for each request if we don't want to be blacklisted
    def _getSession(self):
        if not (self.appToken and self.challenge):
            raise FreeboxHandlerError('missing value appToken:'+self.appToken+" challenge:"+self.challenge)
        hashed = hmac.new(self.appToken, self.challenge, hashlib.sha1)
        payload = { 'app_id': self.appId, 'password': hashed.hexdigest() }
        data = json.dumps(payload)
        apiResponse = requests.post(self.apiUrl + '/login/session/', data, verify=self.certPath)
        jData = json.loads(apiResponse.content)
        if jData['success'] == True:
            self.session = jData['result']['session_token']
            return True
        raise FreeboxHandlerError('Get Session - ' + str(jData['msg'].encode('utf-8') + "appToken:"+self.appToken+" challenge:"+self.challenge.encode('utf-8')))
        return False


    # unifying channels info with streams info and filter/sort it to return a final list for m3ufile write
    def _filterAndSortChannels(self,channelsList, streamsList):
        lChannels = []
        for channelId in channelsList:
            # we filter channel and don't process unavailable channels
            if channelsList[channelId]['available'] == True:
                # we get the stream uri for the channel in choosed quality and the channel number in same time
                channelNumber = ''
                rtspUrl = ''

                try:
                    streamChannel = (item for item in streamsList if item["uuid"] == channelsList[channelId]['uuid']).next()
                except StopIteration as e:
                    xbmc.log('[FREEBOXTV] no stream found for '+str(channelsList[channelId]['uuid'])+' - '+channelsList[channelId]['name'], xbmc.LOGWARNING)
                # if the channel is not a pub_service, the rtsp is always missing
                if streamChannel['pub_service'] == True:
                    channelNumber = streamChannel['number']
                   
                    # we prepare a dict of stream uri & quality available for the channel
                    lStream = {}
                    for stream in streamChannel['streams']:
                        lStream[stream['quality']] = stream['rtsp']
                        #we search for the nearest of choosed one quality available
                    tmpQuality = self.quality
                    while tmpQuality not in lStream:
                        tmpQuality = self._getLowerQuality(tmpQuality)
                        if not tmpQuality:
                            raise FreeboxHandlerError("Quality unexpected with uuid:"+uuid)
                    rtspUrl = lStream[tmpQuality]
                # we process the channel only if a stream uri is returned
                if rtspUrl:
                    dChannel = {
                        'channelId':channelsList[channelId]['uuid'], 
                        'number':channelNumber,
                        'name':channelsList[channelId]['name'],
                        'shortname':channelsList[channelId]['short_name'], 
                        'logo':self.apiUrl.split('/api')[0]+channelsList[channelId]['logo_url'], 
                        'group':self.bouquetName,
                        'stream':rtspUrl,
                        #'quality':quality
                    }
                    lChannels.append(dChannel)
                if len(lChannels)<=0:
                    raise FreeboxHandlerError("List is empty")
        # we sort the channels list by their official number in the bouquet
        finalChannelsList = sorted(lChannels, key=lambda lChannels: lChannels['number'])
        xbmc.log("[FREEBOXTV]" + str(len(finalChannelsList))+' channels available on 627', xbmc.LOGWARNING)
        return finalChannelsList
    
    # create m3u file
    def _createM3uFile(self,channelsList,userDataPath):
        try:
            if not os.path.exists(userDataPath):
                os.makedirs(userDataPath)
    
            if not channelsList:
                raise FreeboxHandlerError('channel list is empty channelsList:')
                
            with io.open(userDataPath+'freebox.m3u', 'w', encoding='utf-8') as the_file:
                m3uhead = u'#EXTM3U\r\n'
                the_file.write(m3uhead)                
                for dChannel in channelsList:
                    m3uFormat = "#EXTINF:-1 channel-id=\"%d\"tvg-id=\"%s\" tvg-name=\"%s\" tvg-logo=\"%s\" group-title=\"%s\",%s\r\n%s\r\n"
                    m3uline = m3uFormat % (
                        dChannel['number'],
                        dChannel['channelId'], 
                        dChannel['shortname'], 
                        dChannel['logo'], 
                        dChannel['group'], 
                        dChannel['name'], 
                        dChannel['stream']
                    )
                    the_file.write(m3uline)
                return True
        except Exception, e:
            raise FreeboxHandlerError(str(e))

    #####################################
    # Now the three only callable methods #
    #####################################
    
    # all mandatory checks for connexion stability    
    def connect(self, appToken, trackId):
        if self._checkApiVersion():
            # launch only at first time if addon config have no data about connexion
            if not (appToken and trackId):
                appToken, trackId = self._pairingWithFreebox()
                # return the appToken and trackId to write it in addon config
                return appToken, trackId
            #else we check the status of the app_token if we are paired of not
            else:
                # if we are paired then memorize the session 
                if self._checkPairing(trackId):
                    self._getSession()
        return appToken, trackId

    # we create the xmltv file
    # this method is not private because this one will be called externally by cron 
    def createXmlTvFile(self,channelsList,userDataPath):
        if not channelsList:
            raise FreeboxHandlerError('channel list is empty channelsList:')
        
        os.environ['TZ'] = 'Europe/Paris'
        epoch = int(time.mktime(time.localtime()))
        programsList = self._requestJsonData('/tv/epg/by_time/'+str(epoch))

        xmltvLine = (   "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\r\n"
                        "<!DOCTYPE tv SYSTEM \"xmltv.dtd\">\r\n\r\n"
                        "<tv source-info-url=\"http://www.schedulesdirect.org/\" source-info-name=\"Schedules Direct\""
                        " generator-info-name=\"XMLTV/$Id: tv_grab_na_dd.in,v 1.70 2008/03/03 15:21:41 rmeden Exp"
                        " $\" generator-info-url=\"http://www.xmltv.org/\">\r\n"
                    )

        xbmc.log(xmltvLine,xbmc.LOGWARNING)

        for channel in channelsList:
            xmltvLine += (
                "   <channel id=\"%s\">\r\n"
                "       <display-name>%s</display-name>\r\n"
                "       <icon src=\"%s\" />\r\n"
                "   </channel>\r\n"
                ) % (channel['channelId'], channel['name'], channel['logo'])
            
        for channelId,lChannel in programsList.iteritems():
            for programId,lProgram in lChannel.iteritems():
                programStartTS = int(lProgram['date'])
                programEndTS = int(programStartTS) + int(lProgram['duration'])

                xmltvLine += (
                        "   <programme start=\"%s\" stop=\"%s\" channel=\"%s\">\r\n"
                        "       <date>%d</date>\r\n" ) % (
                        time.strftime('%Y%m%d%H%M%S '+str(time.timezone), time.localtime( programStartTS ) ),
                        time.strftime('%Y%m%d%H%M%S '+str(time.timezone), time.localtime( programEndTS ) ),
                        channelId,
                        int(lProgram['date']),
                    )
                if 'title' in lProgram:
                    xmltvLine += "      <title lang=\"fr\">%s</title>\r\n" % lProgram['title']

                if 'category_name' in lProgram:
                    xmltvLine += "      <category lang=\"fr\">%s</category>\r\n" % lProgram['category_name']

                if 'sub_title' in lProgram:
                    xmltvLine += "      <desc lang=\"fr\">%s</desc>\r\n" % lProgram['sub_title']

                if 'category' in lProgram and lProgram['category']==3 and 'episode_number' in lProgram:
                    if not 'season_number' in lProgram:
                        xmltvLine += "      <episode-num system=\"xmltv_ns\">%d</episode-num>\r\n" % lProgram['episode_number']
                    else:
                        xmltvLine += "      <episode-num system=\"xmltv_ns\">%d.%d</episode-num>\r\n"  % (lProgram['season_number'], lProgram['episode_number']) 

                xmltvLine += '   </programme>\r\n'
            
        xmltvLine += '</tv>'
        
        with io.open(userDataPath+'freebox.xml', 'w', encoding='utf-8') as the_file:
            the_file.write(xmltvLine)

    # all steps needed to create xmltv and m3u file
    def createConfFiles(self, quality, userDataPath):
            self.quality = quality
            self._checkBouquetId()

            channelsList    = self._requestJsonData('/tv/channels')
            streamsList     = self._requestJsonData('/tv/bouquets/'+str(self.bouquetId)+'/channels')
            
            finalList = self._filterAndSortChannels(channelsList,streamsList)
            
            self._createM3uFile(finalList, userDataPath)
            self.createXmlTvFile(finalList, userDataPath)
            return True
            
