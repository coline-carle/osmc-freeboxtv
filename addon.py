# -*- coding: utf-8 -*-
import xbmc, xbmcaddon
import socket, sys, os
#from cron import CronManager,CronJob

from distutils.version import LooseVersion
from resources.lib.handler.freebox import Freebox as cFreeboxHandler
from resources.lib.handler.exceptions import FreeboxHandlerError


def main():
    settings    = xbmcaddon.Addon(id='script.module.freeboxtv')
    appToken   = settings.getSetting("app_token")
    trackId     = settings.getSetting("track_id")
    
    try:
        oFreebox = cFreeboxHandler( 'fr.freebox.KodiPVR', 'FreeboxTV for Kodi PVR', '0.1.0', socket.gethostname(), appToken, trackId )     
        
        appToken, trackId = oFreebox.connect(appToken, trackId)
        settings.setSetting("app_token",appToken)
        settings.setSetting("track_id",str(trackId))
        
        oFreebox.createConfFiles(settings.getSetting("quality".lower()), xbmc.translatePath('special://home/../pvr.freeboxtv/') )
        
        #record a cron to create xmltv file each hour( ? depend of freebox server api :/ )
        #job = CronJob()
        #job.name = "refresh_XMLTV_File"
        #job.command = "runScript(special://home/addons/pvr.freeboxtv/cron.py,date +%s)"
        #job.expression = "0 */1 * * *"
        #job.show_notification = "false"    
    except FreeboxHandlerError, e:
        xbmc.log("[FREEBOXTV]"+str(e),xbmc.LOGERROR)

main()
