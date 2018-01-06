# Description
An XBMC/KODI/OSMC addon which request freebox server for the available channels list, and automaticly generate an m3u list for PVR IpTv simple addon  
It request freebox server too for epg and create an XMLTV file each hour by cron  

# Dependencies with other addons
Developped and tested on Krypton 17 (xbmc.python 2.25)

It need and install this addon : 
* pvr.iptvsimple >= 3.4.0 see: https://github.com/kodi-pvr/pvr.iptvsimple
* service.cronxbmc >= 0.0.9 see: https://github.com/robweber/cronxbmc

# install 
* No repo for the moment update coming

## In pvr.iptvsimple config: 
### General Tab:
* Choose `local` in location 
* target the file `personnal folder/pvr.freeboxtv/freebox.m3u`
### Tv Guide Tab:
* choose `local` in location
* target the file `personnal folder/pvr.freeboxtv/xmltv.xml`
### Logo tag
* Choose `internet adress` in location
* write `http://mafreebox.freebox.fr` in base url for logos
* `prefer m3u` for Channel logos 
