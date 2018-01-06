import xbmc, xbmcvfs, xbmcaddon
from cron import CronManager,CronJob

from distutils.version import LooseVersion
from resources.lib.handler.oFreebox import cFreeboxHandler


def main:
	settings = xmbcaddon.Addon(id='pvr.freeboxtv')
	
	videoQuality = settings.getSetting("quality")
	appToken = settings.getSetting("app_token")
	trackId = settings.getSetting("track_id")
    
    try:
    	oFreebox = cFreeboxHandler( 'fr.freebox.KodiPVR', 'FreeboxTV for Kodi PVR', '0.1.0', socket.gethostname() )
    	if oFreebox.checkApiVersion():
    		# launch only at first time
    		if not appToken:
    			appToken, trackId = oFreebox.pairingWithFreebox()
    			settings.setSetting("app_token",appToken)
    			settings.setSetting("track_id",trackId)
    		else:
    			#else we check the status of the app_token
    			if oFreebox.checkPairing(trackId):
    			    oFreebox.getSession
    		
    		channelsList = oFreebox.getChannels(videoQuality.lower())
    		
    		# create m3u file
    		with open('special://home/pvr.freeboxtv/freebox.m3u', 'w') as the_file:
                the_file.write('#EXTM3U')
    		    for oChannel in channelsList:
    		        the_file.write(oChannel.getM3ULine())
    		    		        
    		    
    		#record a cron to create xmltv file each hour
            job = CronJob()
            job.name = "refresh_XMLTV_File"
            job.command = "runScript(special://home/addons/pvr.freeboxtv/cron.py,date +%s)"
            job.expression = "0 */1 * * *"
            job.show_notification = "false"	
            
    except oFreeboxHandlerError as e:
        xbmc.log(e.strerror,xbmc.LOGDEBUG)
	
main()