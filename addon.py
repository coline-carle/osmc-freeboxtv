# -*- coding: utf-8 -*-
import xbmc, xbmcaddon
import socket, os
#from cron import CronManager,CronJob

from distutils.version import LooseVersion
from resources.lib.handler.freebox import Freebox as cFreeboxHandler
from resources.lib.handler.exceptions import FreeboxHandlerError
from resources.lib.channel import Channel as cChannel


def main():
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
            with open(userDataPath+'freebox.m3u', 'w') as the_file:
                the_file.write("#EXTM3U\r\n")
                for oChannel in channelsList:
                    xbmc.log("writing m3u for uuid"+oChannel.uuid,xbmc.LOGERROR)
                    the_file.write(oChannel.getM3ULine())

            #record a cron to create xmltv file each hour
            #job = CronJob()
            #job.name = "refresh_XMLTV_File"
            #job.command = "runScript(special://home/addons/pvr.freeboxtv/cron.py,date +%s)"
            #job.expression = "0 */1 * * *"
            #job.show_notification = "false"    
            
    except FreeboxHandlerError as e:
        xbmc.log(str(e),xbmc.LOGERROR)

main()
