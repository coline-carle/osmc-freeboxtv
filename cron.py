import requests, json, datetime, time, xbmc

#todo    
def main:  
    now = datetime.datetime.now()  
    timestamp = time.mktime(now.timetuple())
    apiResponse = request.get('https://mafreebox.freebox.fr/api/v4/tv/epg/by_time/%d' % timestamp)
    jData = json.loads(apiResponse.content)
    if jData['success']=='true':
        for channel in jData['result']:
            #to finish have to check xmltv file format/syntax
            
    else:
        xbmc.log("pvr.freeboxtv cron can't reach egp")
    
main()