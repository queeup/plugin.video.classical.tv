# -*- coding: utf-8 -*-

# Imports
import os
import sys
import urllib
import urllib2
import time
import datetime
import hashlib
import shutil
import tempfile
import errno
import simplejson
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon

# Debug
DEBUG = False

__addon__ = xbmcaddon.Addon(id='plugin.video.classical.tv')
__info__ = __addon__.getAddonInfo
__plugin__ = __info__('name')
__version__ = __info__('version')
__icon__ = __info__('icon')
__fanart__ = __info__('fanart')
__cachedir__ = __info__('profile')
__language__ = __addon__.getLocalizedString

CACHE_1MINUTE = 60
CACHE_1HOUR = 3600
CACHE_1DAY = 86400
CACHE_1WEEK = 604800
CACHE_1MONTH = 2592000

CACHE_TIME = CACHE_1DAY

URL = 'http://api.adrise.tv/playlists.php?content-owner=brightcove&_=1327339320673'


class Main:
  def __init__(self):
    if ("action=list" in sys.argv[2]):
      self.list_contents()
    else:
      self.main_menu()

  def main_menu(self):
    if DEBUG:
      self.log('main_menu()')
    Main = [{'title':__language__(30201), 'number':6},
            {'title':__language__(30202), 'number':5},
            {'title':__language__(30203), 'number':4},
            {'title':__language__(30204), 'number':3},
            {'title':__language__(30205), 'number':2},
            {'title':__language__(30206), 'number':1},
            {'title':__language__(30207), 'number':0}, ]
    for i in Main:
      listitem = xbmcgui.ListItem(i['title'], iconImage='DefaultFolder.png', thumbnailImage=__icon__)
      url = '%s?action=list&number=%i' % (sys.argv[0], i['number'])
      xbmcplugin.addDirectoryItems(int(sys.argv[1]), [(url, listitem, True)])
    # Sort methods and content type...
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_NONE)
    # End of directory...
    xbmcplugin.endOfDirectory(int(sys.argv[1]), True)

  def list_contents(self):
    if DEBUG:
      self.log('list_contents()')
    json = simplejson.loads(fetcher.fetch(URL))
    for entry in json['items'][int(self.arguments('number'))]['videos']:
      thumb = entry['videoStillURL']
      video = entry['FLVURL']
      shortdesc = entry['shortDescription']
      longdesc = entry['longDescription']
      name = entry['name']
      #id = entry['id']
      more = entry['FLVFullLength']
      _duration = more['videoDuration']
      if _duration >= 3600 * 1000:
          duration = time.strftime('%H:%M:%S', time.gmtime(_duration / 1000))
      else:
        duration = time.strftime('%M:%S', time.gmtime(_duration / 1000))
      size = more['size']
      date = datetime.datetime.fromtimestamp(more['uploadTimestampMillis'] / 1000).strftime('%d.%m.%Y')
      listitem = xbmcgui.ListItem(name, iconImage='DefaultVideo.png', thumbnailImage=thumb)
      listitem.setProperty('IsPlayable', 'true')
      listitem.setProperty('mimetype', 'video/mp4')
      listitem.setInfo(type='video',
                       infoLabels={'title': name,
                                   'label': name,
                                   'plot': longdesc,
                                   'plotoutline': shortdesc,
                                   'size': long(size),
                                   'date': date,
                                   'duration': duration, })
      xbmcplugin.addDirectoryItems(int(sys.argv[1]), [(video, listitem, False)])
    # Content Type
    # Consider putting musicvideos value to setContent. But no plot support on that view.
    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    # Sort methods
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DATE)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_SIZE)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_RUNTIME)
    # End of directory...
    xbmcplugin.endOfDirectory(int(sys.argv[1]), True)

  def arguments(self, arg):
    try:
      _arguments = dict(part.split('=') for part in sys.argv[2][1:].split('&'))
    except KeyError, e:
      return e
    else:
      return urllib.unquote_plus(_arguments[arg])

  def log(self, description):
    xbmc.log("[ADD-ON] '%s v%s': %s" % (__plugin__, __version__, description), xbmc.LOGNOTICE)


class DiskCacheFetcher:
  def __init__(self, cache_dir=None):
    # If no cache directory specified, use system temp directory
    if cache_dir is None:
      cache_dir = tempfile.gettempdir()
    if not os.path.exists(cache_dir):
      try:
        os.mkdir(cache_dir)
      except OSError, e:
        if e.errno == errno.EEXIST and os.path.isdir(cache_dir):
          # File exists, and it's a directory,
          # another process beat us to creating this dir, that's OK.
          pass
        else:
          # Our target dir is already a file, or different error,
          # relay the error!
          raise
    self.cache_dir = cache_dir

  def fetch(self, url, max_age=CACHE_TIME):
    # Use MD5 hash of the URL as the filename
    filename = hashlib.md5(url).hexdigest()
    filepath = os.path.join(self.cache_dir, filename)
    if os.path.exists(filepath):
      if int(time.time()) - os.path.getmtime(filepath) < max_age:
        if DEBUG:
          print 'file exists and reading from cache.'
        return open(filepath).read()
    # Retrieve over HTTP and cache, using rename to avoid collisions
    if DEBUG:
      print 'file not yet cached or cache time expired. File reading from URL and try to cache to disk'
    data = urllib2.urlopen(url).read()
    fd, temppath = tempfile.mkstemp()
    fp = os.fdopen(fd, 'w')
    fp.write(data)
    fp.close()
    shutil.move(temppath, filepath)
    return data

fetcher = DiskCacheFetcher(xbmc.translatePath(__cachedir__))

if __name__ == '__main__':
  Main()