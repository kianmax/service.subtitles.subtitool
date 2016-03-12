# *-* coding: utf-8 *-*

import urllib, urllib2, base64, StringIO, sys, xbmc
from xml.dom import minidom


class SubTiToolHelper:
    def __init__(self, filename, md5hash):
        self.info = {}
        self.filename = filename
        self.url = "http://www.subtitool.com/api/"
        self.md5hash = md5hash

    def search(self, item, t, langs):
        for language in item["3let_language"]:
            language = "pl" if language == "pol" else language

            fulllang = xbmc.convertLanguage(language, xbmc.ENGLISH_NAME)
            if fulllang == "Persian": fulllang = "Farsi/Persian"

            url = "http://www.subtitool.com/api/?query=" + self.filename + "&Lang=" + langs
            subs = urllib.urlopen(url).read()
            DOMTree = minidom.parseString(subs)
            if DOMTree.getElementsByTagName('Subtitle').length == 0:
                try:
                    url = "http://www.subtitool.com/api/?query=" + self.filename + "&Lang=" + fulllang + "&OR=1"
                    subs = urllib.urlopen(url).read()
                    DOMTree = minidom.parseString(subs)
                except Exception, e:
                    log("Subtitool","Not Found OR")

                try:
                    url = "http://www.subtitool.com/api/?query=" + self.filename + "&Lang=" + fulllang
                    subs = urllib.urlopen(url).read()
                    DOMTree = minidom.parseString(subs)
                except Exception, e:
                    log("Subtitool","Not Found")

        return DOMTree

    def download(self, dllink, language="PL"):

        try:
            response = urllib.urlopen(dllink)
        except urllib2.URLError, e:
            sys.stderr.write(e.message)
            return False

        try:
            srtdata = response.read()
            open(self.filename, "w").write(srtdata)
            return self.filename

        except Exception, e:
            return False

        return False


def log(module, msg):
  xbmc.log((u"### [%s] - %s" % (module,msg,)).encode('utf-8'),level=xbmc.LOGDEBUG )