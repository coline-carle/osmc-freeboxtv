# -*- coding: utf-8 -*-
import xbmc, xbmcaddon
import socket, sys, os
#from cron import CronManager,CronJob

from distutils.version import LooseVersion
from resources.lib.handler.freebox import Freebox as cFreeboxHandler
from resources.lib.handler.exceptions import FreeboxHandlerError


def main():
    xbmc.log("[FREEBOXTV]start...",xbmc.LOGERROR)
    settings = xbmcaddon.Addon(id='script.module.freeboxtv')

    videoQuality = settings.getSetting("quality")
    appToken = settings.getSetting("app_token")
    trackId = settings.getSetting("track_id")

    userDataPath = xbmc.translatePath('special://home/pvr.freeboxtv/')
    
    try:
        oFreebox = cFreeboxHandler( 'fr.freebox.KodiPVR', 'FreeboxTV for Kodi PVR', '0.1.0', socket.gethostname() )

        if oFreebox.checkApiVersion():
            # launch only at first time
            if not (appToken and trackId):
                appToken, trackId = oFreebox.pairingWithFreebox()
                settings.setSetting("app_token",appToken)
                settings.setSetting("track_id",str(trackId))
            else:
                #else we check the status of the app_token
                if oFreebox.checkPairing(trackId):
                    oFreebox.getSession

            channelsList = oFreebox.getChannelsList(videoQuality.lower())

            # create m3u file
            if not os.path.exists(userDataPath):
                os.makedirs(userDataPath)
            import io
            with io.open(userDataPath+'freebox.m3u', 'w', encoding='utf-8') as the_file:
                m3uhead = u'#EXTM3U\r\n'
                #m3uhead = m3uhead.encode('utf-8')
                the_file.write(m3uhead)
                for dChannel in channelsList:
                    m3uFormat = "#EXTINF:-1 tvg-id=\"%s\" tvg-name=\"%s\" tvg-logo=\"%s\" group-title=\"%s\",%s\r\n%s\r\n"
                    m3uline = m3uFormat % (
                        dChannel['channelId'], 
                        dChannel['shortname'], 
                        dChannel['logo'], 
                        dChannel['group'], 
                        str(dChannel['number'])+'. '+dChannel['name'], 
                        dChannel['stream']
                    )
                    the_file.write(m3uline)

            #record a cron to create xmltv file each hour
            #job = CronJob()
            #job.name = "refresh_XMLTV_File"
            #job.command = "runScript(special://home/addons/pvr.freeboxtv/cron.py,date +%s)"
            #job.expression = "0 */1 * * *"
            #job.show_notification = "false"    
        xbmc.log("[FREEBOXTV]end.",xbmc.LOGERROR)
    #except Exception, e:
    except FreeboxHandlerError, e:
        xbmc.log("[FREEBOXTV]"+str(e),xbmc.LOGERROR)

main()
