# -*- coding: utf-8 -*-
class Channel:
    
    def __init__(self,uuid,number,name,shortname,logo,rtsp,quality):
        self.uuid = uuid
        self.number = number
        self.name = name
        self.shortname = shortname
        self.logo = logo 
        self.rtsp = rtsp
        self.quality = quality
        self.group = "Freebox TV"
        self.m3uFormat = "#EXTINF:-1 tvg-id=\"%s\" tvg-name=\"%s\" tvg-logo=\"%s\" group-title=\"%s\",%s\r\n%s\r\n"
            
    def getM3ULine(self):
        m3uline = self.m3uFormat % (self.uuid, self.shortname, self.logo, self.group, str(self.number)+'. '+self.name, self.rtsp)
        return m3uline 
