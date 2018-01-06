class Channel:
    
    def __init__(self,uuid,number,name,shortname,logo,rtsp,quality):
        self.uuid = uuid
        self.number = number
        self.name = name
        self.shortname = shortname
        self.logo = logo 
        self.rtsp = rtsp
        self.quality = quality
        self.m3uFormat = "#EXTINF:-1 tvg-id=\"%s\" tvg-name=\"%s\" tvg-logo=\"%s\" group-title=\"Freebox TV\",%s\r\n%s"
            
    def getM3ULine(self):
        m3uline = self.m3uFormat % (self.uuid, self.shortname, self.logo, self.group, self.number+'. '+self.name, self.rtsp)
        return m3line 
