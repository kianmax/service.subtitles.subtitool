# -*- coding: utf-8 -*- 

import os
import sys
import urllib
import unicodedata
import xbmc
import xbmcvfs
import xbmcaddon
import xbmcgui
import xbmcplugin

try:
    # Python 2.6 +
    from hashlib import md5
except ImportError:
    # Python 2.5 and earlier
    from md5 import new as md5

_ADDON = xbmcaddon.Addon()
_SCRIPTID = _ADDON.getAddonInfo('id')
_SCRIPTNAME = _ADDON.getAddonInfo('name')
_VERSION = _ADDON.getAddonInfo('version')
_LANGUAGE = _ADDON.getLocalizedString

_CWD = xbmc.translatePath(_ADDON.getAddonInfo('path')).decode("utf-8")
_PROFILE = xbmc.translatePath(_ADDON.getAddonInfo('profile')).decode("utf-8")
_RESOURCE = xbmc.translatePath(os.path.join(_CWD, 'resources', 'lib')).decode("utf-8")
TEMP_FOLDER = xbmc.translatePath(os.path.join(_PROFILE, 'temp', '')).decode("utf-8")

sys.path.append(_RESOURCE)

from SubTiTool import SubTiToolHelper


def timeout(func, args=(), kwargs={}, timeout_duration=10, default=None):
    import threading

    class InterruptableThread(threading.Thread):
        def __init__(self):
            threading.Thread.__init__(self)
            self.result = "000000000000"

        def run(self):
            self.result = func(*args, **kwargs)

    it = InterruptableThread()
    it.start()
    it.join(timeout_duration)
    if it.isAlive():
        return it.result
    else:
        return it.result


def set_filehash(path, rar):
    d = md5()
    qpath = urllib.quote(path)
    if rar:
        path = """rar://""" + qpath + '/'
        for file in xbmcvfs.listdir(path)[1]:
            if (file.lower().endswith(('.avi', '.mkv', '.mp4'))):
                path = path + file
                break

    d.update(xbmcvfs.File(path, "rb").read(10485760))
    return d


def f(z):
    idx = [0xe, 0x3, 0x6, 0x8, 0x2]
    mul = [2, 2, 5, 4, 3]
    add = [0, 0xd, 0x10, 0xb, 0x5]

    b = []
    for i in xrange(len(idx)):
        a = add[i]
        m = mul[i]
        i = idx[i]

        t = a + int(z[i], 16)
        v = int(z[t:t + 2], 16)
        b.append(("%x" % (v * m))[-1])

    return ''.join(b)


def Search(item,langs):
    d = timeout(set_filehash, args=(item["file_original_path"], item["rar"]), timeout_duration=15)
    md5hash = d.hexdigest()
    t = f(md5hash)
    filename = '.'.join(os.path.basename(item["file_original_path"]).split(".")[:-1])
    helper = SubTiToolHelper(filename, md5hash)
    results = helper.search(item, t, langs)

    if results is None:
        return

    results = results.getElementsByTagName('Subtitle')
    for node in results:
        sTitle = node.getElementsByTagName('TITLE')[0].firstChild.data
        sLang = node.getElementsByTagName('LANGUAGE')[0].firstChild.data
        sTitle = node.getElementsByTagName('TITLE')[0].firstChild.data
        sDlLink = node.getElementsByTagName('DOWNLOADLINK')[0].firstChild.data
        sRate = node.getElementsByTagName('RATE')[0].firstChild.data
        if sLang == "Farsi/Persian": sLang = "Persian"

        listitem = xbmcgui.ListItem(label=sLang,
                                    # language name for the found subtitle
                                    label2=sTitle,  # file name for the found subtitle
                                    iconImage=sRate,  # rating for the subtitle, string 0-5
                                    thumbnailImage=xbmc.convertLanguage(sLang, xbmc.ISO_639_1)
                                    # language flag, ISO_639_1 language + gif extention, e.g - "en.gif"
                                    )
        listitem.setProperty("sync", '{0}'.format("true").lower())  # set to "true" if subtitle is matched by hash,
        # indicates that sub is 100 Comaptible
        listitem.setProperty("hearing_imp",
                             '{0}'.format("false").lower())  # set to "true" if subtitle is for hearing impared

        ## below arguments are optional, it can be used to pass any info needed in download function
        ## anything after "action=download&" will be sent to addon once user clicks listed subtitle to download
        url = "plugin://%s/?action=download&l=%s&f=%s&filename=%s&dllink=%s" % (
            _SCRIPTID, sLang, md5hash, filename, sDlLink)
        ## add it to list, this can be done as many times as needed for all subtitles found
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=listitem, isFolder=False)


def Download(language, hash, filename, dlLink):
    subtitle_list = []
    ## Cleanup temp dir, we recomend you download/unzip your subs in temp folder and
    ## pass that to XBMC to copy and activate
    if xbmcvfs.exists(TEMP_FOLDER):
        xbmcvfs.rmdir(TEMP_FOLDER,True)
    xbmcvfs.mkdirs(TEMP_FOLDER)
    filename = os.path.basename(xbmc.Player().getPlayingFile().decode('utf-8'))
    filename = filename[:filename.rfind(".")] + ".srt"
    filename = os.path.join(TEMP_FOLDER, filename)
    napiHelper = SubTiToolHelper(filename, hash)
    filename = napiHelper.download(dlLink,language)
    subtitle_list.append(filename)  # this can be url, local path or network path.

    return subtitle_list


def normalizeString(str):
    return unicodedata.normalize(
        'NFKD', unicode(unicode(str, 'utf-8'))
    ).encode('ascii', 'ignore')


def get_params():
    param = []
    paramstring = sys.argv[2]
    if len(paramstring) >= 2:
        params = paramstring
        cleanedparams = params.replace('?', '')
        if (params[len(params) - 1] == '/'):
            params = params[0:len(params) - 2]
        pairsofparams = cleanedparams.split('&')
        param = {}
        for i in range(len(pairsofparams)):
            splitparams = {}
            splitparams = pairsofparams[i].split('=')
            if (len(splitparams)) == 2:
                param[splitparams[0]] = splitparams[1]

    return param


params = get_params()

if params['action'] == 'search' or params['action'] == 'manualsearch':
    item = {}
    if 'searchstring' in params:
        item['mansearch'] = True
        item['mansearchstr'] = params['searchstring']
    else:
        item['mansearch'] = False
        item['mansearchstr'] = ''

    item['temp'] = False
    item['rar'] = False
    item['year'] = xbmc.getInfoLabel("VideoPlayer.Year")  # Year
    item['season'] = str(xbmc.getInfoLabel("VideoPlayer.Season"))  # Season
    item['episode'] = str(xbmc.getInfoLabel("VideoPlayer.Episode"))  # Episode
    item['tvshow'] = normalizeString(xbmc.getInfoLabel("VideoPlayer.TVshowtitle"))  # Show
    item['title'] = normalizeString(xbmc.getInfoLabel("VideoPlayer.OriginalTitle"))  # try to get original title
    item['file_original_path'] = urllib.unquote(
        xbmc.Player().getPlayingFile().decode('utf-8'))  # Full path of a playing file
    item['3let_language'] = []
    item['preferredlanguage'] = unicode(urllib.unquote(params.get('preferredlanguage', '')), 'utf-8')
    item['preferredlanguage'] = xbmc.convertLanguage(item['preferredlanguage'], xbmc.ISO_639_2)
    for lang in urllib.unquote(params['languages']).decode('utf-8').split(","):
        item['3let_language'].append(xbmc.convertLanguage(lang, xbmc.ISO_639_2))

    if item['title'] == "":
        item['title'] = normalizeString(xbmc.getInfoLabel("VideoPlayer.Title"))  # no original title, get just Title

    if item['episode'].lower().find("s") > -1:  # Check if season is "Special"
        item['season'] = "0"  #
        item['episode'] = item['episode'][-1:]

    if (item['file_original_path'].find("http") > -1):
        item['temp'] = True

    elif (item['file_original_path'].find("rar://") > -1):
        item['rar'] = True
        item['file_original_path'] = os.path.dirname(item['file_original_path'][6:])

    elif (item['file_original_path'].find("stack://") > -1):
        stackPath = item['file_original_path'].split(" , ")
        item['file_original_path'] = stackPath[0][8:]

    Search(item,params['languages'])

elif params['action'] == 'download':
    ## we pickup all our arguments sent from def Search()
    subs = Download(params["l"], params["f"], params["filename"], params["dllink"])
    ## we can return more than one subtitle for multi CD versions, for now we are still working out how to handle that in XBMC core
    for sub in subs:
        listitem = xbmcgui.ListItem(label=sub)
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=sub, listitem=listitem, isFolder=False)

xbmcplugin.endOfDirectory(int(sys.argv[1]))  ## send end of directory to XBMC
