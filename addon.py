# -*- coding: utf-8 -*-
import xbmc, xbmcaddon
import socket, sys, os
from cron import CronManager,CronJob
#from service.cronxbmc import CronManager, CronJob

from distutils.version import LooseVersion
from resources.lib.handler.freebox import Freebox as cFreeboxHandler
from resources.lib.handler.exceptions import FreeboxHandlerError


def update():
    settings    = xbmcaddon.Addon(id='script.module.freeboxtv')
    appToken   = settings.getSetting("app_token")
    trackId     = settings.getSetting("track_id")

    try:
        oFreebox = cFreeboxHandler( 'fr.freebox.KodiPVR', 'FreeboxTV for Kodi PVR', '0.1.0', socket.gethostname(), appToken, trackId )

        appToken, trackId = oFreebox.connect(appToken, trackId)
        settings.setSetting("app_token",appToken)
        settings.setSetting("track_id",str(trackId))

        oFreebox.updateXmlTvFile(xbmc.translatePath('special://home/../pvr.freeboxtv/'))
    except Exception, e:
        xbmc.log('[FREEBOX]'+str(e),xbmc.LOGERROR)

def main():
    if len(sys.argv) >0:
        if sys.argv == 'update':
            update()
            
    settings    = xbmcaddon.Addon(id='script.module.freeboxtv')
    appToken    = settings.getSetting("app_token")
    trackId     = settings.getSetting("track_id")
    
    try:
        oFreebox = cFreeboxHandler( 'fr.freebox.KodiPVR', 'FreeboxTV for Kodi PVR', '0.1.0', socket.gethostname(), appToken, trackId )     
        
        appToken, trackId = oFreebox.connect(appToken, trackId)
        settings.setSetting("app_token",appToken)
        settings.setSetting("track_id",str(trackId))
        
        oFreebox.createConfFiles(settings.getSetting("quality".lower()), xbmc.translatePath('special://home/../pvr.freeboxtv/') )

        job = CronJob()
        job.name = "refresh_XMLTV_File"
        job.command = "runScript(script.module.freeboxtv, update)"
        job.expression = "0 */1 * * *"
        job.show_notification = "true"
        job.addon = "script.module.freeboxtv"
        manager = CronManager()
        jobId = manager.addJob(job)

    except FreeboxHandlerError, e:
        xbmc.log("[FREEBOXTV]"+str(e),xbmc.LOGERROR)

main()
