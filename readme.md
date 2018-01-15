# Description
An XBMC/KODI/OSMC addon which request freebox server for the availables channels list, automaticly generate m3u and xmltv files ready to use for PVR IpTV simple addon   

# Dependencies with other addons
Developped and tested on Krypton 17 osmc (xbmc.python 2.25)
Need jsonmerge lib for python

It need this addons to work : 
* pvr.iptvsimple >= 3.4.0 see: https://github.com/kodi-pvr/pvr.iptvsimple
* service.cronxbmc >= 0.0.9 see: https://github.com/robweber/cronxbmc


# install 
## Manually from git
connect on your osmc/xbmc/kodi, go to ~/.kodi/addons/ and then
```
sudo pip install jsonmerge

#optional do it only if dependencies addons are not already installed
git clone https://github.com/dbuteau/cronxbmc.git service.cronxbmc
#iptv Simple can be found in the official kodi repo

#installing this script
git clone https://github.com/dbuteau/osmc-freeboxtv.git script.module.freeboxtv
```

## from zip via repo
no repo for the moment


# Configure
## script.module.freeboxtv
go to my extension -> programs -> freeboxtv   
click on gear for configure it.   
choose the quality of the stream (SD,LD,auto or HD), click OK, then activate the plugin.
It will generate m3u and xmltv (at each activation, you can force a refresh of file like this) in ~/pvr.freeboxtv  
by default the file are refreshed automaticly each 1hour (you can change that in service.cronxbmc config)

## In pvr.iptvsimple config: 
### General Tab:
* Choose `local` in location 
* target the file `personnal folder/pvr.freeboxtv/freebox.m3u`
### Tv Guide Tab:
* choose `local` in location
* target the file `personnal folder/pvr.freeboxtv/xmltv.xml`
