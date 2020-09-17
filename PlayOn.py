import contextlib
from functools import partial
import threading
import selectors
import argparse
import os
import sys
import shutil
import msvcrt
import subprocess
import time
from http import server, client, HTTPStatus
import socket
import socketserver
import urllib.request, urllib.parse
from io import BytesIO
from xml.dom import minidom
import json
import html
import struct
import hashlib
import base64
import webbrowser
import mimetypes


class log_event:

  def __init__(self, verbosity):
    self.verbosity = verbosity

  def log(self, msg, level):
    if level <= self.verbosity:
      now = time.localtime()
      s_now = '%02d/%02d/%04d %02d:%02d:%02d' % (now.tm_mday, now.tm_mon, now.tm_year, now.tm_hour, now.tm_min, now.tm_sec)
      print(s_now, ':', msg)


class ThreadedDualStackServer(socketserver.ThreadingMixIn, server.HTTPServer):

  def __init__(self, *args, verbosity, auth_ip=None, **kwargs):
    self.logger = log_event(verbosity)
    if auth_ip:
      if isinstance(auth_ip, tuple):
        self.auth_ip = (*auth_ip , socket.gethostbyname(socket.getfqdn()), "127.0.0.1")
      else:
        self.auth_ip = (auth_ip, socket.gethostbyname(socket.getfqdn()), "127.0.0.1")
    else:
      self.auth_ip = None
    server.HTTPServer.__init__(self, *args, **kwargs)
  
  def server_bind(self):
    self.conn_sockets = []
    with contextlib.suppress(Exception):
      self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
    super().server_bind()
    
  def process_request_thread(self, request, client_address):
    self.conn_sockets.append(request)
    self.logger.log('Connexion de %s:%s' % (client_address[0], client_address[1]), 2)
    super().process_request_thread(request, client_address)

  def shutdown(self):
    super().shutdown()
    self.socket.close()

  def server_close(self):
    pass


class MediaBuffer:

  def __init__(self, BufferSize, BufferBlocSize):
    self.content = [None] * BufferSize
    self.bloc_size = BufferBlocSize
    self.w_index = 0
    self.r_indexes = []
    self.create_lock = threading.Lock()
    self.r_event = threading.Event()
    self.w_condition = threading.Condition()
    self.len = 0
    self.t_index = None


class MediaProvider(threading.Thread):

  STATUS_INITIALIZING = 0
  STATUS_ABORTED = 1
  STATUS_RUNNING = 2
  STATUS_COMPLETED = 3
  SCRIPT_PATH = os.path.dirname(sys.argv[0])
  
  SERVER_MODE_AUTO = 0
  SERVER_MODE_SEQUENTIAL = 1
  SERVER_MODE_RANDOM = 2
  SERVER_MODES = ("auto", "séquentiel", "aléatoire")

  @classmethod
  def open_url(cls, url, method=None):
    header = {'User-Agent': 'Lavf'}
    if method:
      if method.upper() == 'HEAD':
        header['Range'] = 'bytes=0-'
    req = urllib.request.Request(url, headers=header, method=method)
    rep = None
    try:
      rep = urllib.request.urlopen(req)
    except:
      pass
    return rep

  def __init__(self, ServerMode, MediaSrc, MediaSrcType=None, MediaStartFrom=None, MediaBuffer=None, MediaBufferAhead=None, MediaMuxContainer=None, MediaSubSrc=None, MediaSubSrcType=None, MediaSubLang=None, MediaSubBuffer=None, MediaProcessProfile=None, FFmpegPort=None, BuildFinishedEvent=None, verbosity=0):
    threading.Thread.__init__(self)
    self.logger = log_event(verbosity)
    self.ServerMode = ServerMode if ServerMode in (MediaProvider.SERVER_MODE_SEQUENTIAL, MediaProvider.SERVER_MODE_RANDOM) else MediaProvider.SERVER_MODE_AUTO
    self.MediaSrc = MediaSrc
    self.MediaSrcType = MediaSrcType
    self.MediaStartFrom = MediaStartFrom if not MediaStartFrom in (None, '0', '0:00', '00:00', '0:00:00', '00:00:00') else ''
    self.MediaBuffer = MediaBuffer
    if MediaBuffer:
      self.MediaBufferSize = len(MediaBuffer.content)
      self.MediaBufferAhead = MediaBufferAhead
    else:
      self.MediaBufferSize = 0
      self.MediaBufferAhead = 0
    if FFmpegPort:
      if MediaMuxContainer:
        self.MediaMuxAlways = MediaMuxContainer[0:1] == '!'
      else:
        self.MediaMuxAlways = None
        self.MediaMuxContainer = None
      if self.MediaMuxAlways:
        self.MediaMuxContainer = MediaMuxContainer[1:]
      else:
        self.MediaMuxContainer = MediaMuxContainer
      if self.MediaMuxContainer:
        self.ffmpeg_server_url = 'http://localhost:%s' % FFmpegPort
        if self.ServerMode == MediaProvider.SERVER_MODE_RANDOM:
          self.MediaMuxAlways = None
          self.MediaMuxContainer = None
      else:
        self.ffmpeg_server_url = ''
        self.MediaMuxAlways = None
        self.MediaMuxContainer = None
    else:
      self.ffmpeg_server_url = ''
      self.MediaMuxAlways = None
      self.MediaMuxContainer = None
    if self.ServerMode == MediaProvider.SERVER_MODE_AUTO:
      if self.MediaMuxAlways:
        self.ServerMode = MediaProvider.SERVER_MODE_SEQUENTIAL
      if not self.MediaMuxContainer:
        self.ServerMode = MediaProvider.SERVER_MODE_RANDOM
    self.FFmpeg_process = None
    if MediaSubBuffer:
      self.MediaSubBuffer = MediaSubBuffer
      if (not MediaSubBuffer[1] if len(MediaSubBuffer) == 2 else True):
        if MediaSubSrc:
          self.MediaSubSrc = MediaSubSrc
          self.MediaSubSrcType = MediaSubSrcType
          self.MediaSubLang = MediaSubLang
          self.MediaSubBuffer.clear()
          self.MediaSubBuffer.append(b'')
          self.MediaSubBuffer.append('')
        else:
          self.MediaSubSrc = None
          self.MediaSubSrcType = None
          self.MediaSubLang = None
      else:
        self.MediaSubSrc = ''
    else:
      self.MediaSubSrc = None
      self.MediaSubSrcType = None
      self.MediaSubLang = None
    self.FFmpeg_sub_process = None
    self.MediaProcessProfile = MediaProcessProfile if MediaProcessProfile else ''
    self.Connection = None
    self.Persistent = None
    self.AcceptRanges = None
    self.MediaFeed = None
    self.MediaFeedExt = None
    self.MediaSize = None
    self.MediaTitle = ''
    self.Status = None
    self.shutdown_requested = False
    if isinstance(BuildFinishedEvent, threading.Event):
      self.BuildFinishedEvent = BuildFinishedEvent
    else:
      self.BuildFinishedEvent = threading.Event()

  def _open_FFmpeg(self, vid=None, aud=None, sub=None, in_sub_buffer=None, out_sub_buffer=None):
    if not vid and not (sub and out_sub_buffer):
      return None
    ffmpeg_env = {'mediabuilder_address': '-' if sub else self.ffmpeg_server_url, 'mediabuilder_start': self.MediaStartFrom, 'mediabuilder_mux': self.MediaMuxContainer if vid else 'SRT', 'mediabuilder_profile': self.MediaProcessProfile}
    ffmpeg_env['mediabuilder_vid'] = '"%s"' % (vid) if vid else ''
    ffmpeg_env['mediabuilder_aud'] = '"%s"' % (aud) if aud else ''
    ffmpeg_env['mediabuilder_sub'] = '-' if in_sub_buffer else ('"%s"' % (sub) if sub else '')
    ffmpeg_env['mediabuilder_lang'] = '%s' % (self.MediaSubLang) if sub and self.MediaSubLang else ''
    media_feed = None
    while True:
      if not sub:
        self.FFmpeg_process = subprocess.Popen(r'"%s\%s"' % (MediaProvider.SCRIPT_PATH, 'ffmpeg.bat'), env={**os.environ,**ffmpeg_env}, creationflags=subprocess.CREATE_NEW_CONSOLE, startupinfo=subprocess.STARTUPINFO(dwFlags=subprocess.STARTF_USESHOWWINDOW, wShowWindow=6))
        media_feed = None
        while not media_feed and self.FFmpeg_process.poll() == None and not self.shutdown_requested:
          try:
            media_feed = urllib.request.urlopen(self.ffmpeg_server_url)
          except:
            pass
        time.sleep(0.5)
        if self.FFmpeg_process.poll() in (None, 0):
          break
        if media_feed:
          try:
            media_feed.close()
          except:
            pass
        media_feed = None
      else:
        if self.ServerMode == MediaProvider.SERVER_MODE_RANDOM:
          ffmpeg_env['mediabuilder_start'] = ''
        self.FFmpeg_sub_process = subprocess.Popen(r'"%s\%s"' % (MediaProvider.SCRIPT_PATH, 'ffmpeg.bat'), env={**os.environ,**ffmpeg_env}, stdin=None if not in_sub_buffer else subprocess.PIPE, stdout=subprocess.PIPE, creationflags=subprocess.CREATE_NEW_CONSOLE, startupinfo=subprocess.STARTUPINFO(dwFlags=subprocess.STARTF_USESHOWWINDOW, wShowWindow=6))
        out_sub_buffer[0] = self.FFmpeg_sub_process.communicate(input=None if not in_sub_buffer else in_sub_buffer, timeout=30)[0]
        if out_sub_buffer[0]:
          out_sub_buffer[1] = '.srt'
          break
      if self.shutdown_requested:
        break
      if ffmpeg_env['mediabuilder_mux'][-2] != '-' :
        ffmpeg_env['mediabuilder_mux'] = ffmpeg_env['mediabuilder_mux'] + '-'
      else:
        break
    return media_feed

  def MediaBuilder(self):
    if not self.MediaBuffer and self.ServerMode in (MediaProvider.SERVER_MODE_AUTO, MediaProvider.SERVER_MODE_SEQUENTIAL):
      return False
    if not mimetypes.inited:
      mimetypes.init()
    if not self.MediaSrcType:
      if r'://' in self.MediaSrc:
        self.MediaSrcType = 'WebPageURL'
        if '.' in self.MediaSrc[-5:]:
          media_mime = mimetypes.guess_type(self.MediaSrc)[0]
          if media_mime:
            if media_mime[0:5] in ('video', 'audio', 'image'):
              self.MediaSrcType = 'ContentURL'
      else:
        self.MediaSrcType = 'ContentPath'
    if self.MediaSubSrc and not self.MediaSubSrcType:
      sub_ext = (''.join(self.MediaSubSrc.rstrip().rpartition('.')[-2:])).lower() if '.' in self.MediaSubSrc else ''
      if r'://' in self.MediaSubSrc:
        if '?' in sub_ext:
          sub_ext = sub_ext.rpartition('?')[0]
        if sub_ext in ('.ttxt', '.txt', '.smi', '.srt', '.sub', '.ssa', '.ass', '.vtt', '.m3u8'):
          self.MediaSubSrcType = 'ContentURL'
        else:
          self.MediaSubSrcType = 'WebPageURL'
      else:
        self.MediaSubSrcType = 'ContentPath'
    if self.MediaSrcType.lower() == 'ContentPath'.lower() and not self.MediaMuxAlways and self.ServerMode != MediaProvider.SERVER_MODE_SEQUENTIAL and self.MediaSubSrc == None and self.MediaSubBuffer:
      for sub_ext in ('.ttxt', '.txt', '.smi', '.srt', '.sub', '.ssa', '.ass'):
        if os.path.exists(self.MediaSrc.rsplit(".", 1)[0] + sub_ext):
          self.MediaSubSrc = self.MediaSrc.rsplit(".", 1)[0] + sub_ext
          self.MediaSubSrcType = 'ContentPath'
          break
    if self.MediaSubSrc:
      MediaSubFeed = None
      sub_ext = None
      MediaSubBuffer = None
      if self.MediaSubSrcType.lower() == 'ContentPath'.lower():
        try:
          sub_ext = (''.join(self.MediaSubSrc.rstrip().rpartition('.')[-2:])).lower() if '.' in self.MediaSubSrc else ''
        except:
          pass
      elif self.MediaSubSrcType.lower() == 'ContentURL'.lower():
        try:
          MediaSubFeed = MediaProvider.open_url(self.MediaSubSrc)
          sub_ext = (''.join(MediaSubFeed.url.rstrip().rpartition('.')[-2:])).lower() if '.' in MediaSubFeed.url else ''
          if '?' in sub_ext:
            sub_ext = sub_ext.rpartition('?')[0]
        except:
          pass
      elif self.MediaSubSrcType.lower() == 'WebPageURL'.lower():
        sub_url = None
        try:
          process_result = subprocess.run(r'"%s\%s" %s' % (MediaProvider.SCRIPT_PATH, 'youtube-dl.bat', 'sub'), env={**os.environ, 'mediabuilder_url': '"%s"' % (self.MediaSubSrc), 'mediabuilder_lang': '%s' % (self.MediaSubLang), 'mediabuilder_profile': self.MediaProcessProfile}, capture_output=True)
          if process_result.returncode == 0 and not self.shutdown_requested:
            process_result_file = BytesIO(process_result.stdout)
            process_output = json.load(process_result_file)
            sub_url = list(process_output['requested_subtitles'].values())[0]['url']
        except:
          pass
        if not sub_url and not self.shutdown_requested:
          sub_lang = self.MediaSubLang.partition(',')[0].encode('utf-8') if self.MediaSubLang else b''
          try:
            rep = MediaProvider.open_url(self.MediaSubSrc)
            page = rep.read(1000000)
            rep.close()
            sub_url = None
            tracks = None
            try:
              tracks = (s.split(b'>')[0].split() for s in page.split(b'<track')[1:])
            except:
              pass
            if tracks:
              sub_url_lang = None
              sub_url_label = None
              for track in tracks:
                try:    
                  dic_track = {kv[0]:kv[1] for kv in (p.split(b'=') for p in track) if len(kv)==2}
                  if not sub_url:
                    sub_url = html.unescape(dic_track.get(b'src').decode('utf-8'))[1:-1]
                    if not sub_lang:
                      break
                  if sub_lang in dic_track.get(b'srclang','').lower():
                    sub_url_lang = html.unescape(dic_track.get(b'src').decode('utf-8'))[1:-1]
                    break
                  if sub_lang in dic_track.get(b'label','').lower():
                    if not sub_url_label:
                      sub_url_label = html.unescape(dic_track.get(b'src').decode('utf-8'))[1:-1]
                except:
                  pass
              if sub_url_lang:
                sub_url = sub_url_lang
              elif sub_url_label:
                sub_url = sub_url_label
              if sub_url:
                if not 'http' in sub_url[0:4].lower():
                  if sub_url[0] == '/':
                    sub_url = '/'.join(self.MediaSubSrc.split('/')[0:3]) + sub_url
                  elif sub_url[0] == '../':
                    sub_url = '/'.join(self.MediaSubSrc.split('/')[:-2]) + sub_url[2:]
                  else:
                    sub_url = '/'.join(self.MediaSubSrc.split('/')[:-1] + [sub_url])
            if not sub_url and not self.shutdown_requested:
              tracks = None
              try:
                tracks_srt = (b'http' + s.split(b'http')[-1] + b'.srt' for s in page.split(b'.srt')[:-1] if b'http' in s)
                tracks_vtt = (b'http' + s.split(b'http')[-1] + b'.vtt' for s in page.split(b'.vtt')[:-1] if b'http' in s)
                tracks = list(track for track in tracks_srt if not b'\n' in track) + list(track for track in tracks_vtt if not b'\n' in track)
              except:
                pass
              if tracks:
                if sub_lang:
                  len_pos = list((len(track),track.lower().rfind(sub_lang)) for track in tracks)
                  ind = min(range(len(len_pos)), key=lambda i: len_pos[i][0]-len_pos[i][1] if len_pos[i][1] >=0 else 1000000)
                else:
                  ind = 0
                sub_url = html.unescape(tracks[ind].decode('utf-8'))
          except:
            pass
        if sub_url and not self.shutdown_requested:
          try:
            MediaSubFeed = MediaProvider.open_url(sub_url)
            sub_ext = (''.join(MediaSubFeed.url.rstrip().rpartition('.')[-2:])).lower() if '.' in MediaSubFeed.url else ''
            if '?' in sub_ext:
              sub_ext = sub_ext.rpartition('?')[0]
          except:
            pass
      if MediaSubFeed:
        if not self.shutdown_requested:
          try:
            MediaSubBuffer = MediaSubFeed.read(1000000)
            if len(MediaSubBuffer) == 1000000:
              MediaSubBuffer = b''
          except:
            pass
        try:
          MediaSubFeed.close()
        except:
          pass
        MediaSubFeed = None
    if self.shutdown_requested:
      return None
    if self.MediaSrcType.lower() == 'ContentPath'.lower():
      if os.path.exists(self.MediaSrc):
        try:
          if self.ServerMode == MediaProvider.SERVER_MODE_SEQUENTIAL:
            if self.MediaMuxContainer and (self.MediaMuxAlways or self.MediaStartFrom):
              self.MediaFeed = self._open_FFmpeg(vid=self.MediaSrc)
              self.MediaFeedExt = {'MP4':'.mp4','MPEGTS':'.ts'}.get(self.MediaMuxContainer,'')
            else:
              self.MediaFeed = open(self.MediaSrc, "rb")
              self.MediaFeedExt = (''.join(self.MediaSrc.rstrip().rpartition('.')[-2:])).lower() if '.' in self.MediaSrc else ''
              self.MediaStartFrom = ''
          else:
            self.ServerMode = MediaProvider.SERVER_MODE_RANDOM
            self.MediaFeed = self.MediaSrc
            self.MediaFeedExt = (''.join(self.MediaSrc.rstrip().rpartition('.')[-2:])).lower() if '.' in self.MediaSrc else ''
            self.MediaSize = os.path.getsize(self.MediaSrc)
            self.AcceptRanges = True
          self.MediaTitle = self.MediaSrc.rsplit('\\', 1)[-1][:501]
        except:
          pass
    elif self.MediaSrcType.lower() == 'ContentURL'.lower():
      try:
        if self.ServerMode != MediaProvider.SERVER_MODE_SEQUENTIAL:
          rep = MediaProvider.open_url(self.MediaSrc, 'HEAD')
          self.MediaSize = int(rep.getheader('Content-Length'))
          if rep.getheader('Accept-Ranges'):
            if rep.getheader('Accept-Ranges').lower() != 'none':
              self.AcceptRanges = True
            else:
              self.AcceptRanges = False
          elif rep.status == HTTPStatus.PARTIAL_CONTENT:
            self.AcceptRanges = True
          else:
            self.AcceptRanges = False
          if self.ServerMode == MediaProvider.SERVER_MODE_RANDOM:
            if self.MediaSize:
              self.MediaFeed = rep.url
              self.MediaFeedExt = (''.join(rep.url.rstrip().rpartition('.')[-2:])).lower() if '.' in rep.url else ''
            if not self.AcceptRanges:
              self.MediaStartFrom = ''
          elif self.MediaSize and self.AcceptRanges:
            self.ServerMode = MediaProvider.SERVER_MODE_RANDOM
            self.MediaFeed = rep.url
            self.MediaFeedExt = (''.join(rep.url.rstrip().rpartition('.')[-2:])).lower() if '.' in rep.url else ''
          else:
            self.ServerMode = MediaProvider.SERVER_MODE_SEQUENTIAL
          rep.close()
        if self.ServerMode == MediaProvider.SERVER_MODE_SEQUENTIAL:
          if self.MediaMuxContainer and (self.MediaMuxAlways or self.MediaStartFrom):
            self.MediaFeed = self._open_FFmpeg(vid=self.MediaSrc)
            self.MediaFeedExt = {'MP4':'.mp4','MPEGTS':'.ts'}.get(self.MediaMuxContainer,'')
          else:
            self.MediaFeed = MediaProvider.open_url(self.MediaSrc)
            self.MediaFeedExt = (''.join(self.MediaFeed.url.rstrip().rpartition('.')[-2:])).lower() if '.' in self.MediaFeed.url else ''
            self.MediaStartFrom = ''
        if self.MediaFeedExt:
          if '?' in self.MediaFeedExt:
            self.MediaFeedExt = self.MediaFeedExt.rpartition('?')[0]
        self.MediaTitle = self.MediaSrc.rsplit('/', 1)[-1][:501]
      except:
        pass
    elif self.MediaSrcType.lower() == 'WebPageURL'.lower():
      try:
        process_result = subprocess.run(r'"%s\%s" %s' % (MediaProvider.SCRIPT_PATH, 'youtube-dl.bat', 'mux' if self.MediaMuxAlways or self.ServerMode == MediaProvider.SERVER_MODE_AUTO else 'nomux'), env={**os.environ, 'mediabuilder_url': '"%s"' % (self.MediaSrc), 'mediabuilder_profile': self.MediaProcessProfile, }, capture_output=True)
        if process_result.returncode == 0 and not self.shutdown_requested:
          process_output = process_result.stdout.splitlines()
          process_output.reverse()
          del process_output[0]
          if b'###PlayOn_Separator###' in process_output:
            del process_output[process_output.index(b'###PlayOn_Separator###'):]
          self.MediaTitle = process_output.pop(-1).decode('utf-8')[:501]
          if (self.MediaMuxAlways or self.ServerMode == MediaProvider.SERVER_MODE_AUTO) and len(process_output) == 2:
            self.MediaFeed = self._open_FFmpeg(vid=process_output[1].decode('utf-8'), aud=process_output[0].decode('utf-8'))
            self.MediaFeedExt = {'MP4':'.mp4','MPEGTS':'.ts'}.get(self.MediaMuxContainer,'')
            self.ServerMode = MediaProvider.SERVER_MODE_SEQUENTIAL
          elif len(process_output) == 1:
            if self.ServerMode == MediaProvider.SERVER_MODE_AUTO and self.MediaMuxContainer and b'.m3u8' in process_output[0]:
              self.ServerMode = MediaProvider.SERVER_MODE_SEQUENTIAL
            if self.ServerMode != MediaProvider.SERVER_MODE_SEQUENTIAL:
              rep = MediaProvider.open_url(process_output[0].decode('utf-8'), 'HEAD')
              self.MediaSize = int(rep.getheader('Content-Length'))
              if rep.getheader('Accept-Ranges'):
                if rep.getheader('Accept-Ranges').lower() != 'none':
                  self.AcceptRanges = True
                else:
                  self.AcceptRanges = False
              elif rep.status == HTTPStatus.PARTIAL_CONTENT:
                self.AcceptRanges = True
              else:
                self.AcceptRanges = False
              if self.ServerMode == MediaProvider.SERVER_MODE_RANDOM:
                if self.MediaSize:
                  self.MediaFeed = rep.url
                  self.MediaFeedExt = (''.join(rep.url.rstrip().rpartition('.')[-2:])).lower() if '.' in rep.url else ''
                  if not self.AcceptRanges:
                    self.MediaStartFrom = ''
              elif self.MediaSize and self.AcceptRanges:
                self.ServerMode = MediaProvider.SERVER_MODE_RANDOM
                self.MediaFeed = rep.url
                self.MediaFeedExt = (''.join(rep.url.rstrip().rpartition('.')[-2:])).lower() if '.' in rep.url else ''
              else:
                self.ServerMode = MediaProvider.SERVER_MODE_SEQUENTIAL
              if not self.AcceptRanges:
                self.MediaStartFrom = ''
              rep.close()
            if self.ServerMode == MediaProvider.SERVER_MODE_SEQUENTIAL:
              if self.MediaMuxContainer and (self.MediaMuxAlways or self.MediaStartFrom or b'.m3u8' in process_output[0]):
                self.MediaFeed = self._open_FFmpeg(vid=process_output[0].decode('utf-8'))
                self.MediaFeedExt = {'MP4':'.mp4','MPEGTS':'.ts'}.get(self.MediaMuxContainer,'')
              else:
                self.MediaFeed = MediaProvider.open_url(process_output[0].decode('utf-8'))
                self.MediaFeedExt = (''.join(self.MediaFeed.url.rstrip().rpartition('.')[-2:])).lower() if '.' in self.MediaSubFeed.url else ''
                self.MediaStartFrom = ''
          if self.MediaFeedExt:
            if '?' in self.MediaFeedExt:
              self.MediaFeedExt = self.MediaFeedExt.rpartition('?')[0]
      except:
        pass
    if not self.shutdown_requested:
      if self.MediaFeed:
        self.logger.log('Ouverture de "%s" reconnu comme "%s" en mode "%s" - titre: %s' % (self.MediaSrc, self.MediaSrcType, MediaProvider.SERVER_MODES[self.ServerMode], self.MediaTitle), 1)
        if self.MediaFeedExt:
          media_mime = mimetypes.guess_type('f' + self.MediaFeedExt)[0]
          if media_mime:
            if not media_mime[0:5] in ('video', 'audio', 'image'):
              self.MediaFeedExt = ''
          else:
            self.MediaFeedExt = ''
        else:
          self.MediaFeedExt = ''
        if not self.MediaFeedExt and self.ServerMode == MediaProvider.SERVER_MODE_RANDOM:
          if 'mp4' in self.MediaFeed.lower():
            self.MediaFeedExt = '.mp4'
        self.logger.log('Extension de "%s" retenue comme "%s"' % (self.MediaSrc, self.MediaFeedExt), 2)
        if self.MediaSubSrc:
          if self.MediaSubSrcType.lower() == 'ContentPath'.lower():
            try:
              if not sub_ext in ('.ttxt', '.txt', '.smi', '.srt', '.sub', '.ssa', '.ass') or (self.ServerMode == MediaProvider.SERVER_MODE_SEQUENTIAL and (self.MediaStartFrom or self.MediaMuxAlways)):
                self._open_FFmpeg(sub=self.MediaSubSrc, in_sub_buffer=None, out_sub_buffer=self.MediaSubBuffer)
              else:
                MediaSubFeed = open(self.MediaSubSrc, "rb")
                try:
                  self.MediaSubBuffer[0] = MediaSubFeed.read(1000000)
                  if len(self.MediaSubBuffer[0]) == 1000000:
                    self.MediaSubBuffer[0] = b''
                  else:
                    self.MediaSubBuffer[1] = sub_ext
                except:
                  pass
                try:
                  MediaSubFeed.close()
                except:
                  pass
              MediaSubFeed = None
            except:
              pass
          elif MediaSubBuffer:
            try:
              if not sub_ext in ('.ttxt', '.txt', '.smi', '.srt', '.sub', '.ssa', '.ass') or (self.ServerMode == MediaProvider.SERVER_MODE_SEQUENTIAL and (self.MediaStartFrom or self.MediaMuxAlways)):
                self._open_FFmpeg(sub='-', in_sub_buffer=MediaSubBuffer, out_sub_buffer=self.MediaSubBuffer)
              else:
                self.MediaSubBuffer[0] = MediaSubBuffer
                self.MediaSubBuffer[1] = sub_ext
            except:
              pass
          if self.MediaSubBuffer[0]:
            self.logger.log('Ouverture des sous-titres "%s" reconnus comme "%s"' % (self.MediaSubSrc, self.MediaSubSrcType), 1)
            self.logger.log('Extension des sous_titres retenue comme "%s"' % self.MediaSubBuffer[1], 2)
          else:
            self.logger.log('Échec de l\'ouverture des sous-titres "%s" en tant que "%s"' % (self.MediaSubSrc, self.MediaSubSrcType), 0)
        return True
      else:
        self.logger.log('Échec de l\'ouverture de "%s" en tant que "%s"' % (self.MediaSrc, self.MediaSrcType), 0)
        return False
    else:
      return None

  def MediaFeederS(self):
    if not self.MediaBuffer:
      return
    self.logger.log('Début du chargement dans le tampon du contenu', 1)
    self.MediaBuffer.w_index = 1
    while self.Status != MediaProvider.STATUS_ABORTED and not self.shutdown_requested and self.MediaBuffer.w_index > 0:
      while self.Status != MediaProvider.STATUS_ABORTED and not self.shutdown_requested and self.MediaBuffer.w_index <= max(max(self.MediaBuffer.r_indexes, default=0), 1) + self.MediaBufferAhead:
        bloc = None
        try:
          bloc = self.MediaFeed.read(self.MediaBuffer.bloc_size)
        except:
          self.Status = MediaProvider.STATUS_ABORTED
          self.logger.log('Segment %d -> échec de lecture du contenu' % (self.MediaBuffer.w_index), 1)
        if not bloc:
          self.MediaBuffer.w_index = - abs(self.MediaBuffer.w_index)
          break
        else:
          self.MediaBuffer.content[(self.MediaBuffer.w_index - 1) % self.MediaBufferSize] = bloc
          self.logger.log('Segment %d -> placement dans la zone %d du tampon' % (self.MediaBuffer.w_index, (self.MediaBuffer.w_index - 1) % self.MediaBufferSize), 2)
          self.MediaBuffer.w_index += 1
          self.MediaBuffer.w_condition.acquire()
          self.MediaBuffer.w_condition.notify_all()
          self.MediaBuffer.w_condition.release()
      if self.Status != MediaProvider.STATUS_ABORTED and not self.shutdown_requested and self.MediaBuffer.w_index > 0:
        self.MediaBuffer.r_event.wait()
        self.MediaBuffer.r_event.clear()
    if self.Status != MediaProvider.STATUS_ABORTED and not self.shutdown_requested:
      self.Status = MediaProvider.STATUS_COMPLETED
      self.logger.log('Fin du chargement dans le tampon du contenu', 1)
    else:
      self.logger.log('Interruption du chargement dans le tampon du contenu', 1)
    self.MediaBuffer.w_condition.acquire()
    self.MediaBuffer.w_condition.notify_all()
    self.MediaBuffer.w_condition.release()
    try:
      self.MediaFeed.close()
    except:
      pass

  def MediaFeederR(self):
    if not self.MediaSize:
      return
    self.logger.log('Début du chargement dans le tampon du contenu', 1)
    header = {'User-Agent': 'Lavf'}
    header['Range'] = 'bytes=0-'
    header['Connection'] = 'keep-alive'
    rep = None
    try:
      url = urllib.parse.urlparse(self.MediaFeed)
      self.MediaSrcURL = self.MediaFeed[len(url.scheme) + 3 + len(url.netloc):]
      if url.scheme.lower() == 'http':
        self.Connection = client.HTTPConnection(url.netloc)
      elif url.scheme.lower() == 'https':
        self.Connection = client.HTTPSConnection(url.netloc)
      self.Connection.request('HEAD', self.MediaSrcURL, headers=header)
      rep = self.Connection.getresponse()
      self.Persistent = not rep.will_close
      self.logger.log('Connexion pour diffusion de "%s": persistente=%s - requêtes partielles=%s' % (self.MediaFeed, 'vrai' if self.Persistent else 'faux', 'vrai' if self.AcceptRanges else 'faux'), 2)
    except:
      self.Status = MediaProvider.STATUS_ABORTED
    if rep:
      try:
        rep.read()
        rep.close()
      except:
        pass
    rep = None
    while self.Status != MediaProvider.STATUS_ABORTED and not self.shutdown_requested:
      self.MediaBuffer.create_lock.acquire()
      t_index = None
      r_index = None
      for ind in range(len(self.MediaBuffer.r_indexes) - 1, -1, -1):
        if self.MediaBuffer.r_indexes[ind] != 0:
          t_index = ind
          break
      self.MediaBuffer.create_lock.release()
      if t_index != None:
        if self.MediaBuffer.t_index != t_index:
          self.MediaBuffer.t_index = t_index
          self.logger.log('Indexation du tampon sur la connexion %d' % (self.MediaBuffer.t_index + 1), 2)
          self.MediaBuffer.w_condition.acquire()
          self.MediaBuffer.w_condition.notify_all()
          self.MediaBuffer.w_condition.release()
        r_index = self.MediaBuffer.r_indexes[t_index]
      elif self.MediaBuffer.t_index != None:
        self.MediaBuffer.t_index = None
        self.logger.log('Désindexation du tampon', 2)
      if r_index and (r_index -1) * self.MediaBuffer.bloc_size < self.MediaSize:
        if r_index < self.MediaBuffer.w_index or ((r_index if self.AcceptRanges else 1) > self.MediaBuffer.w_index + self.MediaBuffer.len):
          self.MediaBuffer.w_condition.acquire()
          if r_index < self.MediaBuffer.w_index:
            self.MediaBuffer.content = [None] * min(self.MediaBuffer.w_index - (r_index if self.AcceptRanges else 1), self.MediaBufferSize) + self.MediaBuffer.content[:(r_index if self.AcceptRanges else 1) - self.MediaBuffer.w_index]
          else:
            self.MediaBuffer.content = self.MediaBuffer.content[r_index - self.MediaBuffer.w_index:] + [None] * min(r_index - self.MediaBuffer.w_index, self.MediaBufferSize)
          self.MediaBuffer.w_index = r_index if self.AcceptRanges else 1
          self.MediaBuffer.len = 0
          self.MediaBuffer.w_condition.release()
          self.logger.log('Translation du tampon vers la position %d' % self.MediaBuffer.w_index, 2)
          if rep:
            try:
              rep.close()
            except:
              pass
          rep = None
        if self.Status != MediaProvider.STATUS_ABORTED and not self.shutdown_requested and self.MediaBuffer.w_index + self.MediaBuffer.len <= self.MediaBuffer.r_indexes[t_index] + self.MediaBufferAhead and (self.MediaBuffer.w_index + self.MediaBuffer.len - 1) * self.MediaBuffer.bloc_size < self.MediaSize:
          if self.MediaBuffer.len < self.MediaBufferSize:
            if self.MediaBuffer.content[self.MediaBuffer.len] and self.AcceptRanges and not rep:
              self.MediaBuffer.len += 1
              self.logger.log('Segment %d -> déjà présent dans la zone %d du tampon' % (self.MediaBuffer.w_index + self.MediaBuffer.len - 1, self.MediaBuffer.len), 2)
              self.MediaBuffer.w_condition.acquire()
              self.MediaBuffer.w_condition.notify_all()
              self.MediaBuffer.w_condition.release()
              continue
          bloc = None
          try:
            header = {'User-Agent': 'Lavf'}
            if self.Persistent and self.AcceptRanges:
              header['Range'] = 'bytes=%d-%d' % ((self.MediaBuffer.w_index + self.MediaBuffer.len - 1) * self.MediaBuffer.bloc_size, min(self.MediaSize, (self.MediaBuffer.w_index + self.MediaBuffer.len) * self.MediaBuffer.bloc_size) - 1)
              header['Connection'] = 'keep-alive'
              self.Connection.request('GET', self.MediaSrcURL, headers=header)
              rep = self.Connection.getresponse()
              bloc = rep.read(self.MediaBuffer.bloc_size)
              rep.close()
              rep = None
            else:
              if rep == None:
                try:
                  self.Connection.close()
                except:
                  pass
                header = {'User-Agent': 'Lavf'}
                if self.AcceptRanges:
                  header['Range'] = 'bytes=%d-' % ((self.MediaBuffer.w_index + self.MediaBuffer.len - 1) * self.MediaBuffer.bloc_size)
                self.Connection.request('GET', self.MediaSrcURL, headers=header)
                rep = self.Connection.getresponse()
              bloc = rep.read(self.MediaBuffer.bloc_size)
          except:
            if self.Persistent and self.AcceptRanges:
              try:
                self.Connection.close()
                self.Connection.request('GET', self.MediaSrcURL, headers=header)
                rep = self.Connection.getresponse()
                bloc = rep.read(self.MediaBuffer.bloc_size)
                rep.close()
                rep = None
              except:
                pass
            pass
          if not bloc:
            self.Status = MediaProvider.STATUS_ABORTED
            self.logger.log('Segment %d -> échec de lecture du contenu' % (self.MediaBuffer.w_index + self.MediaBuffer.len), 1)
            try:
              self.Connection.close()
            except:
              pass
            if rep:
              try:
                rep.close()
              except:
                pass
            rep = None
            self.Connection = None
            break
          else:
            self.MediaBuffer.w_condition.acquire()
            if self.MediaBuffer.len < self.MediaBufferSize:
              self.MediaBuffer.content[self.MediaBuffer.len] = bloc
              self.MediaBuffer.len +=1
            else:
              self.MediaBuffer.w_index += 1
              del self.MediaBuffer.content[0]
              self.logger.log('Translation du tampon vers la position %d' % self.MediaBuffer.w_index, 2)
              self.MediaBuffer.content += [bloc]
            self.logger.log('Segment %d -> placement dans la zone %d du tampon' % (self.MediaBuffer.w_index + self.MediaBuffer.len - 1, self.MediaBuffer.len), 2)
            self.MediaBuffer.w_condition.notify_all()
            self.MediaBuffer.w_condition.release()
        elif self.Status != MediaProvider.STATUS_ABORTED and not self.shutdown_requested:
          self.MediaBuffer.r_event.wait()
          self.MediaBuffer.r_event.clear()
      elif self.Status != MediaProvider.STATUS_ABORTED and not self.shutdown_requested:
        self.MediaBuffer.r_event.wait()
        self.MediaBuffer.r_event.clear()
    try:
      self.Connection.close()
    except:
      pass
    if self.Status != MediaProvider.STATUS_ABORTED and not self.shutdown_requested:
      self.Status = MediaProvider.STATUS_COMPLETED
      self.logger.log('Fin du chargement dans le tampon du contenu', 1)
    else:
      self.logger.log('Interruption du chargement dans le tampon du contenu', 1)
    self.MediaBuffer.t_index = -1
    self.MediaBuffer.w_condition.acquire()
    self.MediaBuffer.w_condition.notify_all()
    self.MediaBuffer.w_condition.release()

  def run(self):
    self.Status = MediaProvider.STATUS_INITIALIZING
    build_success = False
    if not self.shutdown_requested:
      build_success = self.MediaBuilder()
    if build_success and not self.shutdown_requested:
      self.BuildFinishedEvent.set()
      self.Status = MediaProvider.STATUS_RUNNING
      if self.ServerMode == MediaProvider.SERVER_MODE_SEQUENTIAL:
        self.MediaFeederS()
      elif self.ServerMode == MediaProvider.SERVER_MODE_RANDOM:
        if self.MediaSrcType.lower() in ('ContentURL'.lower(), 'WebPageURL'.lower()):
          self.MediaFeederR()
      else:
        self.Status = MediaProvider.STATUS_ABORTED
        self.BuildFinishedEvent.set()
    else:
      self.Status = MediaProvider.STATUS_ABORTED
      self.BuildFinishedEvent.set()

  def shutdown(self):
    self.shutdown_requested = True
    if self.FFmpeg_process:
      if self.FFmpeg_process.poll() == None:
        try:
          os.system('taskkill /t /f /pid %s > nul' % (self.FFmpeg_process.pid))
        except:
          pass
    if self.FFmpeg_sub_process:
      if self.FFmpeg_sub_process.poll() == None:
        try:
          os.system('taskkill /t /f /pid %s > nul' % (self.FFmpeg_process.pid))
        except:
          pass
    if self.Status == MediaProvider.STATUS_INITIALIZING:
      self.Status = MediaProvider.STATUS_ABORTED
    if self.Status == MediaProvider.STATUS_RUNNING:
      self.Status = MediaProvider.STATUS_ABORTED
      self.MediaBuffer.r_event.set()


class MediaRequestHandlerS(server.SimpleHTTPRequestHandler):

  protocol_version = "HTTP/1.1"

  def __init__(self, *args, MediaBuffer, MediaSubBuffer, MediaExt, **kwargs):
    self.MediaBuffer = MediaBuffer
    if MediaSubBuffer:
      self.MediaSubBuffer = MediaSubBuffer
    else:
      self.MediaSubBuffer = None
    self.MediaExt = MediaExt
    super().__init__(*args, **kwargs)

  
  def send_head(self):
    if self.server.auth_ip:
      if not self.client_address[0] in self.server.auth_ip:
        self.close_connection = True
        try:
          self.send_error(HTTPStatus.FORBIDDEN, "Unauthorized client")
        except:
          pass
        return False
    alt_sub = '/mediasub'
    if self.MediaSubBuffer:
      if self.MediaSubBuffer[1]:
        alt_sub = '/media' + self.MediaSubBuffer[1]
    if self.path.lower() in ('/media', '/media' + self.MediaExt):
      self.MediaBufferSize = len(self.MediaBuffer.content)
      self.MediaBuffer.create_lock.acquire()
      self.MediaBufferId = len(self.MediaBuffer.r_indexes)
      self.MediaBuffer.r_indexes.append(0)
      self.MediaBuffer.create_lock.release()
      self.send_response(HTTPStatus.OK)
      self.send_header("Content-type", "application/octet-stream")
      self.send_header("Accept-Ranges", "none")
      self.send_header("Transfer-Encoding", "chunked")
      if self.MediaSubBuffer:
        if self.MediaSubBuffer[0]:
          self.send_header("CaptionInfo.sec", r"http://%s:%s/mediasub%s" % (*self.server.server_address[:2], self.MediaSubBuffer[1]))
      try:
        self.end_headers()
      except:
        self.close_connection = True
        return False
      return 'media'
    elif (self.path.lower().rsplit(".", 1)[0] == '/mediasub' or self.path.lower() == alt_sub) and self.MediaSubBuffer:
      if not self.MediaSubBuffer[0]:
        self.close_connection = True
        try:
          self.send_error(HTTPStatus.NOT_FOUND, "Content not found")
        except:
          pass
        return False
      self.send_response(HTTPStatus.OK)
      self.send_header("Content-type", "application/octet-stream")
      self.send_header("Transfer-Encoding", "chunked")
      try:
        self.end_headers()
      except:
        self.close_connection = True
        return False
      return 'mediasub'
    else:
      self.close_connection = True
      try:
        self.send_error(HTTPStatus.NOT_FOUND, "File not found")
      except:
        pass
      return False

  def do_GET(self):
    f = self.send_head()
    if f in ('media', 'mediasub'):
      try:
        self.copyfile(f, self.wfile)
      except:
        pass

  def do_HEAD(self):
    f = self.send_head()

  def copyfile(self, source, outputfile):
    if self.server.__dict__['_BaseServer__is_shut_down'].is_set() or not source in ('media', 'mediasub'):
      self.close_connection = True
      try:
        outputfile.write(b"0\r\n\r\n")
      except:
        pass
      return
    if source == 'mediasub':
      try:
        outputfile.write(str(hex(len(self.MediaSubBuffer[0]))).encode("ISO-8859-1")[2:] + b"\r\n" + self.MediaSubBuffer[0] + b"\r\n")
        self.server.logger.log('Distribution des sous-titres à %s:%s' % (self.client_address[0], self.client_address[1]), 2)
      except:
        self.server.logger.log('Échec de distribution des sous-titres à %s:%s' % (self.client_address[0], self.client_address[1]), 1)
    else:
      self.server.logger.log('Connexion %d -> début de la distribution du contenu à %s:%s' % (self.MediaBufferId + 1, self.client_address[0], self.client_address[1]), 1)
      self.MediaBuffer.r_indexes[self.MediaBufferId] = 1
      while not self.MediaBuffer.r_indexes[self.MediaBufferId] == - self.MediaBuffer.w_index:
        self.MediaBuffer.w_condition.acquire()
        while self.MediaBuffer.r_indexes[self.MediaBufferId] == self.MediaBuffer.w_index:
          if self.server.__dict__['_BaseServer__is_shut_down'].is_set():
            break
          self.MediaBuffer.w_condition.wait()
        self.MediaBuffer.w_condition.release()
        if self.server.__dict__['_BaseServer__is_shut_down'].is_set():
          break
        if self.MediaBuffer.r_indexes[self.MediaBufferId] != - self.MediaBuffer.w_index:
          bloc = self.MediaBuffer.content[(self.MediaBuffer.r_indexes[self.MediaBufferId] -1) % self.MediaBufferSize]
          if self.MediaBuffer.r_indexes[self.MediaBufferId] <= abs(self.MediaBuffer.w_index) - self.MediaBufferSize:
            self.server.logger.log('Connexion %d -> segment %d -> la zone %d a été dépassée par la queue du tampon' % (self.MediaBufferId + 1, self.MediaBuffer.r_indexes[self.MediaBufferId], (self.MediaBuffer.r_indexes[self.MediaBufferId] - 1) % self.MediaBufferSize), 2)
            self.server.logger.log('Connexion %d -> segment %d -> échec de distribution du contenu' % (self.MediaBufferId + 1, self.MediaBuffer.r_indexes[self.MediaBufferId]), 1)
            break
          else:
            try:
              outputfile.write(str(hex(len(bloc))).encode("ISO-8859-1")[2:] + b"\r\n" + bloc + b"\r\n")
              self.server.logger.log('Connexion %d -> segment %d -> distribution à partir de la zone %d du tampon' % (self.MediaBufferId + 1, self.MediaBuffer.r_indexes[self.MediaBufferId], (self.MediaBuffer.r_indexes[self.MediaBufferId] - 1) % self.MediaBufferSize), 2)
              self.MediaBuffer.r_indexes[self.MediaBufferId] += 1
              self.MediaBuffer.r_event.set()
            except:
               self.server.logger.log('Connexion %d -> segment %d -> échec de distribution du contenu' % (self.MediaBufferId + 1, self.MediaBuffer.r_indexes[self.MediaBufferId]), 1)
               break
      self.MediaBuffer.r_indexes[self.MediaBufferId] = - self.MediaBuffer.r_indexes[self.MediaBufferId]
      self.server.logger.log('Connexion %d -> fin de la distribution du contenu' % (self.MediaBufferId + 1), 1)
    try:
      outputfile.write(b"0\r\n\r\n")
    except:
      pass
    if self.server.__dict__['_BaseServer__is_shut_down'].is_set():
      self.close_connection = True

  def handle(self):
    self.close_connection = True
    with selectors.DefaultSelector() as selector:
      selector.register(self.request, selectors.EVENT_READ)
      closed = False
      while not closed:
        ready = selector.select(0.5)
        if self.server.__dict__['_BaseServer__shutdown_request'] or self.server.__dict__['_BaseServer__is_shut_down'].is_set():
          break
        if ready:
          try:
            self.handle_one_request()
          except:
            pass
          closed = self.close_connection


class MediaRequestHandlerR(server.SimpleHTTPRequestHandler):

  protocol_version = "HTTP/1.1"
  
  def __init__(self, *args, MediaBuffer, MediaSubBuffer, MediaSrc, MediaSrcType, MediaExt, MediaSize, AcceptRanges, **kwargs):
    self.MediaBuffer = MediaBuffer
    if MediaSubBuffer:
      self.MediaSubBuffer = MediaSubBuffer
    else:
      self.MediaSubBuffer = None
    self.MediaSrc = MediaSrc
    self.MediaSrcType = MediaSrcType
    self.MediaExt = MediaExt
    self.MediaSize = MediaSize
    self.AcceptRanges = AcceptRanges
    super().__init__(*args, **kwargs)

  def send_head(self):
    if self.server.auth_ip:
      if not self.client_address[0] in self.server.auth_ip:
        self.close_connection = True
        try:
          self.send_error(HTTPStatus.FORBIDDEN, "Unauthorized client")
        except:
          pass
        return None, None, None
    alt_sub = '/mediasub'
    if self.MediaSubBuffer:
      if self.MediaSubBuffer[1]:
        alt_sub = '/media' + self.MediaSubBuffer[1]
    if self.path.lower() in ('/media', '/media' + self.MediaExt):
      bad_range = False
      req_range = self.headers.get('Range',"") if self.AcceptRanges else ""
      if req_range:
        try:
          req_start = req_range.split("=")[-1].split("-")[0].strip()
          req_end = req_range.split("=")[-1].split("-")[1].split(",")[0].strip()
          if not req_start:
            req_start = self.MediaSize - int(req_end)
            if req_start < 0:
              raise
            req_end = self.MediaSize
          else:
            req_start = int(req_start)
            if req_end:
              req_end = int(req_end) + 1
            else:
              req_end = self.MediaSize
          assert req_end <= self.MediaSize
          assert req_start < req_end
        except:
          req_start = None
          req_end = None
          bad_range = True
      else:
        req_start = None
        req_end = None
      if bad_range:
        self.close_connection = True
        try:
          self.send_error(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE, "Bad range request")
        except:
          pass
        return None, None, None
      if req_start == None:
        self.send_response(HTTPStatus.OK)
      else:
        self.send_response(HTTPStatus.PARTIAL_CONTENT)
      self.send_header("Content-type", "application/octet-stream")
      self.send_header("Content-Length", str(self.MediaSize if req_start == None else req_end - req_start))
      if self.AcceptRanges:
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("contentFeatures.dlna.org", "DLNA.ORG_PN=;DLNA.ORG_OP=01;DLNA.ORG_FLAGS=21700000000000000000000000000000")
      else:
        self.send_header("Accept-Ranges", "none")
        self.send_header("contentFeatures.dlna.org", "DLNA.ORG_PN=;DLNA.ORG_OP=00;DLNA.ORG_FLAGS=01700000000000000000000000000000")
      if req_start != None:
        self.send_header("Content-Range", "bytes %d-%d/%d" % (req_start, req_end - 1, self.MediaSize))
      if self.MediaSubBuffer:
        if self.MediaSubBuffer[0]:
          self.send_header("CaptionInfo.sec", r"http://%s:%s/mediasub%s" % (*self.server.server_address[:2], self.MediaSubBuffer[1]))
      return 'media', req_start or 0, req_end or self.MediaSize
    elif (self.path.lower().rsplit(".", 1)[0] == '/mediasub' or self.path.lower() == alt_sub) and self.MediaSubBuffer:
      sub_size = len(self.MediaSubBuffer[0])
      if sub_size == 0:
        self.close_connection = True
        try:
          self.send_error(HTTPStatus.NOT_FOUND, "Content not found")
        except:
          pass
        return None, None, None
      self.send_response(HTTPStatus.OK)
      self.send_header("Content-type", "application/octet-stream")
      self.send_header("Content-Length", str(sub_size))
      return 'mediasub', None, None
    else:
      self.close_connection = True
      try:
        self.send_error(HTTPStatus.NOT_FOUND, "Content not found")
      except:
        pass
      return None, None, None

  def do_GET(self):
    source, req_start, req_end = self.send_head()
    if source in ('media', 'mediasub'):
      try:
        self.copyfile(source, req_start, req_end, self.wfile)
      except:
        pass

  def do_HEAD(self):
    source, req_start, req_end = self.send_head()
    try:
      self.end_headers()
    except:
      self.close_connection = True

  def copyfile(self, source, req_start, req_end, outputfile):
    if self.server.__dict__['_BaseServer__is_shut_down'].is_set() or not source in ('media', 'mediasub'):
      self.close_connection = True
      return
    f = None
    if source == 'media':
      if self.MediaSrcType == 'ContentPath':
        self.MediaBuffer.create_lock.acquire()
        self.MediaBufferId = len(self.MediaBuffer.r_indexes)
        self.MediaBuffer.r_indexes.append(0)
        self.MediaBuffer.create_lock.release()
        self.server.logger.log('Connexion %d -> début de la distribution du contenu à %s:%s' % (self.MediaBufferId + 1, self.client_address[0], self.client_address[1]), 1)
        try:
          f = open(self.MediaSrc, 'rb')
          if req_start:
            f.seek(req_start)
          self.end_headers()
        except:
          self.close_connection = True
          self.server.logger.log('Connexion %d -> échec de distribution du contenu' % (self.MediaBufferId + 1), 1)
          try:
            f.close()
          except:
            pass
          return
        try:
          index = req_start
          while not self.server.__dict__['_BaseServer__is_shut_down'].is_set():
            if index < req_end:
              bloc = None
              bloc = f.read(min(self.MediaBuffer.bloc_size, req_end - index))
              if not bloc:
                raise
              outputfile.write(bloc)
              self.server.logger.log('Connexion %d -> segment %d- -> distribution' % (self.MediaBufferId + 1, index), 2)
              index = index + min(self.MediaBuffer.bloc_size, req_end - index)
            else:
              break
        except:
          index = -1
          self.close_connection = True
        try:
          f.close()
        except:
          pass
        if index < 0:
          self.server.logger.log('Connexion %d -> échec de distribution du contenu' % (self.MediaBufferId + 1), 1)
        else:
          self.server.logger.log('Connexion %d -> fin de la distribution du contenu' % (self.MediaBufferId + 1), 1)
      elif self.MediaSrcType in ('ContentURL', 'WebPageURL'):
        self.MediaBuffer.create_lock.acquire()
        self.MediaBufferId = len(self.MediaBuffer.r_indexes)
        r_index = req_start // self.MediaBuffer.bloc_size + 1
        self.MediaBuffer.r_indexes.append(r_index)
        self.MediaBuffer.create_lock.release()
        self.MediaBuffer.r_event.set()
        bloc = None
        first_loop = True
        self.server.logger.log('Connexion %d -> début de la distribution du contenu à %s:%s' % (self.MediaBufferId + 1, self.client_address[0], self.client_address[1]), 1)
        while not self.server.__dict__['_BaseServer__is_shut_down'].is_set():
          self.MediaBuffer.w_condition.acquire()
          while r_index < self.MediaBuffer.w_index or r_index >= self.MediaBuffer.w_index + self.MediaBuffer.len - (1 if first_loop and r_index * self.MediaBuffer.bloc_size < req_end else 0):
            if self.MediaBufferId < (self.MediaBuffer.t_index if self.MediaBuffer.t_index !=None else 0) and r_index != self.MediaBuffer.w_index + self.MediaBuffer.len:
              self.server.logger.log('Connexion %d -> segment %d -> expulsion du tampon' % (self.MediaBufferId + 1, r_index), 2)  
              r_index = 0
              break
            if self.MediaBuffer.t_index == -1:
              r_index = 0
              break
            if self.server.__dict__['_BaseServer__is_shut_down'].is_set():
              break
            self.MediaBuffer.w_condition.wait()
          if r_index == 0 or self.server.__dict__['_BaseServer__is_shut_down'].is_set():
            self.MediaBuffer.w_condition.release()
            break
          if r_index >= self.MediaBuffer.w_index and r_index < self.MediaBuffer.w_index + self.MediaBuffer.len:
            bloc = self.MediaBuffer.content[(r_index - self.MediaBuffer.w_index)][(0 if not first_loop else req_start % self.MediaBuffer.bloc_size):]
          self.MediaBuffer.w_condition.release()
          if not bloc:
            r_index = 0
            break
          try:
            if first_loop:
              self.end_headers()
              first_loop = False
            if r_index * self.MediaBuffer.bloc_size >= req_end:
              outputfile.write(bloc[:(req_end - 1) % self.MediaBuffer.bloc_size + 1])
            else:
              self.MediaBuffer.r_indexes[self.MediaBufferId] += 1
              self.MediaBuffer.r_event.set()
              outputfile.write(bloc)
            self.server.logger.log('Connexion %d -> segment %d -> distribution à partir du tampon' % (self.MediaBufferId + 1, r_index), 2)
            r_index += 1
          except:
            r_index = 0
            break
          if (r_index - 1) * self.MediaBuffer.bloc_size >= req_end:
            break
        if r_index == 0:
          self.server.logger.log('Connexion %d -> segment %d -> échec de distribution du contenu' % (self.MediaBufferId + 1, self.MediaBuffer.r_indexes[self.MediaBufferId]), 1)
          self.close_connection = True
          if first_loop and not self.server.__dict__['_BaseServer__is_shut_down']:
            try:
              self.send_error(HTTPStatus.NOT_FOUND, "Content not found")
            except:
              pass
        else:
          r_index = 0
          self.server.logger.log('Connexion %d -> fin de la distribution du contenu' % (self.MediaBufferId + 1), 1)
        self.MediaBuffer.r_indexes[self.MediaBufferId] = 0
        self.MediaBuffer.r_event.set()
    elif source == 'mediasub':
      try:
        self.end_headers()
      except:
        self.close_connection = True
        self.server.logger.log('Échec de distribution des sous-titres à %s:%s' % (self.client_address[0], self.client_address[1]), 1)
        return
      self.server.logger.log('Distribution des sous-titres à %s:%s' % (self.client_address[0], self.client_address[1]), 2)
      try:
        outputfile.write(self.MediaSubBuffer[0])
      except:
        self.close_connection = True
        self.server.logger.log('Échec de distribution des sous-titres à %s:%s' % (self.client_address[0], self.client_address[1]), 1)
    else:
      self.close_connection = True
      try:
        self.send_error(HTTPStatus.NOT_FOUND, "Content not found")
      except:
        pass
    if self.server.__dict__['_BaseServer__is_shut_down'].is_set():
      self.close_connection = True

  def handle(self):
    self.close_connection = True
    with selectors.DefaultSelector() as selector:
      selector.register(self.request, selectors.EVENT_READ)
      closed = False
      while not closed:
        ready = selector.select(0.5)
        if self.server.__dict__['_BaseServer__shutdown_request'] or self.server.__dict__['_BaseServer__is_shut_down'].is_set():
          break
        if ready:
          try:
            self.handle_one_request()
          except:
            pass
          closed = self.close_connection


class MediaServer(threading.Thread):

  MediaBufferBlocSize = 1024 * 1024

  def __init__(self, MediaServerMode, MediaServerAddress, MediaSrc, MediaSrcType=None, MediaStartFrom=0, MediaBufferSize=75, MediaBufferAhead=25, MediaMuxContainer=None, MediaSubSrc=None, MediaSubSrcType=None, MediaSubLang=None, MediaSubBuffer=None, MediaProcessProfile=None, verbosity=0, auth_ip=None):
    threading.Thread.__init__(self)
    self.verbosity = verbosity
    self.auth_ip = auth_ip
    self.logger = log_event(verbosity)
    self.MediaServerMode = MediaServerMode
    self.MediaServerAddress = MediaServerAddress
    self.MediaSrc = MediaSrc
    self.MediaSrcType = MediaSrcType
    self.MediaStartFrom = MediaStartFrom
    self.MediaBufferAhead = MediaBufferAhead
    self.MediaBufferSize = max(MediaBufferSize, self.MediaBufferAhead + 2)
    self.MediaMuxContainer = MediaMuxContainer
    self.MediaBufferInstance = MediaBuffer(self.MediaBufferSize, MediaServer.MediaBufferBlocSize)
    self.MediaSubSrc = MediaSubSrc
    self.MediaSubSrcType = MediaSubSrcType
    self.MediaSubLang = MediaSubLang
    if MediaSubBuffer:
      if len(MediaSubBuffer) == 2:
        self.MediaSubBufferInstance = MediaSubBuffer
      else:
        self.MediaSubBufferInstance = [b'', '']
    else:
      self.MediaSubBufferInstance = [b'', '']
    self.MediaProcessProfile = MediaProcessProfile
    self.is_running = None
    self.BuildFinishedEvent = threading.Event()
    self.ShutdownEvent = self.BuildFinishedEvent

  def run(self):
    if not self.is_running and not self.ShutdownEvent.is_set():
      self.is_running = True
      if not self.ShutdownEvent.is_set():
        self.MediaProviderInstance = MediaProvider(self.MediaServerMode, self.MediaSrc, self.MediaSrcType, self.MediaStartFrom, self.MediaBufferInstance, self.MediaBufferAhead, self.MediaMuxContainer, self.MediaSubSrc, self.MediaSubSrcType, self.MediaSubLang, self.MediaSubBufferInstance, self.MediaProcessProfile, self.MediaServerAddress[1]+1, self.BuildFinishedEvent, self.verbosity)
        self.MediaProviderInstance.start()
        self.MediaProviderInstance.BuildFinishedEvent.wait()
        if self.is_running and self.MediaProviderInstance.Status in (MediaProvider.STATUS_RUNNING, MediaProvider.STATUS_COMPLETED):
          if self.MediaProviderInstance.ServerMode == MediaProvider.SERVER_MODE_SEQUENTIAL:
            self.MediaRequestBoundHandler = partial(MediaRequestHandlerS, MediaBuffer=self.MediaBufferInstance, MediaSubBuffer=self.MediaSubBufferInstance, MediaExt=self.MediaProviderInstance.MediaFeedExt)
          elif self.MediaProviderInstance.ServerMode == MediaProvider.SERVER_MODE_RANDOM:
            self.MediaRequestBoundHandler = partial(MediaRequestHandlerR, MediaBuffer=self.MediaBufferInstance, MediaSubBuffer=self.MediaSubBufferInstance, MediaSrc=self.MediaProviderInstance.MediaSrc, MediaSrcType=self.MediaProviderInstance.MediaSrcType, MediaExt=self.MediaProviderInstance.MediaFeedExt, MediaSize=self.MediaProviderInstance.MediaSize, AcceptRanges=self.MediaProviderInstance.AcceptRanges)
          else:
            self.is_running = None
            try:
              self.MediaProviderInstance.shutdown()
            except:
              pass
            return
          with ThreadedDualStackServer(self.MediaServerAddress, self.MediaRequestBoundHandler, verbosity=self.verbosity, auth_ip=self.auth_ip) as self.MediaServerInstance:
            if self.is_running:
              self.logger.log('Démarrage du serveur de diffusion en mode %s%s' % ({MediaProvider.SERVER_MODE_SEQUENTIAL: 'séquentiel', MediaProvider.SERVER_MODE_RANDOM: 'aléatoire'}.get(self.MediaProviderInstance.ServerMode,''), '' if self.MediaProviderInstance.ServerMode==MediaProvider.SERVER_MODE_SEQUENTIAL else ('' if self.MediaProviderInstance.AcceptRanges else ' non supporté par la source')), 0)
              self.MediaServerInstance.serve_forever()
      self.is_running = None

  def shutdown(self):
    was_running = self.is_running
    self.is_running = False
    self.ShutdownEvent.set()
    if was_running:
      try:
        self.MediaProviderInstance.shutdown()
      except:
        pass
      try:
        self.MediaServerInstance.shutdown()
        self.logger.log('Fermeture du serveur de diffusion', 0)
        for sock in self.MediaServerInstance.conn_sockets:
          try:
            sock.shutdown(socket.SHUT_RDWR)
          except:
            pass
      except:
        pass
      self.MediaBufferInstance.r_event.set()
      self.MediaBufferInstance.w_condition.acquire()
      self.MediaBufferInstance.w_condition.notify_all()
      self.MediaBufferInstance.w_condition.release()

      
class DLNAArgument:

  def __init__(self):
    self.Name = None
    self.Direction = None
    self.Event = None
    self.Type = None
    self.AllowedValueList = None
    self.AllowedValueRange = None
    self.DefaultValue = None


class DLNAAction:

  def __init__(self):
    self.Name = None
    self.Arguments = []


class DLNAService:

  def __init__(self):
    self.Type = None
    self.Id = None
    self.ControlURL = None
    self.SubscrEventURL = None
    self.DescURL = None
    self.Actions = []
    self.EventThroughLastChange = None


class DLNARenderer:

  def __init__(self):
    self.DescURL = None
    self.BaseURL = None
    self.Manufacturer = None
    self.ModelName = None
    self.FriendlyName = None
    self.ModelDesc = None
    self.ModelNumber = None
    self.SerialNumber = None
    self.UDN = None
    self.IconURL = None
    self.Services = []
    self.StatusAlive = None
    self.StatusTime = None
    self.StatusAliveLastTime = None


def _XMLGetNodeText(node):
  text = []
  for childNode in node.childNodes:
    if childNode.nodeType == node.TEXT_NODE:
      text.append(childNode.data)
  return(''.join(text))

class HTTPMessage():

  def __init__(self, request, timeout=5, max_length=1048576):
    iter = 0
    while iter < 2:
      self.method = None
      self.path = None
      self.version = None
      self.code = None
      self.message = None
      self.headers = {}
      self.body = None
      if iter == 0:
        if self._read_request(request, timeout, max_length):
          iter = 2
        else:
          iter = 1
      else:
        iter = 2
    
  def _read_headers(self, msg):
    if not msg:
      return
    a = None
    for msg_line in msg.splitlines()[:-1]:
      if not msg_line:
        return
      if not a:
        try:
          msg_line.strip().split(None, 2)
          a, b, c = msg_line.strip().split(None, 2)
        except:
          return
      else:
        try:
          header_name, header_value = msg_line.split(':', 1)
        except:
          return
        header_name = header_name.strip().upper()
        if header_name:
          header_value = header_value.strip()
          self.headers[header_name] = header_value
        else:
          return
    if a[:4].upper() == 'HTTP':
      self.version = a.upper()
      self.code = b
      self.message = c
    else:
      self.method = a.upper()
      self.path = b
      self.version = c.upper()
    if not 'Content-Length'.upper() in self.headers:
      self.headers['Content-Length'.upper()] = 0
    return True

  def header(self, name, default = None):
    return self.headers.get(name.upper(), default)

  def _read_request(self, request, timeout=5, max_length=1048576):
    if not isinstance(request, socket.socket):
      resp = request[0]
      body_pos = resp.find(b'\r\n\r\n')
      if body_pos >= 0:
        body_pos += 4
      else:
        body_pos = resp.find(b'\n\n')
        if body_pos >= 0:
          body_pos += 2
    else:
      request.settimeout(timeout)
      resp = b''
      while len(resp) < max_length:
        bloc = None
        try:
          bloc = request.recv(max_length - len(resp))
        except:
          return None
        if not bloc:
          return None
        resp = resp + bloc
        body_pos = resp.find(b'\r\n\r\n')
        if body_pos >= 0:
          body_pos += 4
          break
        else:
          body_pos = resp.find(b'\n\n')
          if body_pos >= 0:
            body_pos += 2
            break
    if body_pos < 0:
      return None
    if not self._read_headers(resp[:body_pos].decode('ISO-8859-1')):
      return None
    try:
      body_len = int(self.header('Content-Length'))
    except:
      return None
    if body_pos + body_len > max_length:
      return None
    if isinstance(request, socket.socket):
      while len(resp) < body_pos + body_len:
        bloc = None
        try:
          bloc = request.recv(body_pos + body_len - len(resp))
        except:
          return None
        if not bloc:
          return None
        resp = resp + bloc
    self.body = resp[body_pos:].decode('UTF-8')
    return True


class DLNAEvent:

  def __init__(self):
    self.ReceiptTime = None
    self.Changes = []


class DLNAEventWarning:

  def __init__(self, event_listener, prop_name, *warn_values, WarningEvent=None):
    self.EventListener = event_listener
    self.WatchedProperty = prop_name
    if isinstance(WarningEvent, threading.Event):
      self.WarningEvent = WarningEvent
    else:
      self.WarningEvent = threading.Event()
    if warn_values:
      self.WatchedValues = warn_values
    else:
      self.WatchedValues = None
    self.TriggerLastValue = None
    self.ReferenceSEQ = None


class DLNAEventListener:

  def __init__(self, log):
    self.port = None
    self.SID = None
    self.Renderer = None
    self.Service = None
    self.is_running = None
    self.log = log
    self.EventsLog = []
    self.CurrentSEQ = None
    self.Warnings = []


class DLNAEventNotificationHandler(socketserver.StreamRequestHandler):

  def __init__(self, *args, EventListener, **kwargs):
    self.EventListener = EventListener
    try:
      super().__init__(*args, **kwargs)
    except:
      pass
  
  def handle(self):
    try:
      resp = HTTPMessage(self.request)
      if resp.method != 'NOTIFY' or resp.header('SID', '') != self.EventListener.SID:
        self.request.sendall("HTTP/1.0 400 Bad Request\r\n\r\n".encode("ISO-8859-1"))
        return
      dlna_event = DLNAEvent()
      time_receipt = time.localtime()
      seq = resp.header('SEQ', '')
      self.server.logger.log('DLNA Renderer %s -> service %s -> réception de la notification d\'événement %s' % (self.EventListener.Renderer.FriendlyName, self.EventListener.Service.Id[23:], seq), 1)
      seq = int(seq)
      if not self.EventListener.CurrentSEQ:
        self.EventListener.CurrentSEQ = 0
      if seq > self.EventListener.CurrentSEQ:
        self.EventListener.CurrentSEQ = seq
      if self.EventListener.log:
        dlna_event.ReceiptTime = time_receipt
        if len(self.EventListener.EventsLog) < seq:
          self.EventListener.EventsLog = self.EventListener.EventsLog + [None]*(seq - len(self.EventListener.EventsLog))
      root_xml = minidom.parseString(resp.body)
      try:
        self.request.sendall("HTTP/1.0 200 OK\r\n\r\n".encode("ISO-8859-1"))
      except:
        pass
    except:
      self.request.sendall("HTTP/1.0 400 Bad Request\r\n\r\n".encode("ISO-8859-1"))
      return
    try:
      for node in root_xml.documentElement.childNodes:
        if node.tagName.split(':', 1)[-1].lower() != 'property':
          continue
        for child_node in node.childNodes:
          try:
            prop_name = child_node.tagName
          except:
            continue
          try:
            prop_nvalue = _XMLGetNodeText(child_node)
          except:
            continue
          self.server.logger.log('DLNA Renderer %s -> Service %s -> notification d\'événement %s -> %s est passé à %s' % (self.EventListener.Renderer.FriendlyName, self.EventListener.Service.Id[23:], seq, prop_name, prop_nvalue), 2)
          if prop_name.upper() == 'LastChange'.upper():
            lc_xml = minidom.parseString(prop_nvalue)
            for p_node in lc_xml.documentElement.childNodes[0].childNodes:
              lc_prop_name = p_node.tagName
              for att in p_node.attributes.items():
                if att[0].lower() == 'val':
                  lc_prop_value = att[1]
                  break
              dlna_event.Changes.append((lc_prop_name, lc_prop_value))
          else:
            dlna_event.Changes.append((prop_name, prop_nvalue))
      if self.EventListener.log:
        self.EventListener.EventsLog.append(dlna_event)
      for (prop_name, prop_nvalue) in dlna_event.Changes:
        for warning in self.EventListener.Warnings:
          try:
            if prop_name == warning.WatchedProperty:
              if not warning.ReferenceSEQ:
                warn_update = True
              else:
                if warning.ReferenceSEQ < seq:
                  warn_update = True
                else:
                  warn_update = False
              if warn_update:
                if not warning.WatchedValues:
                  self.server.logger.log('DLNA Renderer %s -> Service %s -> notification d\'événement %s -> alerte: %s est passé à %s' % (self.EventListener.Renderer.FriendlyName, self.EventListener.Service.Id[23:], seq, prop_name, prop_nvalue), 2)
                  warning.TriggerLastValue = prop_nvalue
                  warning.ReferenceSEQ = seq
                  warning.WarningEvent.set()
                elif prop_nvalue in warning.WatchedValues:
                  self.server.logger.log('DLNA Renderer %s -> Service %s -> notification d\'événement %s -> alerte: %s est passé à %s' % (self.EventListener.Renderer.FriendlyName, self.EventListener.Service.Id[23:], seq, prop_name, prop_nvalue), 2)
                  warning.TriggerLastValue = prop_nvalue
                  warning.ReferenceSEQ = seq
                  warning.WarningEvent.set()
          except:
            continue
    except:
      return


class DLNAAdvertisementServer(socketserver.ThreadingMixIn, socketserver.UDPServer):

  allow_reuse_address = True
  
  def __init__(self, *args, verbosity, **kwargs):
    self.logger = log_event(verbosity)
    socketserver.UDPServer.__init__(self, *args, **kwargs)

  def server_bind(self):
    super().server_bind()
    self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, struct.pack('4sL', socket.inet_aton('239.255.255.250'), socket.INADDR_ANY))


class DLNAAdvertisementHandler(socketserver.DatagramRequestHandler):

  def __init__(self, *args, Controler, **kwargs):
    self.Controler = Controler
    try:
      super().__init__(*args, **kwargs)
    except:
      pass
  
  def handle(self):
    try:
      resp = HTTPMessage(self.request)
      if resp.method != 'NOTIFY':
        return
      nt = resp.header('NT', '')
      if not 'MediaRenderer'.lower() in nt.lower():
        return
      time_resp = time.localtime()
      nts = resp.header('NTS', '')
      udn = resp.header('USN','')[:41]
      desc_url = resp.header('Location','')
      self.server.logger.log('Réception d\'une publicité du renderer %s:%s: %s' % (self.client_address[0], self.client_address[1], nts), 2)
      if 'alive' in nts.lower():
        rend_found = False
        for rend in self.Controler.Renderers:
          if rend.UDN == udn:
            rend_found = True
            if not rend.StatusAlive:
              self.server.advert_status_change.set()
              rend.StatusAlive = True
            rend.StatusTime = time_resp
            rend.StatusAliveLastTime = time_resp
        if not rend_found:
          if (urllib.parse.urlparse(desc_url)).netloc.split(':',1)[0] == self.client_address[0]:
            if self.Controler._update_renderers(desc_url, time_resp):
              self.server.advert_status_change.set()
          else:
            self.server.logger.log('Publicité du renderer %s:%s ignorée en raison de la discordance d\'adresse de l\'URL de description' % (self.client_address[0], self.client_address[1]), 2)
      else:
        for rend in self.Controler.Renderers:
          if rend.UDN == udn:
            if rend.StatusAlive:
              self.server.advert_status_change.set()
              rend.StatusAlive = False
            rend.StatusTime = time_resp
    except:
      return


class DLNARendererControler:

  def __init__(self, verbosity=0):
    self.Renderers = []
    self.verbosity = verbosity
    self.logger = log_event(verbosity)
    self.is_advert_receiver_running = None
    self.advert_status_change = None
    self.is_discovery_polling_running = None
    self.discovery_status_change = None
    self.discovery_polling_shutdown = None
    self.ip = socket.gethostbyname(socket.getfqdn())
    self.update_renderers = threading.Lock()

  def _update_renderers(self, desc_url, time_resp):
    renderer = DLNARenderer()
    renderer.DescURL = desc_url
    try:
      desc_httpresp = urllib.request.urlopen(renderer.DescURL, timeout=5)
      desc = desc_httpresp.read()
      desc_httpresp.close()
    except:
      return None
    try:
      root_xml = minidom.parseString(desc)
    except:
      return False
    try:
      if not 'MediaRenderer'.lower() in _XMLGetNodeText(root_xml.getElementsByTagName('deviceType')[0]).lower():
        return False
    except:
      return False
    baseurl_elem = root_xml.getElementsByTagName('URLBase')
    if baseurl_elem:
      renderer.BaseURL = _XMLGetNodeText(baseurl_elem[0]).rstrip('/')
    else:
      url = urllib.parse.urlparse(renderer.DescURL)
      renderer.BaseURL = '%s://%s' % (url.scheme, url.netloc)
    try:
      renderer.Manufacturer = _XMLGetNodeText(root_xml.getElementsByTagName('manufacturer')[0])
    except:
      pass
    try:
      renderer.ModelName = _XMLGetNodeText(root_xml.getElementsByTagName('modelName')[0])
    except:
      pass
    try:
      renderer.FriendlyName = _XMLGetNodeText(root_xml.getElementsByTagName('friendlyName')[0])
    except:
      pass
    try:
      renderer.ModelDesc = _XMLGetNodeText(root_xml.getElementsByTagName('modelDescription')[0])
    except:
      pass
    try:
      renderer.ModelNumber = _XMLGetNodeText(root_xml.getElementsByTagName('modelNumber')[0])
    except:
      pass
    try:
      renderer.SerialNumber = _XMLGetNodeText(root_xml.getElementsByTagName('serialNumber')[0])
    except:
      pass
    try:
      renderer.UDN = _XMLGetNodeText(root_xml.getElementsByTagName('UDN')[0])
    except:
      pass
    try:
      renderer.IconURL = renderer.BaseURL + _XMLGetNodeText(root_xml.getElementsByTagName('icon')[-1].getElementsByTagName('url')[0])
    except:
      pass
    self.update_renderers.acquire()
    for rend in self.Renderers:
      if rend.BaseURL == renderer.BaseURL and rend.UDN == renderer.UDN:
        rend.StatusAlive = True
        if rend.StatusTime < time_resp:
          rend.StatusTime = time_resp
          rend.StatusAliveLastTime = time_resp
        renderer.StatusAlive = True
        break
    if renderer.StatusAlive:
      self.update_renderers.release()
      return False
    renderer.StatusAlive = True
    renderer.StatusTime = time_resp
    renderer.StatusAliveLastTime = time_resp
    self.logger.log('Enregistrement du renderer %s' % (renderer.FriendlyName), 1)
    self.Renderers.append(renderer)
    self.update_renderers.release()
    for node in root_xml.getElementsByTagName('service'):
      service = DLNAService()
      try:
        service.Type = _XMLGetNodeText(node.getElementsByTagName('serviceType')[0])
        service.Id = _XMLGetNodeText(node.getElementsByTagName('serviceId')[0])
        service.ControlURL = '%s%s' % (renderer.BaseURL, _XMLGetNodeText(node.getElementsByTagName('controlURL')[0]))
        service.SubscrEventURL = '%s%s' % (renderer.BaseURL, _XMLGetNodeText(node.getElementsByTagName('eventSubURL')[0]))
        service.DescURL = '%s%s' % (renderer.BaseURL, _XMLGetNodeText(node.getElementsByTagName('SCPDURL')[0]))
      except:
        continue
      try:
        desc_httpresp = urllib.request.urlopen(service.DescURL, timeout=5)
        desc = desc_httpresp.read()
        desc_httpresp.close()
      except:
        continue
      root_s_xml = minidom.parseString(desc)
      for node_s in root_s_xml.getElementsByTagName('action'):
        action = DLNAAction()
        try:
          action.Name = _XMLGetNodeText(node_s.getElementsByTagName('name')[0])
        except:
          continue
        for node_a in node_s.getElementsByTagName('argument'):
          argument = DLNAArgument()
          try:
            argument.Name = _XMLGetNodeText(node_a.getElementsByTagName('name')[0])
            argument.Direction = _XMLGetNodeText(node_a.getElementsByTagName('direction')[0])
            statevar = _XMLGetNodeText(node_a.getElementsByTagName('relatedStateVariable')[0])
            node_sv = next(sv for sv in root_s_xml.getElementsByTagName('stateVariable') if sv.getElementsByTagName('name')[0].childNodes[0].data == statevar)
            if node_sv.getAttribute('sendEvents') == 'yes':
              argument.Event = True
            elif node_sv.getAttribute('sendEvents') == 'no':
              argument.Event = False
            argument.Type = _XMLGetNodeText(node_sv.getElementsByTagName('dataType')[0])
            try:
              node_sv_av = node_sv.getElementsByTagName('allowedValueList')[0]
              argument.AllowedValueList = *(_XMLGetNodeText(av) for av in node_sv_av.getElementsByTagName('allowedValue')),
            except:
              pass
            try:
              node_sv_ar = node_sv.getElementsByTagName('allowedValueRange')[0]
              argument.AllowedValueRange = (_XMLGetNodeText(node_sv_ar.getElementsByTagName('minimum')[0]), _XMLGetNodeText(node_sv_ar.getElementsByTagName('maximum')[0]))
            except:
              pass
            try:
              argument.DefaultValue = _XMLGetNodeText(node_sv.getElementsByTagName('defaultValue')[0])
            except:
              pass
          except:
            argument = None
            continue
          if argument:
            action.Arguments.append(argument)
          else:
            action = None
            break
        if action:
          service.Actions.append(action)
      service.EventThroughLastChange = False
      try:
        node_sv = next(sv for sv in root_s_xml.getElementsByTagName('stateVariable') if sv.getElementsByTagName('name')[0].childNodes[0].data.upper() == 'LastChange'.upper())
        if node_sv.getAttribute('sendEvents') == 'yes':
          service.EventThroughLastChange = True
      except:
        pass
      renderer.Services.append(service)
    return True

  def discover(self, uuid=None, timeout=2, alive_persistence=0, from_polling=False):
    if uuid:
      self.logger.log('Envoi d\'un message de recherche de uuid:%s' % (uuid), 2)
      msg = \
      'M-SEARCH * HTTP/1.1\r\n' \
      'HOST: 239.255.255.250:1900\r\n' \
      'ST:uuid: ' + uuid + '\r\n' \
      'MX: 2\r\n' \
      'MAN: "ssdp:discover"\r\n' \
      '\r\n'
    else:
      self.logger.log('Envoi d\'un message de recherche de renderer DLNA', 2)
      msg = \
      'M-SEARCH * HTTP/1.1\r\n' \
      'HOST: 239.255.255.250:1900\r\n' \
      'ST: urn:schemas-upnp-org:device:MediaRenderer:1\r\n' \
      'MX: 2\r\n' \
      'MAN: "ssdp:discover"\r\n' \
      '\r\n'
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.settimeout(timeout)
    sock.sendto(msg.encode("ISO-8859-1"), ('239.255.255.250', 1900))
    loca_time=[]
    stopped = False
    time_req = time.localtime()
    try:
      with selectors.DefaultSelector() as selector:
        selector.register(sock, selectors.EVENT_READ)
        start_time = time.monotonic()
        while time.monotonic() - start_time <= timeout and (not from_polling or self.is_discovery_polling_running != False):
          ready = selector.select(0.5)
          if ready:
            resp, addr = sock.recvfrom(65507)
            self.logger.log('Réception d\'une réponse au message de recherche de %s:%s' % (addr[0], addr[1]), 2)
            time_resp = time.localtime()
            try:
              loca = resp[resp.upper().find(b'LOCATION:')+10:].split(b'\r',1)[0].decode("ISO-8859-1")
              if (urllib.parse.urlparse(loca)).netloc.split(':',1)[0] == addr[0]:
                loca_time.append((loca,time_resp))
              else:
                self.logger.log('Réponse de %s:%s ignorée en raison de la discordance d\'adresse de l\'URL de description' % (addr[0], addr[1]), 2)
            except:
              pass
    except:
      pass
    sock.close()
    for desc_url, time_resp in loca_time:
      self._update_renderers(desc_url, time_resp)
    for rend in self.Renderers:
      if rend.StatusAlive:
        if not uuid:
          if time.mktime(time_req) - time.mktime(rend.StatusAliveLastTime) > alive_persistence:
            rend.StatusAlive = False
            rend.StatusTime = time_resp
        elif rend.UDN == 'uuid:' + uuid:
          if time.mktime(time_req) - time.mktime(rend.StatusAliveLastTime) > alive_persistence:
            rend.StatusAlive = False
            rend.StatusTime = time_resp
      
  def search(self, uuid=None, name=None):
    for rend in self.Renderers:
      if uuid:
        if name:
          if rend.UDN == 'uuid:' + uuid and rend.FriendlyName.lower() == name.lower():
            return rend
        else:
          if rend.UDN == 'uuid:' + uuid:
            return rend
      else:
        if name:
          if rend.FriendlyName.lower() == name.lower():
            return rend
        else:
          if rend.StatusAlive:
            return rend
    return None

  def _discovery_polling(self, timeout=2, alive_persistence=0, polling_period=30):
    self.is_discovery_polling_running = True
    if self.discovery_status_change == None:
        self.discovery_status_change = threading.Event()
    while self.is_discovery_polling_running and not self.discovery_polling_shutdown.is_set():
      rend_stat = list([renderer.StatusAlive for renderer in self.Renderers])
      self.discover(uuid=None, timeout=timeout, alive_persistence=alive_persistence, from_polling=True)
      discovery_event = False
      for ind in range(len(self.Renderers)):
        if ind < len(rend_stat):
          if rend_stat[ind] != self.Renderers[ind].StatusAlive:
            discovery_event = True
            rend_stat[ind] = self.Renderers[ind].StatusAlive
        else:
          discovery_event = True
          rend_stat.append(self.Renderers[ind].StatusAlive)
      if discovery_event:
        self.discovery_status_change.set()
      self.discovery_polling_shutdown.wait(polling_period)
    self.discovery_polling_shutdown.clear()
    self.discovery_polling_shutdown = None
    self.is_discovery_polling_running = None

  def start_discovery_polling(self, timeout=2, alive_persistence=0, polling_period=30, DiscoveryEvent=None):
    if self.is_discovery_polling_running:
      self.logger.log('Recherche de renderer DLNA déjà activée', 1)
    else:
      self.logger.log('Démarrage de la recherche de renderer DLNA', 1)
      if isinstance(DiscoveryEvent, threading.Event):
        self.discovery_status_change = DiscoveryEvent
      else:
        self.discovery_status_change = threading.Event()
      self.discovery_polling_shutdown = threading.Event()
      discovery_thread = threading.Thread(target=self._discovery_polling, args=(timeout, alive_persistence, polling_period))
      discovery_thread.start()
      return self.discovery_status_change

  def stop_discovery_polling(self):
    try:
      self.discovery_polling_shutdown.set()
    except:
      pass
    if self.is_discovery_polling_running:
      self.logger.log('Fin de la recherche de renderer DLNA', 1)
      self.is_discovery_polling_running = False
      self.discovery_status_change.set()

  def wait_for_discovery(self, timeout=None):
    disc_event = None
    try:
      disc_event = self.discovery_status_change.wait(timeout)
    except:
      pass
    if disc_event:
      self.discovery_status_change.clear()
    if self.is_discovery_polling_running:
      return disc_event
    else:
      return None

  def _build_soap_msg(self, renderer, service, action, **arguments):
    if not renderer:
      return None
    serv = next((serv for serv in renderer.Services if serv.Id == ('urn:upnp-org:serviceId:' + service)), None)
    if not serv:
      return None
    act = next((act for act in serv.Actions if act.Name == action), None)
    if not act :
      return None
    msg_body = \
      '<?xml version="1.0"?>\n' \
      '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">\n' \
      '<s:Body>\n' \
      '<u:##action## xmlns:u="urn:schemas-upnp-org:service:##service##:1">\n' \
      '##arguments##' \
      '</u:##action##>\n' \
      '</s:Body>\n' \
      '</s:Envelope>'
    msg_body = msg_body.replace('##service##', service)
    msg_body = msg_body.replace('##action##', action)
    msg_arguments = ''
    cnt_arg = 0
    out_args = {}
    for arg in act.Arguments:
      if arg.Direction == 'in':
        if not arguments:
          return None
        cnt_arg += 1
        if not arg.Name in arguments:
          if arg.DefaultValue:
            arguments[arg.Name] = arg.DefaultValue
          else:
            return None
        msg_arguments = msg_arguments + '<%s>%s</%s>' % (arg.Name, html.escape(str(arguments[arg.Name])) , arg.Name) + '\n'
      if arg.Direction == 'out':
        out_args[arg.Name] = None
    if arguments:
      if len(arguments) > cnt_arg:
        return None
    msg_body = msg_body.replace('##arguments##', msg_arguments)
    msg_body_b = msg_body.encode("utf-8")
    soap_action = 'urn:schemas-upnp-org:service:%s:1#%s' % (service, action)
    msg_headers = {
      'User-Agent': 'PlayOn DLNA Controler',
      'Host': '%s' % urllib.parse.urlparse(renderer.BaseURL).netloc,
      'Content-Type': 'text/xml; charset="utf-8"',
      'Content-Length': '%s' % len(msg_body_b),
      'SOAPAction': '"%s"' % soap_action
    }
    return serv.ControlURL, msg_headers, msg_body_b, out_args

  def send_soap_msg(self, renderer, service, action, soap_timeout=5, **arguments):
    if not renderer:
      return None
    cturl_headers_body_oargs = self._build_soap_msg(renderer, service, action, **arguments)
    if not cturl_headers_body_oargs:
      self.logger.log('Renderer %s -> service %s -> abandon de l\'envoi de la commande %s' % (renderer.FriendlyName, service, action), 1)
      return None
    self.logger.log('Renderer %s -> service %s -> envoi de la commande %s' % (renderer.FriendlyName, service, action), 2)
    try:
      requ = urllib.request.Request(cturl_headers_body_oargs[0], cturl_headers_body_oargs[2], cturl_headers_body_oargs[1])
      resp = urllib.request.urlopen(requ, timeout=soap_timeout)
    except:
      self.logger.log('Renderer %s -> service %s -> échec de l\'envoi de la commande %s' % (renderer.FriendlyName, service, action), 1)
      return None
    if resp.status != HTTPStatus.OK:
      self.logger.log('Renderer %s -> service %s -> échec de l\'envoi de la commande %s' % (renderer.FriendlyName, service, action), 1)
      return None
    self.logger.log('Renderer %s -> service %s -> succès de l\'envoi de la commande %s' % (renderer.FriendlyName, service, action), 1)    
    try:
      msg = resp.read()
    except:
      msg = None
    if not msg:
      self.logger.log('Renderer %s -> service %s -> échec de la réception de la réponse à la commande %s' % (renderer.FriendlyName, service, action), 2)
      return None
    try:
      root_xml = minidom.parseString(msg)
    except:
      self.logger.log('Renderer %s -> service %s -> échec du traitement de la réponse à la commande %s' % (renderer.FriendlyName, service, action), 2)
      return None
    out_args = cturl_headers_body_oargs[3]
    try:
      for arg in out_args:
        out_args[arg] = _XMLGetNodeText(root_xml.getElementsByTagName(arg)[0])
    except:
      self.logger.log('Renderer %s -> service %s -> échec du traitement de la réponse à la commande %s' % (renderer.FriendlyName, service, action), 2)
      return None
    self.logger.log('Renderer %s -> service %s -> succès de la réception de la réponse à la commande %s' % (renderer.FriendlyName, service, action), 2)
    if out_args:
      return out_args
    else:
      return True
    
  def _build_didl(self, uri, title, kind=None, size=None, duration=None, suburi=None):
    if size:
      size_arg = ' size="%s"' % (size)
    else:
      size_arg = ''
    if duration:
      duration_arg = ' duration="%s"' % (duration)
    else:
      duration_arg = ''
    media_class = 'object.item.videoItem'
    try:
      if kind.lower() == 'audio':
        media_class = 'object.item.audioItem'
      if kind.lower() == 'image':
        media_class = 'object.item.imageItem'
    except:
      pass
    subtype = None
    try:
      subtype = suburi.rsplit('.', 1)[1]
    except:
      pass
    if not subtype:
      suburi = None
    else:
      if len(subtype) > 4:
        suburi = None
    didl_lite = \
      '<DIDL-Lite '\
      'xmlns:dc="http://purl.org/dc/elements/1.1/" ' \
      'xmlns:dlna="urn:schemas-dlna-org:metadata-1-0/" ' \
      'xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" ' \
      'xmlns:sec="http://www.sec.co.kr/" ' \
      'xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/">' \
      '<item restricted="1" id="PlayOn-content" parentID="">' \
      '<upnp:class>%s</upnp:class>' \
      '<dc:title>%s</dc:title>' \
      '<res protocolInfo="http-get:*:application/octet-stream:DLNA.ORG_PN=;DLNA.ORG_OP=00;DLNA.ORG_FLAGS=01700000000000000000000000000000" sec:URIType="public"%s%s>%s</res>' \
      '%s' \
      '</item>' \
      '</DIDL-Lite>' % (media_class, html.escape(title), size_arg, duration_arg, html.escape(uri), '<sec:CaptionInfoEx sec:type="%s">%s</sec:CaptionInfoEx>' %(html.escape(subtype), html.escape(suburi)) if suburi else '')
    return didl_lite
    
  def send_URI(self, renderer, uri, title, kind=None, size=None, duration=None, suburi=None):
    didl_lite = self._build_didl(uri, title, kind, size, duration, suburi)
    out_args = self.send_soap_msg(renderer, 'AVTransport', 'SetAVTransportURI', soap_timeout=10, InstanceID=0, CurrentURI=uri, CurrentURIMetaData=didl_lite)
    if not out_args:
      return None
    else:
      return True
      
  def send_Local_URI(self, renderer, uri, title, kind=None, size=None, duration=None, suburi=None):
    didl_lite = self._build_didl(uri, title, kind, size, duration, suburi)
    didl_lite = didl_lite.replace(' sec:URIType="public"', '').replace('DLNA.ORG_OP=00', 'DLNA.ORG_OP=01').replace('DLNA.ORG_FLAGS=017', 'DLNA.ORG_FLAGS=217')
    out_args = self.send_soap_msg(renderer, 'AVTransport', 'SetAVTransportURI', soap_timeout=10, InstanceID=0, CurrentURI=uri, CurrentURIMetaData=didl_lite)
    if not out_args:
      return None
    else:
      return True
  
  def send_Play(self, renderer):
    out_args = self.send_soap_msg(renderer, 'AVTransport', 'Play', soap_timeout=30, InstanceID=0, Speed=1)
    if not out_args:
      return None
    else:
      return True

  def send_Resume(self, renderer):
    out_args = self.send_soap_msg(renderer, 'AVTransport', 'Play', InstanceID=0, Speed=1)
    if not out_args:
      return None
    else:
      return True

  def send_Stop(self, renderer):
    out_args = self.send_soap_msg(renderer, 'AVTransport', 'Stop', InstanceID=0)
    if not out_args:
      return None
    else:
      return True
      
  def send_Pause(self, renderer):
    out_args = self.send_soap_msg(renderer, 'AVTransport', 'Pause', InstanceID=0)
    if not out_args:
      return None
    else:
      return True

  def send_Seek(self, renderer, target="0:00:00"):
    out_args = self.send_soap_msg(renderer, 'AVTransport', 'Seek', InstanceID=0, Unit="REL_TIME", Target=target)
    if not out_args:
      return None
    else:
      return True

  def get_Position(self, renderer):
    out_args = self.send_soap_msg(renderer, 'AVTransport', 'GetPositionInfo', soap_timeout=3, InstanceID=0)
    if not out_args:
      return None
    return out_args['RelTime']

  def get_Duration(self, renderer):
    out_args = self.send_soap_msg(renderer, 'AVTransport', 'GetMediaInfo', soap_timeout=3, InstanceID=0)
    if not out_args:
      return None
    return out_args['MediaDuration']

  def get_TransportInfo(self, renderer):
    out_args = self.send_soap_msg(renderer, 'AVTransport', 'GetTransportInfo', InstanceID=0)
    if not out_args:
      return None
    return out_args['CurrentTransportState'], out_args['CurrentTransportStatus']

  def get_StoppedReason(self, renderer):
    out_args = self.send_soap_msg(renderer, 'AVTransport', 'X_GetStoppedReason', InstanceID=0)
    if not out_args:
      return None
    return out_args['StoppedReason'], out_args['StoppedReasonData']

  def _start_event_notification_receiver(self, EventListener, verbosity):
    EventListener.DLNAEventNotificationBoundHandler = partial(DLNAEventNotificationHandler, EventListener=EventListener)
    with socketserver.TCPServer((self.ip, EventListener.port), EventListener.DLNAEventNotificationBoundHandler) as EventListener.DLNAEventNotificationReceiver:
      EventListener.DLNAEventNotificationReceiver.logger = log_event(verbosity)
      EventListener.DLNAEventNotificationReceiver.serve_forever()
    EventListener.is_running = None

  def _shutdown_event_notification_receiver(self, EventListener):
    if EventListener.is_running:
      EventListener.is_running = False
      EventListener.DLNAEventNotificationReceiver.shutdown()

  def new_event_subscription(self, renderer, service, port, log=False):
    if not renderer:
      return None
    serv = next((serv for serv in renderer.Services if serv.Id == ('urn:upnp-org:serviceId:' + service)), None)
    if not serv:
      return None
    EventListener = DLNAEventListener(log)
    EventListener.port = port
    EventListener.Renderer = renderer
    EventListener.Service = serv
    return EventListener

  def send_event_subscription(self, EventListener, timeout):
    if not EventListener:
      return None
    msg_headers = {
    'Host': '%s' % urllib.parse.urlparse(EventListener.Renderer.BaseURL).netloc,
    'Callback': '<http://%s:%s/>' % (self.ip, EventListener.port),
    'NT': 'upnp:event',
    'Timeout': 'Second-%s' % timeout
    }
    if EventListener.is_running:
      self.logger.log('Renderer %s -> service %s -> souscription au serveur d\'événements déjà en place' % (EventListener.Renderer.FriendlyName, EventListener.Service.Id[23:]), 1)
      return None
    EventListener.is_running = True
    receiver_thread = threading.Thread(target=self._start_event_notification_receiver, args=(EventListener, self.verbosity))
    receiver_thread.start()
    requ = urllib.request.Request(url=EventListener.Service.SubscrEventURL, headers=msg_headers, method='SUBSCRIBE')
    try:
      resp = urllib.request.urlopen(requ, timeout=5)
    except:
      self._shutdown_event_notification_receiver(EventListener)
      self.logger.log('Renderer %s -> service %s -> échec de la demande de souscription au serveur d\'événements' % (EventListener.Renderer.FriendlyName, EventListener.Service.Id[23:]), 1)
      return None
    if resp.status != HTTPStatus.OK:
      self._shutdown_event_notification_receiver(EventListener)
      self.logger.log('Renderer %s -> service %s -> échec de la demande de souscription au serveur d\'événements' % (EventListener.Renderer.FriendlyName, EventListener.Service.Id[23:]), 1)
      return None
    EventListener.SID = resp.getheader('SID')
    if EventListener.is_running:
      self.logger.log('Renderer %s -> service %s -> souscription au serveur d\'événements sous le SID %s pour une durée de %s' % (EventListener.Renderer.FriendlyName, EventListener.Service.Id[23:], EventListener.SID, resp.getheader('TIMEOUT')), 1)
      return True
    else:
      self.logger.log('Renderer %s -> service %s -> échec de la demande de souscription au serveur d\'événements' % (EventListener.Renderer.FriendlyName, EventListener.Service.Id[23:]), 1)
      return None
    
  def renew_event_subscription(self, EventListener, timeout):
    if not EventListener:
      return None
    msg_headers = {
    'Host': '%s' % urllib.parse.urlparse(EventListener.Renderer.BaseURL).netloc,
    'SID': '%s' % EventListener.SID,
    'Timeout': 'Second-%s' % timeout
    }
    requ = urllib.request.Request(url=EventListener.Service.SubscrEventURL, headers=msg_headers, method='SUBSCRIBE')
    try:
      resp = urllib.request.urlopen(requ, timeout=5)
    except:
      self.logger.log('Renderer %s -> service %s -> échec de la demande de renouvellement de souscription de SID %s au serveur d\'événements' % (EventListener.Renderer.FriendlyName, EventListener.Service.Id[23:], EventListener.SID), 1)
      return None
    if resp.status != HTTPStatus.OK:
      self.logger.log('Renderer %s -> service %s -> échec de la demande de renouvellement de souscription de SID %s au serveur d\'événements' % (EventListener.Renderer.FriendlyName, EventListener.Service.Id[23:], EventListener.SID), 1)
      return None
    self.logger.log('Renderer %s -> service %s -> renouvellement de la souscription de SID %s au serveur d\'événements pour une durée de %s' % (EventListener.Renderer.FriendlyName, EventListener.Service.Id[23:], EventListener.SID, resp.getheader('TIMEOUT')), 1)
    return True
    
  def send_event_unsubscription(self, EventListener):
    if not EventListener:
      return None
    msg_headers = {
    'Host': '%s' % urllib.parse.urlparse(EventListener.Renderer.BaseURL).netloc,
    'SID': '%s' % EventListener.SID
    }
    requ = urllib.request.Request(url=EventListener.Service.SubscrEventURL, headers=msg_headers, method='UNSUBSCRIBE')
    try:
      resp = urllib.request.urlopen(requ, timeout=5)
    except:
      self.logger.log('Renderer %s -> service %s -> échec de la demande de fin de souscription de SID %s au serveur d\'événements' % (EventListener.Renderer.FriendlyName, EventListener.Service.Id[23:], EventListener.SID), 1)
      self._shutdown_event_notification_receiver(EventListener)
      return None
    if resp.status != HTTPStatus.OK:
      self.logger.log('Renderer %s -> service %s -> échec de la demande de fin de souscription de SID %s au serveur d\'événements' % (EventListener.Renderer.FriendlyName, EventListener.Service.Id[23:], EventListener.SID), 1)
      self._shutdown_event_notification_receiver(EventListener)
      return None
    self._shutdown_event_notification_receiver(EventListener)
    self.logger.log('Renderer %s -> service %s -> fin de la souscription de SID %s au serveur d\'événements' % (EventListener.Renderer.FriendlyName, EventListener.Service.Id[23:], EventListener.SID), 1)
    return True

  def add_event_warning(self, EventListener, property, *values, WarningEvent=None):
    warning = DLNAEventWarning(EventListener, property, *values, WarningEvent=WarningEvent)
    EventListener.Warnings.append(warning)
    return warning
    
  def wait_for_warning(self, warning, timeout=None, clear=None):
    if clear:
      warning.ReferenceSEQ = warning.EventListener.CurrentSEQ
      warning.WarningEvent.clear()
    warn_event = warning.WarningEvent.wait(timeout)
    if warn_event:
      warning.WarningEvent.clear()
      return warning.TriggerLastValue
    else:
      return None

  def _start_advertisement_receiver(self):
    self.DLNAAdvertisementBoundHandler = partial(DLNAAdvertisementHandler, Controler=self)
    with DLNAAdvertisementServer(('', 1900), self.DLNAAdvertisementBoundHandler, verbosity=self.verbosity) as self.DLNAAdvertisementReceiver:
      if self.advert_status_change == None:
        self.advert_status_change = threading.Event()
      self.DLNAAdvertisementReceiver.advert_status_change = self.advert_status_change
      self.DLNAAdvertisementReceiver.serve_forever()
    self.is_advert_receiver_running = None

  def _shutdown_advertisement_receiver(self):
    if self.is_advert_receiver_running:
      try:
        self.DLNAAdvertisementReceiver.shutdown()
      except:
        pass
    self.is_advert_receiver_running = False

  def start_advertisement_listening(self, AdvertisementEvent=None):
    if self.is_advert_receiver_running:
      self.logger.log('Écoute des publicités de renderer déjà activée', 1)
    else:
      self.is_advert_receiver_running = True
      self.logger.log('Démarrage de l\'écoute des publicités de renderer', 1)
      if isinstance(AdvertisementEvent, threading.Event):
        self.advert_status_change = AdvertisementEvent
      else:
        self.advert_status_change = threading.Event()
      receiver_thread = threading.Thread(target=self._start_advertisement_receiver)
      receiver_thread.start()
      return self.advert_status_change
  
  def stop_advertisement_listening(self):
    if self.is_advert_receiver_running:
      self.logger.log('Fin de l\'écoute des publicités de renderer', 1)
      self._shutdown_advertisement_receiver()

  def wait_for_advertisement(self, timeout=None):
    adv_event = None
    try:
      adv_event = self.advert_status_change.wait(timeout)
    except:
      pass
    if adv_event:
      self.advert_status_change.clear()
    return adv_event


class WebSocketDataStore:

  def __init__(self, IncomingEvent=None):
    self.outgoing = []
    self.incoming = []
    self.incoming_text_only = False
    self.before_shutdown = None
    self.o_condition = threading.Condition()
    if isinstance(IncomingEvent, threading.Event):
      self.IncomingEvent = IncomingEvent
    else:
      self.IncomingEvent = threading.Event()

  def set_outgoing(self, ind, value):
    if ind >= len(self.outgoing):
      self.outgoing = self.outgoing + [None]*(ind - len(self.outgoing) + 1)
    self.outgoing[ind] = str(value)
    self.o_condition.acquire()
    self.o_condition.notify_all()
    self.o_condition.release()

  def add_outgoing(self, value):
    self.outgoing.append(str(value))
    self.o_condition.acquire()
    self.o_condition.notify_all()
    self.o_condition.release()

  def set_before_shutdown(self, value):
    self.before_shutdown = value

  def add_incoming(self, value):
    self.incoming.append(value)
    self.IncomingEvent.set()

  def get_incoming(self):
    if self.incoming:
      return self.incoming.pop(0)
    else:
      return None

  def wait_for_incoming_event(self, timeout=None, clear=None):
    if clear:
      self.IncomingEvent.clear()
    incoming_event = self.IncomingEvent.wait(timeout)
    if incoming_event:
      self.IncomingEvent.clear()
      return True
    else:
      return None

  def reinit(self):
    self.outgoing = []
    self.incoming = []
    self.before_shutdown = None
    try:
      self.o_condition.release()
    except:
      pass
    self.IncomingEvent.clear()


class WebSocketRequestHandler(socketserver.StreamRequestHandler):

  PING_PONG_STRICT = False
  MAX_INACTIVE_TIME = 120
  PONG_TIMEOUT = 20
  timeout = 5

  def __init__(self, *args, **kwargs):
    self.ClientClosing = False
    self.ServerClosing = False
    self.Error = 0
    self.ShutdownMessageTime = None
    self.CloseMessageTime = None
    self.Closed = False
    self.Buffer = bytearray()
    self.MessageData = None
    self.MessageType = None
    self.MessageReady = False
    self.FrameType = None
    self.FrameLength = None
    self.DataLength = None
    self.SendEvent = threading.Event()
    self.PingData = None
    self.PingLock = threading.Lock()
    self.PongData = None
    self.CloseData = None
    self.LastReceptionTime = None
    self.PendingPings = 0
    self.PingTime = None
    self.OutgoingStore = []
    super().__init__(*args, **kwargs)

  @classmethod
  def XOR32_decode(cls, mask, coded_data):
    decoded_data = b''
    for i in range(len(coded_data)):
      decoded_data += bytes([coded_data[i] ^ mask[i%4]])
    return decoded_data

  @classmethod
  def XOR32_encode(cls, mask, data):
    encoded_data = b''
    for i in range(len(data)):
      encoded_data += bytes([data[i] ^ mask[i%4]])
    return encoded_data

  @classmethod
  def build_frame(cls, type, data):
    opcodes = {'text_data': 0x01, 'binary_data': 0x02, 'close': 0x08, 'ping': 0x09, 'pong': 0x0a}
    if type == 'data':
      if isinstance(data, str):
        type = 'text_data'
        data_b = data.encode('utf-8')
      elif isinstance(data, bytes):
        type = 'binary_data'
        data_b = data
      else:
        return None
    else:
      data_b = data
    if not type.lower() in opcodes:
      return None
    if len(data_b) <= 0x7d:
      frame = struct.pack('B', 0x80 + opcodes[type]) + struct.pack('B',len(data_b)) + data_b
    elif len(data_b) <= 0xffff:
      frame = struct.pack('B', 0x80 + opcodes[type]) + struct.pack('B', 0x7e) + struct.pack('!H',len(data_b)) + data_b
    elif len(data_b) <= 0x7fffffffffffffff:
      frame = struct.pack('B', 0x80 + opcodes[type]) + struct.pack('B', 0x7f) + struct.pack('!Q',len(data_b)) + data_b
    else:
      return None
    return frame

  def watch_datastore(self):
    while not self.ClientClosing and not self.ServerClosing and not self.Closed:
      self.server.DataStore.o_condition.acquire()
      while self.server.DataStore.outgoing == self.OutgoingStore:
        self.server.DataStore.o_condition.wait(0.5)
        if self.ClientClosing or self.ServerClosing or self.Closed:
          break
      self.server.DataStore.o_condition.release()
      self.SendEvent.set()

  def send_ping(self):
    try:
      self.request.sendall(WebSocketRequestHandler.build_frame('ping', b'ping'))
    except:
      return False
    return True
      
  def send_pong(self):
    if self.PingData == None:
      return False
    self.PingLock.acquire()
    try:
      self.request.sendall(WebSocketRequestHandler.build_frame('pong', self.PingData))
    except:
      return False
    finally:
      self.PingData = None
      self.PingLock.release()
    return True

  def send_close(self, data=b''):
    try:
      self.request.sendall(WebSocketRequestHandler.build_frame('close', data))
    except:
      return False
    return True

  def send_data(self, data=''):
    try:
      self.request.sendall(WebSocketRequestHandler.build_frame('data', data))
    except:
      return False
    return True

  def get_type(self):
    opcodes = {0x00: 'data', 0x01: 'data', 0x02: 'data', 0x08: 'close', 0x09: 'ping', 0x0a: 'pong'}
    if len(self.Buffer) == 0:
      return False
    self.FrameType = opcodes.get(self.Buffer[0] & 0x0f, 'bad')
    return True

  def get_length(self):
    if len(self.Buffer) < 2:
      return False
    if self.Buffer[1] & 0x7f <= 0x7d:
      self.DataLength = self.Buffer[1] & 0x7f
      self.FrameLength = 6 + self.DataLength
    elif self.Buffer[1] & 0x7f == 0x7e:
      if len(self.Buffer) < 4:
        return False
      self.DataLength = struct.unpack('!H', self.Buffer[2:4])[0]
      self.FrameLength = 8 + self.DataLength
    elif self.Buffer[1] & 0x7f == 0x7f:
      if len(self.Buffer) < 10:
        return False
      self.DataLength = struct.unpack('!Q', self.Buffer[2:10])[0]
      self.FrameLength = 14 + self.DataLength
    return True

  def check_mask(self):
    if len(self.Buffer) < 2:
      return False
    if self.Buffer[1] >> 7 != 1:
      return False
    return True

  def get_data(self):
    if not self.FrameType or not self.FrameLength or self.DataLength == None:
      return False
    if len(self.Buffer) < self.FrameLength:
      return False
    if self.FrameType == 'data':
      if self.MessageType == None:
        if self.Buffer[0] & 0x0f == 0:
          return False
        else:
          self.MessageType = {0x01: 'text', 0x02: 'binary'}[self.Buffer[0] & 0x0f]
          self.MessageData = b''
      else:
        if self.Buffer[0] & 0x0f != 0:
          self.MessageType = {0x01: 'text', 0x02: 'binary'}[self.Buffer[0] & 0x0f]
          self.MessageData = b''
    if self.FrameType != 'data' and self.Buffer[0] >> 7 != 1:
      return False
    if self.FrameType == 'data':
      self.MessageData = self.MessageData + WebSocketRequestHandler.XOR32_decode(self.Buffer[self.FrameLength-self.DataLength-4:self.FrameLength-self.DataLength], self.Buffer[self.FrameLength-self.DataLength:self.FrameLength])
    elif self.FrameType == 'close':
      if self.DataLength <= 0x7d:
        self.CloseData = WebSocketRequestHandler.XOR32_decode(self.Buffer[2:6], self.Buffer[6:self.FrameLength])
      else:
        return False
    elif self.FrameType == 'ping':
      if self.DataLength <= 0x7d:
        self.PingLock.acquire()
        self.PingData = WebSocketRequestHandler.XOR32_decode(self.Buffer[2:6], self.Buffer[6:self.FrameLength])
        self.PingLock.release()
      else:
        return False
    elif self.FrameType == 'pong':
      if self.DataLength <= 0x7d:
        self.PongData = WebSocketRequestHandler.XOR32_decode(self.Buffer[2:6], self.Buffer[6:self.FrameLength])
      else:
        return False
    else:
      return False
    if self.FrameType == 'data' and self.Buffer[0] >> 7 == 1:
      if self.MessageType == 'text':
        try:
          self.MessageData = self.MessageData.decode('utf-8')
        except:
          return False
      self.MessageReady = True
    return True

  def purge_frame(self):
    self.FrameType = None
    del self.Buffer[0:self.FrameLength]
    self.FrameLength = None
    self.DataLength = None

  def handle_out(self):
    watch_datastore_thread = threading.Thread(target=self.watch_datastore)
    watch_datastore_thread.start()
    while not self.Closed:
      self.SendEvent.clear()
      if self.ClientClosing:
        if not self.CloseMessageTime:
          if self.CloseData == None:
            self.CloseData = b''
          if self.send_close(self.CloseData[0:2]):
            self.server.logger.log('WebSocket serveur %s:%s -> WebSocket %s:%s -> succès de l\'envoi de l\'accusé de réception de l\'avis de fin de connexion' % (self.server.Address[0], self.server.Address[1], self.client_address[0], self.client_address[1]), 2)
          else:
            self.server.logger.log('WebSocket serveur %s:%s -> WebSocket %s:%s -> échec de l\'envoi de l\'accusé de réception de l\'avis de fin de connexion' % (self.server.Address[0], self.server.Address[1], self.client_address[0], self.client_address[1]), 2)
        self.CloseData = None
        self.Closed = True
        break
      if self.Error:
        self.server.logger.log('WebSocket serveur %s:%s -> WebSocket %s:%s -> envoi d\'avis de fin de connexion pour cause d\'erreur %s' % (self.server.Address[0], self.server.Address[1], self.client_address[0], self.client_address[1], self.Error), 2)
        if self.send_close(struct.pack('!H', self.Error)):
          self.server.logger.log('WebSocket serveur %s:%s -> WebSocket %s:%s -> succès de l\'envoi de l\'avis de fin de connexion' % (self.server.Address[0], self.server.Address[1], self.client_address[0], self.client_address[1]), 2)
        else:
          self.server.logger.log('WebSocket serveur %s:%s -> WebSocket %s:%s -> échec de l\'envoi de l\'avis de fin de connexion' % (self.server.Address[0], self.server.Address[1], self.client_address[0], self.client_address[1]), 2)
        self.Closed = True
        break
      if self.PingData != None:
        self.send_pong()
      if self.ServerClosing:
        shutdown_value = True
        if self.ShutdownMessageTime and not self.CloseMessageTime:
          if time.time() - self.ShutdownMessageTime > 3:
            shutdown_value = False
        if not self.CloseMessageTime and not self.ShutdownMessageTime:
          shutdown_value = self.server.DataStore.before_shutdown
          if shutdown_value:
            if self.send_data(shutdown_value):
              self.ShutdownMessageTime = time.time()
              self.server.logger.log('WebSocket serveur %s:%s -> WebSocket %s:%s -> succès de l\'envoi de la donnée de terminaison %s' % (self.server.Address[0], self.server.Address[1], self.client_address[0], self.client_address[1], shutdown_value), 2)
            else:
              shutdown_value = False
              self.server.logger.log('WebSocket serveur %s:%s -> WebSocket %s:%s -> échec de l\'envoi de la donnée de terminaison %s' % (self.server.Address[0], self.server.Address[1], self.client_address[0], self.client_address[1], shutdown_value), 2)
        if not shutdown_value:
          if self.send_close():
            self.server.logger.log('WebSocket serveur %s:%s -> WebSocket %s:%s -> succès de l\'envoi de l\'avis de fin de connexion' % (self.server.Address[0], self.server.Address[1], self.client_address[0], self.client_address[1]), 2)
          else:
            self.server.logger.log('WebSocket serveur %s:%s -> WebSocket %s:%s -> échec de l\'envoi de l\'avis de fin de connexion' % (self.server.Address[0], self.server.Address[1], self.client_address[0], self.client_address[1]), 2)
          self.CloseMessageTime = time.time()
          break
      if not self.ServerClosing and self.server.DataStore.outgoing != self.OutgoingStore:
        nb_values = len(self.server.DataStore.outgoing)
        for i in range(nb_values):
          if self.ClientClosing or self.ServerClosing:
            break
          if i == len(self.OutgoingStore):
            self.OutgoingStore.append(None)
          try:
            data_value = self.server.DataStore.outgoing[i]
          except:
            break
          if data_value != self.OutgoingStore[i]:
            if self.send_data(data_value):
              self.server.logger.log('WebSocket serveur %s:%s -> WebSocket %s:%s -> envoi de la donnée %s' % (self.server.Address[0], self.server.Address[1], self.client_address[0], self.client_address[1], data_value), 2)
            else:
              self.server.logger.log('WebSocket serveur %s:%s -> WebSocket %s:%s -> échec de l\'envoi de la donnée %s' % (self.server.Address[0], self.server.Address[1], self.client_address[0], self.client_address[1], data_value), 2)
              self.Error = 1002
              continue
            self.OutgoingStore[i] = data_value
      if not self.ServerClosing:
        cur_time = time.time()
        if (cur_time - self.LastReceptionTime > WebSocketRequestHandler.MAX_INACTIVE_TIME / 3 and self.PendingPings == 0) or (cur_time - self.LastReceptionTime > 2 * WebSocketRequestHandler.MAX_INACTIVE_TIME / 3 and self.PendingPings <= 1):
          if not self.PingTime:
            self.PingTime = cur_time
          self.send_ping()
          self.PendingPings += 1
        if WebSocketRequestHandler.PING_PONG_STRICT and self.PingTime:
          if cur_time - self.PingTime > WebSocketRequestHandler.PONG_TIMEOUT / 2 and self.PendingPings <=1:
            self.send_ping()
            self.PendingPings += 1
        if cur_time - self.LastReceptionTime < WebSocketRequestHandler.MAX_INACTIVE_TIME and not WebSocketRequestHandler.PING_PONG_STRICT:
          self.PingTime = None
          self.PendingPings = 0
      self.SendEvent.wait(0.5)
    if watch_datastore_thread.is_alive():
      try:
        watch_datastore_thread.join()
      except:
        pass  
   
  def handle(self):
    if self.server.__dict__['_BaseServer__shutdown_request'] or self.server.__dict__['_BaseServer__is_shut_down'].is_set():
      return
    self.server.logger.log('WebSocket serveur %s:%s -> demande de connexion du WebSocket %s:%s' % (self.server.Address[0], self.server.Address[1], self.client_address[0], self.client_address[1]), 2)
    resp_err_br = \
      'HTTP/1.1 400 Bad Request\r\n' \
      'Connection: close\r\n' \
      '\r\n'
    req = HTTPMessage(self.request)
    if req.method != 'GET' or not 'websocket' in req.header('Upgrade', '').lower() or not 'upgrade' in req.header('Connection', '').lower() or not req.header('Sec-WebSocket-Key', ''):
      try:
        self.request.sendall(resp_err_br.encode('ISO-8859-1'))
        self.server.logger.log('WebSocket serveur %s:%s -> demande de connexion du WebSocket %s:%s invalide' % (self.server.Address[0], self.server.Address[1], self.client_address[0], self.client_address[1]), 2)
      except:
        pass
      return
    guid = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
    sha1 = hashlib.sha1((req.header('Sec-WebSocket-Key') + guid).encode('utf-8')).digest()
    ws_acc = base64.b64encode(sha1).decode('utf-8')
    resp= \
      'HTTP/1.1 101 Switching Protocols\r\n' \
      'Upgrade: websocket\r\n' \
      'Connection: Upgrade\r\n' \
      'Sec-WebSocket-Accept: %s\r\n' \
      '\r\n' % (ws_acc)
    try:
      self.request.sendall(resp.encode('ISO-8859-1'))
    except:
      self.server.logger.log('WebSocket serveur %s:%s -> échec de l\'envoi de la réponse à la demande de connexion du WebSocket %s:%s' % (self.server.Address[0], self.server.Address[1], self.client_address[0], self.client_address[1]), 2)
      return
    self.server.logger.log('WebSocket serveur %s:%s -> connexion au WebSocket %s:%s' % (self.server.Address[0], self.server.Address[1], self.client_address[0], self.client_address[1]), 1)
    self.LastReceptionTime = time.time()
    out_handler_thread = threading.Thread(target=self.handle_out)
    out_handler_thread.start()
    with selectors.DefaultSelector() as selector:
      selector.register(self.request, selectors.EVENT_READ)
      while not self.Closed:
        if self.CloseMessageTime:
          if time.time() - self.CloseMessageTime > 2:
            self.Closed = True
            break
        if not self.FrameType and len(self.Buffer) > 0:
          ready = True
        else:
          ready = selector.select(0.5)
          if ready:
            chunk = None
            try:
              chunk = self.request.recv(65535)
            except:
              ready = False
              self.Error = 1002
              self.SendEvent.set()
              break
            if not chunk:
              ready = False
              self.Error = 1002
              self.SendEvent.set()
              break
            else:
              self.LastReceptionTime = time.time()
              if not WebSocketRequestHandler.PING_PONG_STRICT:
                self.PingTime = None
                self.PendingPings = 0
              self.Buffer = self.Buffer + chunk
        if self.server.__dict__['_BaseServer__shutdown_request'] or self.server.__dict__['_BaseServer__is_shut_down'].is_set():
          self.ServerClosing = True
          self.SendEvent.set()
        if WebSocketRequestHandler.PING_PONG_STRICT and self.PingTime:
          if time.time() - self.PingTime > WebSocketRequestHandler.PONG_TIMEOUT:
            self.Error = 1002
            self.SendEvent.set()
            break
        if not ready:
          if time.time() - self.LastReceptionTime > WebSocketRequestHandler.MAX_INACTIVE_TIME:
            self.Error = 1002
            self.SendEvent.set()
            break
          continue
        self.get_type()
        if self.FrameType == 'bad':
          self.Error = 1002
          self.SendEvent.set()
          break
        if not self.get_length():
          continue
        if not self.check_mask():
          self.Error = 1002
          self.SendEvent.set()
          break
        if len(self.Buffer) < self.FrameLength:
          continue
        if not self.get_data():
          self.Error = 1002
          self.SendEvent.set()
          break
        if self.FrameType == 'close':
          if self.CloseMessageTime:
            self.Closed = True
            self.server.logger.log('WebSocket serveur %s:%s -> accusé de réception de fin de connexion du WebSocket %s:%s' % (self.server.Address[0], self.server.Address[1], self.client_address[0], self.client_address[1]), 2)
            break
          else:
            self.server.logger.log('WebSocket serveur %s:%s -> avis de fin de connexion du WebSocket %s:%s' % (self.server.Address[0], self.server.Address[1], self.client_address[0], self.client_address[1]), 2)
            self.ClientClosing = True
            self.SendEvent.set()
            break
        elif self.FrameType == 'ping':
          self.SendEvent.set()
          self.purge_frame()
        elif self.FrameType == 'pong':
          if self.PongData == b'ping':
            self.PingTime = None
            self.PendingPings = 0
          self.purge_frame()
        elif self.FrameType == 'data':
          if self.MessageReady:
            if self.server.DataStore.incoming_text_only and self.MessageType != 'text':
              self.Error = 1003
              self.SendEvent.set()
              break
            self.server.logger.log('WebSocket serveur %s:%s -> WebSocket %s:%s -> réception de la donnée %s' % (self.server.Address[0], self.server.Address[1], self.client_address[0], self.client_address[1], self.MessageData), 2)
            self.server.DataStore.add_incoming(self.MessageData)
            self.MessageData = None
            self.MessageReady = False
            self.MessageType = None
          self.purge_frame()
    if out_handler_thread.is_alive():
      try:
        out_handler_thread.join()
      except:
        pass
    self.server.logger.log('WebSocket serveur %s:%s -> fin de connexion au WebSocket %s:%s' % (self.server.Address[0], self.server.Address[1], self.client_address[0], self.client_address[1]), 1)


class ThreadedWebSocketServer(socketserver.ThreadingTCPServer):

  allow_reuse_address = True

  def shutdown(self):
    super().shutdown()
    self.socket.close()

  def server_close(self):
    pass


class WebSocketServer(threading.Thread):

  def __init__(self, WebSocketServerAddress, WebSocketDataStore, verbosity=0):
    threading.Thread.__init__(self)
    self.verbosity = verbosity
    self.DataStore = WebSocketDataStore
    self.Address = WebSocketServerAddress
    self.is_running = None
    self.shutdown_lock = threading.Lock()

  def run(self):
    self.shutdown_lock.acquire()
    if self.is_running == False:
      return
    self.is_running = True
    with ThreadedWebSocketServer(self.Address, WebSocketRequestHandler) as self.WebSocketServerInstance:
      self.WebSocketServerInstance.logger = log_event(self.verbosity)
      self.WebSocketServerInstance.logger.log('Démarrage du serveur pour Websocket à l\'adresse %s:%s' % (self.Address[0], self.Address[1]), 2)
      self.WebSocketServerInstance.Address = self.Address
      self.WebSocketServerInstance.DataStore = self.DataStore
      self.shutdown_lock.release()
      self.WebSocketServerInstance.serve_forever()
    self.is_running = None
      
  def shutdown(self):
    self.shutdown_lock.acquire()
    if self.is_running:
      self.is_running = False
      try:
        self.WebSocketServerInstance.logger.log('Fermeture du serveur pour Websocket à l\'adresse %s:%s' % (self.Address[0], self.Address[1]), 2)
        self.WebSocketServerInstance.shutdown()
      except:
        pass
    self.is_running = False
    self.shutdown_lock.release()
  

class DLNAWebInterfaceControlDataStore(WebSocketDataStore):

  def __init__(self, IncomingEvent=None):
    super().__init__(IncomingEvent)
    self.outgoing = [None, None, None]
    self.incoming_text_only = True
    self.set_before_shutdown('close')

  def reinit(self):
    super().reinit()
    self.outgoing = [None, None, None]
    self.set_before_shutdown('close')

  @property
  def Status(self):
    return self.outgoing[0]

  @Status.setter
  def Status(self, value):
    self.set_outgoing(0, value)

  @property
  def Position(self):
    return self.outgoing[1]

  @Position.setter
  def Position(self, value):
    self.set_outgoing(1, value)

  @property
  def Duration(self):
    return self.outgoing[2]

  @Duration.setter
  def Duration(self, value):
    self.set_outgoing(2, value)

  @property
  def Command(self):
    return self.get_incoming()

  @Command.setter
  def Command(self, value):
    self.add_incoming(value)

  @property
  def Redirect(self):
    if self.before_shutdown == 'redirect':
      return True
    else:
      return False

  @Redirect.setter
  def Redirect(self, value):
    if value:
      self.set_before_shutdown('redirect')
    else:
      self.set_before_shutdown('close')


class DLNAWebInterfaceRenderersDataStore(WebSocketDataStore):

  def __init__(self, IncomingEvent=None):
    super().__init__(IncomingEvent)
    self.incoming_text_only = True
    self.set_before_shutdown('close')

  def reinit(self):
    super().reinit()
    self.set_before_shutdown('close')

  @property
  def Message(self):
    if self.outgoing:
      return self.outgoing[-1]

  @Message.setter
  def Message(self, value):
    self.add_outgoing(value)

  @property
  def Redirect(self):
    if self.before_shutdown == 'redirect':
      return True
    else:
      return False

  @Redirect.setter
  def Redirect(self, value):
    if value:
      self.set_before_shutdown('redirect')
    else:
      self.set_before_shutdown('close')


class DLNAWebInterfaceRequestHandler(server.SimpleHTTPRequestHandler):

  protocol_version = "HTTP/1.1"
  
  HTML_WAIT_TEMPLATE = \
  '<!DOCTYPE html>\r\n' \
  '<html lang="fr-FR">\r\n' \
  '    <meta charset="utf-8">\r\n' \
  '    <title>Page d\'attente</title>\r\n' \
  '  <head>\r\n' \
  '    <meta http-equiv="refresh" content="5;URL=/">\r\n' \
  '  </head>\r\n' \
  '  <body style="background-color:rgb(40,45,50);color:rgb(225,225,225);font-size:32px;">\r\n' \
  '    <h1 style="line-height:20px;font-size:180%;">PlayOn&nbsp;&nbsp;&nbsp;&nbsp;Interface occupée<br></h1>\r\n' \
  '    <p">Quelques secondes de patience...</p>\r\n' \
  '</body>\r\n' \
  '</html>'

  def send_head(self):
    if self.server.Interface.Status == DLNAWebInterfaceServer.INTERFACE_NOT_RUNNING :
      self.close_connection = True
      self.send_error(HTTPStatus.NOT_FOUND, "File not found")
      return None
    self.server.logger.log('Réponse à l\'interface de contrôle %s:%s' % self.client_address, 1)
    if not self.server.Interface.html_ready:
      nb_wait = 0
      while self.server.Interface.Status != DLNAWebInterfaceServer.INTERFACE_NOT_RUNNING and not self.server.Interface.html_ready and nb_wait < 8:
        time.sleep(0.5)
        nb_wait +=1
      if self.server.Interface.Status == DLNAWebInterfaceServer.INTERFACE_NOT_RUNNING :
        self.close_connection = True
        try:
          self.send_error(HTTPStatus.NOT_FOUND, "File not found")
        except:
          pass
        return None
      if not self.server.Interface.html_ready:
        html_wait = DLNAWebInterfaceRequestHandler.HTML_WAIT_TEMPLATE.encode('utf-8')
        self.send_response(HTTPStatus.OK)
        self.send_header("Connection", "keep-alive")
        self.send_header("Content-type", "text/html")
        self.send_header("Content-Length", len(html_wait))
        f = BytesIO(html_wait)
        self.end_headers()
        return f
    if self.path == '/':
      self.send_response(HTTPStatus.TEMPORARY_REDIRECT)
      if self.server.Interface.Status in (DLNAWebInterfaceServer.INTERFACE_DISPLAY_RENDERERS, DLNAWebInterfaceServer.INTERFACE_START):
        self.send_header("Location", "/start.html")
      elif self.server.Interface.Status == DLNAWebInterfaceServer.INTERFACE_CONTROL:
        self.send_header("Location", "/control.html")
      else:
        self.close_connection = True
        self.send_error(HTTPStatus.NOT_FOUND, "File not found")
        return
      self.send_header("Content-Length", 0)
      self.end_headers()
      return None
    if self.path.lower() == '/control.html':
      if self.server.Interface.Status == DLNAWebInterfaceServer.INTERFACE_CONTROL:
        self.send_response(HTTPStatus.OK)
        self.send_header("Connection", "keep-alive")
        self.send_header("Content-type", "text/html")
        self.send_header("Content-Length", len(self.server.Interface.html_control))
        f = BytesIO(self.server.Interface.html_control)
        self.end_headers()
        return f
      else:
        self.send_response(HTTPStatus.TEMPORARY_REDIRECT)
        self.send_header("Location", "/start.html")
        self.send_header("Content-Length", 0)
        self.end_headers()
        return None
    elif self.path.lower() == '/start.html':
      if self.server.Interface.Status in (DLNAWebInterfaceServer.INTERFACE_DISPLAY_RENDERERS, DLNAWebInterfaceServer.INTERFACE_START):
        self.send_response(HTTPStatus.OK)
        self.send_header("Connection", "keep-alive")
        self.send_header("Content-type", "text/html")
        self.send_header("Content-Length", len(self.server.Interface.html_start))
        f = BytesIO(self.server.Interface.html_start)
        self.end_headers()
        return f
      else:
        self.send_response(HTTPStatus.TEMPORARY_REDIRECT)
        self.send_header("Location", "/control.html")
        self.send_header("Content-Length", 0)
        self.end_headers()
        return None
    else:
      self.close_connection = True
      try:
        self.send_error(HTTPStatus.NOT_FOUND, "File not found")
      except:
        pass
      return None

  def do_POST(self):
    if self.path == '/control.html':
      qs = self.rfile.read(int(self.headers.get("Content-Length")))
      self.do_GET()
    elif self.path == '/start.html':
      qs = self.rfile.read(int(self.headers.get("Content-Length")))
      self.server.logger.log('Réception de la donnée de formulaire %s de %s:%s' % (qs, *self.client_address), 2)
      media_src = ''
      media_startfrom = '0:00:00'
      media_subsrc = ''
      renderer_ind = ''
      renderer = None
      try:
        data = urllib.parse.parse_qs(qs.decode('utf-8'))
        if 'MediaSrc' in data:
          media_src = data['MediaSrc'][0]
        if 'MediaStartFrom' in data:
          media_startfrom = (data['MediaStartFrom'][0])[1:]
        if 'MediaSubSrc' in data:
          media_subsrc = data['MediaSubSrc'][0]
        if 'RendererInd' in data:
          renderer = self.server.Interface.DLNARendererControlerInstance.Renderers[int(data['RendererInd'][0])]
      except:
        pass
      if media_src and renderer:
        self.server.post_lock.acquire()
        if self.server.Interface.TargetStatus == DLNAWebInterfaceServer.INTERFACE_START:
          self.server.logger.log('Prise en compte de la demande de lecture de %s%s à partir de %s sur %s de %s:%s' % (media_src, ' et media_subsrc' if media_subsrc else '', media_startfrom, renderer.FriendlyName, *self.client_address), 1)
          self.server.Interface.Renderer = renderer
          self.server.Interface.Renderer_uuid = renderer.UDN[5:]
          self.server.Interface.Renderer_name = renderer.FriendlyName
          self.server.Interface.MediaSrc = media_src
          self.server.Interface.MediaPosition = media_startfrom
          self.server.Interface.MediaSubSrc = media_subsrc
          self.server.Interface.TargetStatus = DLNAWebInterfaceServer.INTERFACE_CONTROL
          self.server.Interface.html_ready = False
        else:
          self.server.logger.log('Rejet de la demande de lecture de %s à partir de %s sur %s de %s:%s' % (media_src, media_startfrom, renderer.FriendlyName, *self.client_address), 1)
        self.server.post_lock.release()
        self.send_response(HTTPStatus.SEE_OTHER)
        self.send_header("Location", "/control.html")
        self.send_header("Content-Length", 0)
        self.end_headers()
      else:
        self.server.logger.log('Rejet de la donnée de formulaire %s de %s:%s' % (qs, *self.client_address), 2)
        self.do_GET()
    else:
      self.close_connection = True
      self.send_error(HTTPStatus.NOT_FOUND, "File not found")
      return None

  def handle(self):
    self.close_connection = True
    with selectors.DefaultSelector() as selector:
      selector.register(self.request, selectors.EVENT_READ)
      closed = False
      while not closed:
        ready = selector.select(0.5)
        if self.server.__dict__['_BaseServer__shutdown_request'] or self.server.__dict__['_BaseServer__is_shut_down'].is_set():
          break
        if ready:
          try:
            self.handle_one_request()
          except:
            pass
          closed = self.close_connection


def _position_to_seconds(position):
  try:
    sec = sum(int(t[0])*t[1] for t in zip(reversed(position.split(':')), [1,60,3600]))
  except:
    return None
  return sec

def _seconds_to_position(seconds):
  try:
    pos = '%d:%02d:%02d' % (seconds // 3600, (seconds % 3600) // 60, seconds % 60)
  except:
    return None
  return pos


class DLNAWebInterfaceServer(threading.Thread):

  INTERFACE_NOT_RUNNING = 0
  INTERFACE_DISPLAY_RENDERERS = 1
  INTERFACE_START = 2
  INTERFACE_CONTROL = 3
  
  SERVER_MODE_NONE = 3
  
  HTML_START_TEMPLATE = \
  '<!DOCTYPE html>\r\n' \
  '<html lang="fr-FR">\r\n' \
  '  <head>\r\n' \
  '    <meta charset="utf-8">\r\n' \
  '    <title>Page de démarrage</title>\r\n' \
  '    <script>\r\n' \
  '      selected = "";\r\n' \
  '      selected_set = "";\r\n' \
  '      function new_socket() {\r\n' \
  '        try {\r\n' \
  '          socket = new WebSocket("ws://" + location.hostname + ":" + String(parseInt(location.port)+2) + "/websocket");\r\n' \
  '        } catch(exception) {\r\n' \
  '          window.alert("Échec de l\'établissement de la connexion WebSocket");\r\n' \
  '        }\r\n' \
  '        socket.onerror = function(event) {\r\n' \
  '          window.location.reload(true);\r\n' \
  '        }\r\n' \
  '        socket.onmessage = function(event) {\r\n' \
  '           if (event.data == "close") {\r\n' \
  '            socket.onclose = function(event) {};\r\n' \
  '            socket.close();\r\n' \
  '            document.getElementById("table").innerHTML = "Renderers - interface close";\r\n' \
  '            document.getElementById("play").style.display = "none";\r\n' \
  '            document.getElementById("reset").style.display = "none";\r\n' \
  '          } else if (event.data == "redirect") {\r\n' \
  '            window.location.replace("##CONTROL-URL##");\r\n' \
  '          } else {\r\n' \
  '            let data_list = event.data.split("&");\r\n' \
  '            if (data_list.length >= 2) {\r\n' \
  '              if (data_list[0] == "command=add") {\r\n' \
  '                let data = [];\r\n' \
  '                for (let i=1; i<data_list.length;i++) {\r\n' \
  '                  let data_name_value = data_list[i].split("=");\r\n' \
  '                  if (data_name_value.length == 2) {\r\n' \
  '                    data.push([data_name_value[0], decodeURIComponent(data_name_value[1])]);\r\n' \
  '                  }\r\n' \
  '                }\r\n' \
  '                if (data.length > 0) {add_renderer(data);}\r\n' \
  '              } else if (data_list[0] == "command=sel") {\r\n' \
  '                let data_name_value = data_list[1].split("=");\r\n' \
  '                if (data_name_value.length == 2) {\r\n' \
  '                  let data = [data_name_value[0], data_name_value[1]];\r\n' \
  '                  sel_renderer(data);\r\n' \
  '                }\r\n' \
  '              } else if (data_list[0] == "command=show") {\r\n' \
  '                let data_name_value = data_list[1].split("=");\r\n' \
  '                if (data_name_value.length == 2) {\r\n' \
  '                  let data = [data_name_value[0], data_name_value[1]];\r\n' \
  '                  show_renderer(data);\r\n' \
  '                }\r\n' \
  '              } else if (data_list[0] == "command=hide") {\r\n' \
  '                let data_name_value = data_list[1].split("=");\r\n' \
  '                if (data_name_value.length == 2) {\r\n' \
  '                  let data = [data_name_value[0], data_name_value[1]];\r\n' \
  '                  hide_renderer(data);\r\n' \
  '                }\r\n' \
  '              }\r\n' \
  '            }\r\n' \
  '          }\r\n' \
  '        }\r\n' \
  '        socket.onclose = function(event) {\r\n' \
  '          new_socket();\r\n' \
  '        }\r\n' \
  '        window.onbeforeunload = function () {\r\n' \
  '          socket.onclose = function(event) {};\r\n' \
  '          socket.close();\r\n' \
  '        }\r\n' \
  '      }\r\n' \
  '      function select_renderer(renderer) {\r\n' \
  '        if (selected != "") {document.getElementById("renderer_" + selected).style.color="rgb(225,225,225)";}\r\n' \
  '        renderer.style.color = "rgb(200,250,240)";\r\n' \
  '        selected = renderer.id.substring(9);\r\n' \
  '        document.getElementById("Renderer").value = selected;\r\n' \
  '      }\r\n' \
  '      function add_renderer(data) {\r\n' \
  '        let renderers = document.getElementById("Renderers");\r\n' \
  '        let renderer_index = "";\r\n' \
  '        let renderer_name = "";\r\n' \
  '        let renderer_ip = "";\r\n' \
  '        let renderer_icon = "";\r\n' \
  '        let renderer_status = "False";\r\n' \
  '        for (let data_item of data) {\r\n' \
  '          if (data_item[0] == "index") {\r\n' \
  '            renderer_index = data_item[1];\r\n' \
  '          } else if (data_item[0] == "name") {\r\n' \
  '            renderer_name = data_item[1];\r\n' \
  '          } else if (data_item[0] == "ip") {\r\n' \
  '            renderer_ip = data_item[1];\r\n' \
  '          } else if (data_item[0] == "icon") {\r\n' \
  '            renderer_icon = data_item[1];\r\n' \
  '          } else if (data_item[0] == "status") {\r\n' \
  '            renderer_status = data_item[1];\r\n' \
  '          }\r\n' \
  '        }\r\n' \
  '        if (renderer_index != "") {\r\n' \
  '          let n_row = renderers.tBodies[0].insertRow();\r\n' \
  '          n_row.id = "renderer_" + renderer_index;\r\n' \
  '          let n_cell = n_row.insertCell();\r\n' \
  '          n_cell.id = "renderer_icon";\r\n' \
  '          n_cell.innerHTML = "<img style=\'height:36px;width:auto;vertical-align:middle;\' src=" + renderer_icon + " alt=\' \'/>";\r\n' \
  '          n_cell = n_row.insertCell();\r\n' \
  '          n_cell.id = "renderer_name";\r\n' \
  '          n_cell.innerHTML = renderer_name;\r\n' \
  '          n_cell = n_row.insertCell();\r\n' \
  '          n_cell.id = "renderer_ip";\r\n' \
  '          n_cell.innerHTML = renderer_ip;\r\n' \
  '          n_cell.style.fontSize="70%";\r\n' \
  '          if (renderer_status == "True") {\r\n' \
  '            n_row.style.display = "table-row";\r\n' \
  '          } else {\r\n' \
  '            n_row.style.display = "none";\r\n' \
  '          }\r\n' \
  '          n_row.onclick = function() {select_renderer(this);};\r\n' \
  '        }\r\n' \
  '      }\r\n' \
  '      function sel_renderer(data) {\r\n' \
  '        if (data[0] == "index") {\r\n' \
  '          selected_set = data[1];\r\n' \
  '          if (selected == "") {\r\n' \
  '            selected = selected_set;\r\n' \
  '            document.getElementById("renderer_" + selected).style.color = "rgb(200,250,240)";\r\n' \
  '            document.getElementById("Renderer").value = selected;\r\n' \
  '          }\r\n' \
  '        }\r\n' \
  '      }\r\n' \
  '      function show_renderer(data) {\r\n' \
  '        if (data[0] == "index") {\r\n' \
  '          document.getElementById("renderer_" + data[1]).style.display = "table-row";}\r\n' \
  '          document.getElementById("renderer_" + data[1]).cells[0].getElementsByTagName("img").item(0).setAttribute("src", document.getElementById("renderer_" + data[1]).cells[0].getElementsByTagName("img").item(0).getAttribute("src"));\r\n' \
  '      }\r\n' \
  '      function hide_renderer(data) {\r\n' \
  '        if (data[0] == "index") {\r\n' \
  '          document.getElementById("renderer_" + data[1]).style.display = "none";\r\n' \
  '          if (selected == data[1]) {\r\n' \
  '            document.getElementById("renderer_" + selected).style.color="rgb(225,225,225)";\r\n' \
  '            selected="";\r\n' \
  '            document.getElementById("Renderer").value = selected;\r\n' \
  '          }\r\n' \
  '        }\r\n' \
  '      }\r\n' \
  '      function reset_button() {\r\n' \
  '        if (selected != "") {document.getElementById("renderer_" + selected).style.color="rgb(225,225,225)";}\r\n' \
  '        selected = "";\r\n' \
  '        if (selected_set != "") {\r\n' \
  '          if (document.getElementById("renderer_" + selected_set).style.display != "none") {\r\n' \
  '            document.getElementById("renderer_" + selected_set).style.color="rgb(200,250,240)";}\r\n' \
  '            selected = selected_set;\r\n' \
  '        }\r\n' \
  '        document.getElementById("Renderer").value = selected;\r\n' \
  '        document.getElementById("URL-").value = URL_set;\r\n' \
  '        document.getElementById("StartFrom").value = StartFrom_set;\r\n' \
  '      }\r\n' \
  '      function play_button() {\r\n' \
  '        let url_ok = true;\r\n' \
  '        let url_lines = document.getElementById("URL-").value.split(/\\r?\\n/g);\r\n' \
  '        document.getElementById("URL").value=url_lines[0];\r\n' \
  '        if (!document.getElementById("URL").checkValidity()) {\r\n' \
  '          url_ok = false;\r\n' \
  '          window.alert("Saisissez une URL valide");\r\n' \
  '        } else {\r\n' \
  '          if (url_lines.length >= 2) {\r\n' \
  '            document.getElementById("SUBURL").value=url_lines[1];\r\n' \
  '            if (!document.getElementById("SUBURL").checkValidity()) {\r\n' \
  '              url_ok = false;\r\n' \
  '              window.alert("Saisissez une URL de sous-titres valide");\r\n' \
  '            }\r\n' \
  '         }\r\n' \
  '        }\r\n' \
  '        if (url_ok) {\r\n' \
  '          if (selected == "") {\r\n' \
  '            window.alert("Sélectionnez d\'abord un renderer");\r\n' \
  '          } else {\r\n' \
  '          document.getElementById("form").submit();\r\n' \
  '          }\r\n' \
  '        }\r\n' \
  '      }\r\n' \
  '    </script>\r\n' \
  '    <style type="text/css">\r\n' \
  '      table {\r\n' \
  '        border: 1px solid rgb(0,0,0);\r\n' \
  '        border-collapse:collapse;\r\n' \
  '        margin-left: 10px;\r\n' \
  '        width: 85%;\r\n' \
  '        table-layout:fixed;\r\n' \
  '      }\r\n' \
  '      td {\r\n' \
  '        border-top: 1px solid rgb(20,20,20);\r\n' \
  '        padding: 5px;\r\n' \
  '        vertical-align:middle;\r\n' \
  '        word-wrap:break-word;\r\n' \
  '        height:20px;\r\n' \
  '      }\r\n' \
  '      td:hover {\r\n' \
  '        cursor:pointer\r\n' \
  '      }\r\n' \
  '      input, textarea {\r\n' \
  '        border: none;\r\n' \
  '        background-color:rgb(30,30,35);\r\n' \
  '        color:rgb(200,250,240);\r\n' \
  '        margin-left:30px;\r\n' \
  '        margin-top:10px;\r\n' \
  '        vertical-align:middle;\r\n' \
  '        word-wrap:break-word;\r\n' \
  '        overflow-y:auto;\r\n' \
  '      }\r\n' \
  '      label {\r\n' \
  '        vertical-align:middle;\r\n' \
  '      }\r\n' \
  '      button {\r\n' \
  '        vertical-align:middle;\r\n' \
  '        border:none;\r\n' \
  '        padding-top:20px;\r\n' \
  '        padding-bottom:20px;\r\n' \
  '        margin-left:10%;\r\n' \
  '        margin-right:10%;\r\n' \
  '        width:250px;\r\n' \
  '        font-size:100%;\r\n' \
  '        font-weight:bold;\r\n' \
  '        cursor:pointer;\r\n' \
  '        display:##DISPLAY##;\r\n' \
  '      }\r\n' \
  '    </style>\r\n' \
  '  </head>\r\n' \
  '  <body style="background-color:rgb(40,45,50);color:rgb(225,225,225);font-size:32px;">\r\n' \
  '    <h1 style="line-height:20px;font-size:180%;">PlayOn&nbsp;&nbsp;&nbsp;&nbsp;Interface de démarrage<br></h1>\r\n' \
  '    <label for="MediaSrc-" style="display:##DISPLAY##;">URL :</label>\r\n' \
  '    <textarea id="URL-" name="MediaSrc-" required style="height:110px;resize:none;display:##DISPLAY##; font-size:50%;width:80%">##URL##</textarea>\r\n' \
  '    <br>\r\n' \
  '    <form method="post" id="form" style="display:##DISPLAY##;">\r\n' \
  '      <input type="URL" id="URL" name="MediaSrc" value="" style="display:none;" required>\r\n' \
  '      <input type="URL" id="SUBURL" name="MediaSubSrc" value="" style="display:none;">\r\n' \
  '      <br>\r\n' \
  '      <label for="StartFrom">Position de lecture :</label>\r\n' \
  '      <input type="time" id="StartFrom" name="MediaStartFrom" step="1" value="0##STARTFROM##" style="height:50px;font-size:70%;">\r\n' \
  '      <input type="hidden" id="Renderer" name="RendererInd" value="" required>\r\n' \
  '    </form>\r\n' \
  '    <script>\r\n' \
  '      new_socket();\r\n' \
  '      URL_set = document.getElementById("URL-").value;\r\n' \
  '      StartFrom_set = document.getElementById("StartFrom").value;\r\n' \
  '    </script>\r\n' \
  '    <button id="play" style="background-color:rgb(200,250,240);" onclick="play_button()">Lire</button>\r\n' \
  '    <button id="reset" style="background-color:rgb(250,220,200);" onclick="reset_button()">Réinitialiser</button>\r\n' \
  '    <br><br>\r\n' \
  '    <table id="Renderers">\r\n' \
  '      <colgroup>\r\n' \
  '      <col style="width:10%">\r\n' \
  '      <col style="width:60%">\r\n' \
  '      <col style="width:20%%;">\r\n' \
  '      </colgroup>\r\n' \
  '      <thead>\r\n' \
  '          <tr>\r\n' \
  '              <th colspan="3" id="table">Renderers</th>\r\n' \
  '          </tr>\r\n' \
  '      </thead>\r\n' \
  '      <tbody>\r\n' \
  '      </tbody>\r\n' \
  '    </table>\r\n' \
  '    <br>\r\n' \
  '  </body>\r\n' \
  '</html>'
  HTML_CONTROL_TEMPLATE = \
  '<!DOCTYPE html>\r\n' \
  '<html lang="fr-FR">\r\n' \
  '  <head>\r\n' \
  '    <meta charset="utf-8">\r\n' \
  '    <title>Page de contrôle</title>\r\n' \
  '    <script>\r\n' \
  '      function new_socket() {\r\n' \
  '        try {\r\n' \
  '          socket = new WebSocket("ws://" + location.hostname + ":" + String(parseInt(location.port)+1) + "/websocket");\r\n' \
  '        } catch(exception) {\r\n' \
  '          window.alert("Échec de l\'établissement de la connexion WebSocket");\r\n' \
  '        }\r\n' \
  '        socket.onerror = function(event) {\r\n' \
  '          window.location.reload(true);\r\n' \
  '        }\r\n' \
  '        socket.onmessage = function(event) {\r\n' \
  '          if (event.data == "close") {\r\n' \
  '            socket.onclose = function(event) {};\r\n' \
  '            socket.close();\r\n' \
  '            document.getElementById("status").innerHTML = "interface close";\r\n' \
  '            document.getElementById("play-pause").style.display = "none";\r\n' \
  '            document.getElementById("stop").style.display = "none";\r\n' \
  '            seekbar.style.display = "none";\r\n' \
  '            seektarget.style.display = "none";\r\n' \
  '            document.getElementById("seektarget").style.display = "none";\r\n' \
  '          } else if (event.data == "redirect") {\r\n' \
  '            document.getElementById("status").innerHTML = "retour";\r\n' \
  '            window.location.replace("##START-URL##");\r\n' \
  '          } else if (event.data == "prêt") {\r\n' \
  '            document.getElementById("status").innerHTML = "prêt";\r\n' \
  '          } else if (event.data == "prêt (lecture à partir du début)") {\r\n' \
  '            document.getElementById("status").innerHTML = "prêt (lecture à partir du début)";\r\n' \
  '          } else if (event.data == "en cours...") {\r\n' \
  '            document.getElementById("status").innerHTML = "en cours...";\r\n' \
  '          } else if (event.data == "Lecture") {\r\n' \
  '            document.getElementById("status").innerHTML = "lecture";\r\n' \
  '            document.getElementById("play-pause").innerHTML = "Pause";\r\n' \
  '          } else if (event.data == "Pause") {\r\n' \
  '            document.getElementById("status").innerHTML = "pause";\r\n' \
  '            document.getElementById("play-pause").innerHTML = "Lecture";\r\n' \
  '          } else if (event.data == "Arrêt") {\r\n' \
  '            document.getElementById("status").innerHTML = "arrêt";\r\n' \
  '            document.getElementById("play-pause").innerHTML = "Lecture";\r\n' \
  '          } else if (event.data.substring(0,8) == "Duration") {\r\n' \
  '            duration = parseInt(event.data.substring(9));\r\n' \
  '            let seekduration_d = new Date(duration*1000);\r\n' \
  '            document.getElementById("seekduration").innerHTML = seekduration_d.toISOString().substr(12, 7);\r\n' \
  '            if (document.getElementById("position").innerHTML !="-") {\r\n' \
  '              let cur_pos = document.getElementById("position").innerHTML.split(":");\r\n' \
  '              seekbar.value = Math.floor((parseInt(cur_pos[0])*3600 + parseInt(cur_pos[1])*60 + parseInt(cur_pos[2])) / duration * 10000);\r\n' \
  '              seekposition.innerHTML = document.getElementById("position").innerHTML;\r\n' \
  '            }\r\n' \
  '            seekbar.style.display = "inline-block";\r\n' \
  '            seektarget.style.display = "block";\r\n' \
  '          } else if (event.data != "close") {\r\n' \
  '            document.getElementById("position").innerHTML = event.data;\r\n' \
  '            if (duration != 0 && !seekongoing ) {\r\n' \
  '              let cur_pos = event.data.split(":");\r\n' \
  '              seekbar.value = Math.floor((parseInt(cur_pos[0])*3600 + parseInt(cur_pos[1])*60 + parseInt(cur_pos[2])) / duration * 10000);\r\n' \
  '              seekposition.innerHTML = event.data;\r\n' \
  '            }\r\n' \
  '          }\r\n' \
  '        }\r\n' \
  '        socket.onclose = function(event) {\r\n' \
  '          new_socket();\r\n' \
  '        }\r\n' \
  '        window.onbeforeunload = function () {\r\n' \
  '          socket.onclose = function(event) {};\r\n' \
  '          socket.close();\r\n' \
  '        }\r\n' \
  '      }\r\n' \
  '      duration = 0;\r\n' \
  '      seekongoing = false;\r\n' \
  '      function play_pause_button() {\r\n' \
  '        if (document.getElementById("status").innerHTML != "initialisation") {\r\n' \
  '          if (document.getElementById("status").innerHTML == "arrêt" && duration != 0) {socket.send("Seek:" + seekposition.innerHTML);}\r\n' \
  '          socket.send(document.getElementById(\'play-pause\').innerHTML);\r\n' \
  '        }\r\n' \
  '      }\r\n' \
  '      function stop_button() {\r\n' \
  '        conf = window.confirm("Arrêter la lecture ?");\r\n' \
  '        if (conf) {socket.send(\'Arrêt\');}\r\n' \
  '      }\r\n' \
  '    </script>\r\n' \
  '  </head>\r\n' \
  '  <body style="background-color:rgb(40,45,50);color:rgb(225,225,225);font-size:32px;">\r\n' \
  '    <h1 style="line-height:20px;font-size:180%;">PlayOn&nbsp;&nbsp;&nbsp;&nbsp;Interface de contrôle<br></h1>\r\n' \
  '    <img id="renderer_icon" src="data:;base64,##RENDERERICON##" alt=" " style="height:36px;width:auto;vertical-align:middle;">\r\n' \
  '    <span id="renderer_name" style="font-size:130%;">&nbsp;&nbsp;##RENDERERNAME##</span>\r\n' \
  '    <br style="line-height:100px;">\r\n' \
  '    <p style="margin-bottom:0px;">URL du média : </p>\r\n' \
  '    <p id="media_src" style="margin-left:30px;margin-top:10px;font-size:50%;word-wrap:break-word;height:110px;width:90%;overflow-y:auto;">##URL##</p>\r\n' \
  '    <p style="line-height:60px;">Statut :&nbsp;&nbsp;&nbsp;<span id="status" style="color:rgb(200,250,240);">initialisation</span></p>\r\n' \
  '    <p style="line-height:60px;">Position de lecture :&nbsp;&nbsp;&nbsp;<span id="position" style="color:rgb(200,250,240);">-</span></p>\r\n' \
  '    <br>\r\n' \
  '    <button id="play-pause" style="background-color:rgb(200,250,240);border:none;padding-top:20px;padding-bottom:20px;margin-left:50px;margin-right:200px;width:200px;font-size:100%;font-weight:bold;cursor:pointer;" onclick="play_pause_button()">Lecture</button>\r\n' \
  '    <button id="stop" style="background-color:rgb(250,220,200);border:none;padding-top:20px;padding-bottom:20px;margin-left:200px;margin-right:50px;width:200px;font-size:100%;font-weight:bold;cursor:pointer;" onclick="stop_button()">Arrêt</button>\r\n' \
  '    <br>\r\n' \
  '    <br>\r\n' \
  '    <input type="range" min="0" max="10000" value="0" id="seekbar" style="margin-left:50px;margin-right:50px;width:80%;cursor:pointer;display:none;">\r\n' \
  '    <p id="seektarget" style="margin-left:50px;font-size:75%;display:none;"> Position cible: <span id="seekposition">0:00:00</span> / <span id="seekduration">0:00:00</span></p>\r\n' \
  '    <script>\r\n' \
  '      new_socket();\r\n' \
  '      seekbar = document.getElementById("seekbar");\r\n' \
  '      seekposition = document.getElementById("seekposition");\r\n' \
  '      seekbar.onmousedown = function() {seekongoing = true;};\r\n' \
  '      seekbar.onmouseup = function() {seekongoing = false;};\r\n' \
  '      seekbar.ontouchstart = function() {seekongoing = true;};\r\n' \
  '      seekbar.ontouchend = function() {seekongoing = false;};\r\n' \
  '      seekbar.oninput = function() {\r\n' \
  '        let seekposition_d = new Date(seekbar.value*duration/10);\r\n' \
  '        seekposition.innerHTML = seekposition_d.toISOString().substr(12, 7);\r\n' \
  '      };\r\n' \
  '      seekbar.onchange = function() {\r\n' \
  '        if (document.getElementById("status").innerHTML != "initialisation") {socket.send("Seek:" + seekposition.innerHTML);}\r\n' \
  '        seekbar.blur();\r\n' \
  '      };\r\n' \
  '    </script>\r\n' \
  '  </body>\r\n' \
  '</html>'

  def __init__(self, DLNAWebInterfaceServerAddress=None, Launch=INTERFACE_NOT_RUNNING, Renderer_uuid=None, Renderer_name=None, MediaServerMode=None, MediaSrc='', MediaStartFrom='0:00:00', MediaBufferSize=75, MediaBufferAhead=25, MediaMuxContainer=None, MediaSubSrc='', MediaSubLang=None, verbosity=0):
    threading.Thread.__init__(self)
    self.verbosity = verbosity
    self.logger = log_event(verbosity)
    self.DLNARendererControlerInstance = DLNARendererControler(verbosity)
    self.RenderersEvent = None
    if not DLNAWebInterfaceServerAddress:
      self.DLNAWebInterfaceServerAddress = (self.DLNARendererControlerInstance.ip, 8000)
    else:
      try:
        self.DLNAWebInterfaceServerAddress = (self.DLNARendererControlerInstance.ip if not DLNAWebInterfaceServerAddress[0] else DLNAWebInterfaceServerAddress[0], 8000 if not DLNAWebInterfaceServerAddress[1] else DLNAWebInterfaceServerAddress[1])
      except:
        self.DLNAWebInterfaceServerAddress = (self.DLNARendererControlerInstance.ip, 8000)
    self.ControlDataStore = DLNAWebInterfaceControlDataStore()
    self.RenderersDataStore = DLNAWebInterfaceRenderersDataStore()
    self.WebSocketServerControlInstance = None
    self.WebSocketServerRenderersInstance = None
    self.html_control = b''
    self.html_start = b''
    self.html_ready = False
    self.Renderer_uuid = Renderer_uuid
    self.Renderer_name = Renderer_name
    self.Renderer = None
    self.MediaServerInstance = None
    self.MediaSrc = MediaSrc
    if MediaStartFrom:
      try:
        self.MediaPosition = _seconds_to_position(_position_to_seconds(MediaStartFrom))
      except:
        self.MediaPosition = '0:00:00'
    else:
      self.MediaPosition = '0:00:00'
    self.MediaBufferSize = MediaBufferSize
    self.MediaBufferAhead = MediaBufferAhead
    self.MediaMuxContainer = MediaMuxContainer
    self.MediaSubSrc = MediaSubSrc
    self.MediaSubLang = MediaSubLang
    self.TargetStatus = Launch
    self.MediaServerMode = MediaServerMode
    if self.MediaServerMode == MediaProvider.SERVER_MODE_SEQUENTIAL and not MediaMuxContainer:
      self.MediaPosition = '0:00:00'
    self.Status = None
    self.shutdown_requested = False
    if not mimetypes.inited:
      mimetypes.init()

  def manage_start(self):
    if self.shutdown_requested:
      return
    self.RenderersDataStore.reinit()
    if self.Status == DLNAWebInterfaceServer.INTERFACE_DISPLAY_RENDERERS:
      self.logger.log('Démarrage du gestionnaire d\'affichage de renderer pour serveur d\'interface Web', 2)
      self.html_start = DLNAWebInterfaceServer.HTML_START_TEMPLATE.replace('##CONTROL-URL##', 'http://%s:%s/control.html' % self.DLNAWebInterfaceServerAddress).replace('##DISPLAY##', 'none').encode('utf-8')
    elif self.Status == DLNAWebInterfaceServer.INTERFACE_START:
      self.logger.log('Démarrage du gestionnaire d\'affichage de renderer dans le formulaire de lancement pour serveur d\'interface Web', 2)
      self.html_start = DLNAWebInterfaceServer.HTML_START_TEMPLATE.replace('##CONTROL-URL##', 'http://%s:%s/control.html' % self.DLNAWebInterfaceServerAddress).replace('##DISPLAY##', 'inline-block').replace('##URL##', html.escape(self.MediaSrc) + ('\r\n' + html.escape(self.MediaSubSrc) if self.MediaSubSrc else '')).replace('##STARTFROM##', self.MediaPosition).encode('utf-8')
    else:
      return
    self.DLNARendererControlerInstance.start_discovery_polling(timeout=3, alive_persistence=86400, polling_period=30, DiscoveryEvent = self.RenderersEvent)
    self.WebSocketServerRenderersInstance = WebSocketServer((self.DLNAWebInterfaceServerAddress[0], self.DLNAWebInterfaceServerAddress[1]+2), self.RenderersDataStore, self.verbosity)
    self.WebSocketServerRenderersInstance.start()
    self.html_ready = True
    rend_stat = []
    first_loop = True
    while self.TargetStatus in (DLNAWebInterfaceServer.INTERFACE_DISPLAY_RENDERERS, DLNAWebInterfaceServer.INTERFACE_START) and not self.shutdown_requested:
      if (first_loop or self.DLNARendererControlerInstance.wait_for_advertisement(1)) and not self.shutdown_requested:
        first_loop = False
        for ind in range(len(self.DLNARendererControlerInstance.Renderers)):
          renderer = self.DLNARendererControlerInstance.Renderers[ind]
          if ind == len(rend_stat):
            rend_stat.append(None)
            self.RenderersDataStore.Message = urllib.parse.urlencode({'command': 'add', 'index': str(ind), 'name': renderer.FriendlyName, 'ip': (urllib.parse.urlparse(renderer.BaseURL)).netloc.split(':',1)[0], 'icon': renderer.IconURL, 'status': renderer.StatusAlive}, quote_via=urllib.parse.quote)
            if self.Renderer_uuid or self.Renderer_name:
              if renderer == self.DLNARendererControlerInstance.search(self.Renderer_uuid, self.Renderer_name):
                self.RenderersDataStore.Message = urllib.parse.urlencode({'command': 'sel', 'index': str(ind)}, quote_via=urllib.parse.quote)
          if renderer.StatusAlive != rend_stat[ind]:
            rend_stat[ind] = renderer.StatusAlive
            if renderer.StatusAlive:
              self.RenderersDataStore.Message = urllib.parse.urlencode({'command': 'show', 'index': str(ind)}, quote_via=urllib.parse.quote)
            else:
              self.RenderersDataStore.Message = urllib.parse.urlencode({'command': 'hide', 'index': str(ind)}, quote_via=urllib.parse.quote)
    self.html_ready = False
    self.DLNARendererControlerInstance.stop_discovery_polling()
    self.logger.log('Arrêt du gestionnaire d\'affichage de renderer pour serveur d\'interface Web', 2)
    if self.Status == DLNAWebInterfaceServer.INTERFACE_START and not self.shutdown_requested:
      self.RenderersDataStore.Redirect = True
    self.WebSocketServerRenderersInstance.shutdown()

  def manage_control(self):
    if self.shutdown_requested or self.Status != DLNAWebInterfaceServer.INTERFACE_CONTROL:
      return
    self.ControlDataStore.reinit()
    self.ControlDataStore.Status = 'initialisation'
    self.ControlDataStore.Position = '0:00:00'
    self.logger.log('Démarrage du gestionnaire de contrôleur de lecture pour serveur d\'interface Web', 2)
    if not self.Renderer :
      nb_search = 0
      renderer = None
      while self.Status == DLNAWebInterfaceServer.INTERFACE_CONTROL and not renderer and nb_search < 3:
        self.DLNARendererControlerInstance.discover(timeout=2*nb_search+2)
        renderer = self.DLNARendererControlerInstance.search(uuid=self.Renderer_uuid, name=self.Renderer_name)
        nb_search +=1
      self.Renderer = renderer
      if renderer:
        self.Renderer_uuid = renderer.UDN[5:]
        self.Renderer_name = renderer.FriendlyName
    else:
      renderer = self.Renderer
    if self.shutdown_requested or not renderer:
      self.logger.log('Interruption du gestionnaire de contrôleur de lecture pour serveur d\'interface Web', 2)
      return
    renderer_icon = b''
    if renderer.IconURL:
      try:
        icon_resp = urllib.request.urlopen(renderer.IconURL, timeout=5)
        renderer_icon = icon_resp.read()
        icon_resp.close()
        if renderer_icon:
          renderer_icon = base64.b64encode(renderer_icon)
      except:
        pass
    self.html_control = DLNAWebInterfaceServer.HTML_CONTROL_TEMPLATE.replace('##START-URL##', 'http://%s:%s/start.html' % self.DLNAWebInterfaceServerAddress).replace('##URL##', html.escape(self.MediaSrc) + ('<br>' + html.escape(self.MediaSubSrc) if self.MediaSubSrc else '')).replace('##RENDERERNAME##', html.escape(renderer.FriendlyName)).encode('utf-8').replace(b'##RENDERERICON##', renderer_icon)
    self.WebSocketServerControlInstance = WebSocketServer((self.DLNAWebInterfaceServerAddress[0], self.DLNAWebInterfaceServerAddress[1]+1), self.ControlDataStore, self.verbosity)
    self.WebSocketServerControlInstance.start()
    self.html_ready = True
    event_listener = self.DLNARendererControlerInstance.new_event_subscription(renderer, 'AVTransport', self.DLNAWebInterfaceServerAddress[1]+3)
    prep_success = True
    if not event_listener:
      prep_success = False
    if prep_success:
      warning = self.DLNARendererControlerInstance.add_event_warning(event_listener, 'TransportState', 'PLAYING', 'STOPPED', 'PAUSED_PLAYBACK', WarningEvent=self.ControlDataStore.IncomingEvent)
      for nb_try in range(3):
        prep_success = self.DLNARendererControlerInstance.send_event_subscription(event_listener, 36000)
        if prep_success:
          break
    if prep_success:
      media_kind = 'video'
      media_mime = mimetypes.guess_type(self.MediaSrc)[0]
      if media_mime:
        if media_mime[0:5] in ('audio', 'image'):
          media_kind = media_mime[0:5]
      self.MediaServerInstance = None
      if self.MediaServerMode != DLNAWebInterfaceServer.SERVER_MODE_NONE:
        self.MediaServerInstance = MediaServer(self.MediaServerMode, (self.DLNAWebInterfaceServerAddress[0], self.DLNAWebInterfaceServerAddress[1]+5), self.MediaSrc, MediaStartFrom=self.MediaPosition, MediaBufferSize=self.MediaBufferSize, MediaBufferAhead=self.MediaBufferAhead, MediaMuxContainer=self.MediaMuxContainer, MediaSubSrc=self.MediaSubSrc, MediaSubLang=self.MediaSubLang, MediaProcessProfile=renderer.FriendlyName, verbosity=self.verbosity, auth_ip=(urllib.parse.urlparse(renderer.BaseURL)).netloc.split(':',1)[0])
        self.MediaServerInstance.start()
        incoming_event = self.ControlDataStore.IncomingEvent
        if not self.shutdown_requested:
          self.ControlDataStore.IncomingEvent = self.MediaServerInstance.BuildFinishedEvent
          self.MediaServerInstance.BuildFinishedEvent.wait()
          self.ControlDataStore.IncomingEvent = incoming_event
          prep_success = (self.MediaServerInstance.is_running == True) and self.MediaServerInstance.MediaProviderInstance.Status in (MediaProvider.STATUS_RUNNING, MediaProvider.STATUS_COMPLETED)
        else:
          prep_success = False
        if prep_success and not self.shutdown_requested:
          suburi = None
          if self.MediaServerInstance.MediaProviderInstance.MediaSubBuffer:
            if self.MediaServerInstance.MediaProviderInstance.MediaSubBuffer[0]:
              suburi = 'http://%s:%s/mediasub%s' % (self.DLNAWebInterfaceServerAddress[0], self.DLNAWebInterfaceServerAddress[1]+5, self.MediaServerInstance.MediaProviderInstance.MediaSubBuffer[1])
          server_mode = self.MediaServerInstance.MediaProviderInstance.ServerMode
          if server_mode == MediaProvider.SERVER_MODE_RANDOM:
            warning_d = self.DLNARendererControlerInstance.add_event_warning(event_listener, 'CurrentMediaDuration')
            accept_ranges = self.MediaServerInstance.MediaProviderInstance.AcceptRanges
            if accept_ranges:
              prep_success = self.DLNARendererControlerInstance.send_Local_URI(self.Renderer, 'http://%s:%s/media%s' % (self.DLNAWebInterfaceServerAddress[0], self.DLNAWebInterfaceServerAddress[1]+5, self.MediaServerInstance.MediaProviderInstance.MediaFeedExt), self.MediaServerInstance.MediaProviderInstance.MediaTitle, kind=media_kind, suburi=suburi)
            else:
              prep_success = self.DLNARendererControlerInstance.send_URI(self.Renderer, 'http://%s:%s/media%s' % (self.DLNAWebInterfaceServerAddress[0], self.DLNAWebInterfaceServerAddress[1]+5, self.MediaServerInstance.MediaProviderInstance.MediaFeedExt), self.MediaServerInstance.MediaProviderInstance.MediaTitle, kind=media_kind, suburi=suburi)
          elif server_mode == MediaProvider.SERVER_MODE_SEQUENTIAL:
            accept_ranges = False
            prep_success = self.DLNARendererControlerInstance.send_URI(self.Renderer, 'http://%s:%s/media%s' % (self.DLNAWebInterfaceServerAddress[0], self.DLNAWebInterfaceServerAddress[1]+5, self.MediaServerInstance.MediaProviderInstance.MediaFeedExt), self.MediaServerInstance.MediaProviderInstance.MediaTitle, kind=media_kind, suburi=suburi)
          else:
            prep_success = False
      else:
        suburi = None
        server_mode = DLNAWebInterfaceServer.SERVER_MODE_NONE
        warning_d = self.DLNARendererControlerInstance.add_event_warning(event_listener, 'CurrentMediaDuration')
        accept_ranges = True
        media_ip = None
        try:
          media_ip = urllib.parse.urlparse(self.MediaSrc).netloc.split(':',1)[0]
        except:
          pass
        if self.DLNAWebInterfaceServerAddress[0] == media_ip:
          prep_success = self.DLNARendererControlerInstance.send_Local_URI(self.Renderer, self.MediaSrc, 'Média', kind=media_kind, suburi=suburi)
        else:
          prep_success = self.DLNARendererControlerInstance.send_URI(self.Renderer, self.MediaSrc, self.MediaSrc, kind=media_kind, suburi=suburi)
    if not prep_success or self.ControlDataStore.Command == 'Arrêt':
      self.logger.log('Interruption du gestionnaire de contrôleur de lecture pour serveur d\'interface Web', 2)
      if self.MediaServerInstance:
        try:
          self.MediaServerInstance.shutdown()
          self.MediaServerInstance = None
        except:
          pass
      self.html_ready = False
      if not self.shutdown_requested:
        self.ControlDataStore.Redirect = True
      self.WebSocketServerControlInstance.shutdown()
      if event_listener:
        self.DLNARendererControlerInstance.send_event_unsubscription(event_listener)
      return
    status_dict = {'PLAYING': 'Lecture', 'PAUSED_PLAYBACK': 'Pause', 'STOPPED': 'Arrêt'}
    old_value = None
    new_value = None
    is_paused = True
    new_duration = None
    transport_status = ''
    stop_reason = ''
    renderer_position = '0:00:00'
    max_renderer_position = '0:00:00'
    if server_mode != DLNAWebInterfaceServer.SERVER_MODE_NONE:
      renderer_stopped_position = self.MediaServerInstance.MediaProviderInstance.MediaStartFrom
    else:
      renderer_stopped_position = self.MediaPosition
    if not renderer_stopped_position or renderer_stopped_position == '0:00:00':
      renderer_stopped_position = None
    self.ControlDataStore.Position = self.MediaPosition
    if server_mode == MediaProvider.SERVER_MODE_RANDOM:
      if accept_ranges:
        self.ControlDataStore.Status = 'prêt'
      else:
        self.ControlDataStore.Status = 'prêt (lecture à partir du début)'
    elif server_mode == MediaProvider.SERVER_MODE_SEQUENTIAL:
      if self.MediaServerInstance.MediaProviderInstance.MediaMuxContainer:
        self.ControlDataStore.Status = 'prêt'
      else:
        self.ControlDataStore.Status = 'prêt (lecture à partir du début)'
    else:
      self.ControlDataStore.Status = 'prêt'
    wi_cmd = None
    if server_mode in (MediaProvider.SERVER_MODE_RANDOM, DLNAWebInterfaceServer.SERVER_MODE_NONE):
      self.DLNARendererControlerInstance.wait_for_warning(warning_d, 0, True)
    while not self.shutdown_requested and new_value != 'STOPPED':
      new_value = self.DLNARendererControlerInstance.wait_for_warning(warning, 10 if is_paused else 1)
      if server_mode in (MediaProvider.SERVER_MODE_RANDOM, DLNAWebInterfaceServer.SERVER_MODE_NONE):
        if old_value:
          new_duration = self.DLNARendererControlerInstance.wait_for_warning(warning_d, 0)
          if new_duration:
            if _position_to_seconds(new_duration):
              self.ControlDataStore.Duration = "Duration:%d" % _position_to_seconds(new_duration)
      renderer_new_position = self.DLNARendererControlerInstance.get_Position(renderer)
      if renderer_new_position:
        if server_mode in (MediaProvider.SERVER_MODE_RANDOM, DLNAWebInterfaceServer.SERVER_MODE_NONE) and _position_to_seconds(renderer_new_position) == 0 and _position_to_seconds(renderer_position) != 0:
          if not renderer_stopped_position:
            try:
              transport_status = self.DLNARendererControlerInstance.get_TransportInfo(renderer)[0]
            except:
              transport_status = ''
            if not transport_status:
              transport_status = ''
            if transport_status.upper() in ('PAUSED_PLAYBACK', 'PLAYING'):
              renderer_position = renderer_new_position
        else:
          renderer_position = renderer_new_position
        if _position_to_seconds(renderer_position) > _position_to_seconds(max_renderer_position):
          max_renderer_position = renderer_position
      if not old_value and new_value == 'STOPPED':
        new_value = None
      if new_value and new_value != old_value:
        if new_value != 'STOPPED' and server_mode in (MediaProvider.SERVER_MODE_RANDOM, DLNAWebInterfaceServer.SERVER_MODE_NONE):
          if renderer_stopped_position:
            if accept_ranges:
              try:
                self.DLNARendererControlerInstance.send_Seek(renderer, renderer_stopped_position)
              except:
                pass
            renderer_stopped_position = None
          if not old_value:
            self.MediaPosition = '0:00:00'
            if accept_ranges:
              try:
                duration = self.DLNARendererControlerInstance.get_Duration(self.Renderer)
                if duration:
                  if _position_to_seconds(duration):
                    self.ControlDataStore.Duration = "Duration:%d" % _position_to_seconds(duration)
              except:
                pass
        if new_value != 'STOPPED' and not old_value and server_mode == MediaProvider.SERVER_MODE_SEQUENTIAL:
          if not self.MediaServerInstance.MediaProviderInstance.MediaMuxContainer:
            self.MediaPosition = '0:00:00'
        if new_value == 'PLAYING':
          is_paused = False
        elif new_value == 'PAUSED_PLAYBACK':
          is_paused = True
        self.ControlDataStore.Status = status_dict[new_value.upper()]
        old_value = new_value
      if new_value != 'STOPPED' or server_mode in (MediaProvider.SERVER_MODE_RANDOM, DLNAWebInterfaceServer.SERVER_MODE_NONE):
        if server_mode == MediaProvider.SERVER_MODE_SEQUENTIAL or not renderer_stopped_position:
          self.ControlDataStore.Position = _seconds_to_position(_position_to_seconds(self.MediaPosition) + _position_to_seconds(renderer_position))
        if new_value == 'STOPPED' and server_mode in (MediaProvider.SERVER_MODE_RANDOM, DLNAWebInterfaceServer.SERVER_MODE_NONE):
          if accept_ranges:
            new_value = None
            if not renderer_stopped_position:
              is_paused = True
              renderer_stopped_position = renderer_position
              try:
                self.DLNARendererControlerInstance.send_Seek(renderer, '0:00:00')
              except:
                pass
        if not wi_cmd:
          wi_cmd = self.ControlDataStore.Command
        if wi_cmd == 'Lecture':
          try:
            if server_mode == MediaProvider.SERVER_MODE_RANDOM:
              if self.MediaServerInstance.MediaProviderInstance.Status == MediaProvider.STATUS_ABORTED:
                try:
                  self.MediaServerInstance.shutdown()
                except:
                  pass
                try:
                  media_feed = self.MediaServerInstance.MediaProviderInstance.MediaFeed
                  media_type = self.MediaServerInstance.MediaProviderInstance.MediaSrcType.replace('WebPageURL', 'ContentURL')
                  media_sub = self.MediaServerInstance.MediaSubBufferInstance
                  self.MediaServerInstance = MediaServer(MediaProvider.SERVER_MODE_RANDOM, (self.DLNAWebInterfaceServerAddress[0], self.DLNAWebInterfaceServerAddress[1]+5), media_feed, MediaSrcType=media_type, MediaStartFrom='', MediaBufferSize=self.MediaBufferSize, MediaBufferAhead=self.MediaBufferAhead, MediaSubBuffer=media_sub, verbosity=self.verbosity, auth_ip=(urllib.parse.urlparse(renderer.BaseURL)).netloc.split(':',1)[0])
                  self.MediaServerInstance.start()
                  incoming_event = self.ControlDataStore.IncomingEvent
                  if not self.shutdown_requested:
                    self.ControlDataStore.IncomingEvent = self.MediaServerInstance.BuildFinishedEvent
                    self.MediaServerInstance.BuildFinishedEvent.wait()
                    self.ControlDataStore.IncomingEvent = incoming_event
                except:
                  pass
            if self.ControlDataStore.Status in ('prêt', 'Arrêt'):
              self.ControlDataStore.Status = 'en cours...'
              self.DLNARendererControlerInstance.send_Play(renderer)
            else:
              self.DLNARendererControlerInstance.send_Resume(renderer)
          except:
            pass
        elif wi_cmd == 'Pause':
          try:
            self.DLNARendererControlerInstance.send_Pause(renderer)
          except:
            pass
        elif wi_cmd == 'Arrêt':
          self.ControlDataStore.Status = 'en cours...'
          try:
            transport_status = self.DLNARendererControlerInstance.get_TransportInfo(renderer)[0]
          except:
            transport_status = ''
          if not transport_status:
            transport_status = ''
          try:
            if transport_status.upper() in ('PAUSED_PLAYBACK', 'PLAYING', 'TRANSITIONING'):
              old_value = 'STOPPED'
              self.DLNARendererControlerInstance.send_Stop(renderer)
              self.ControlDataStore.Status = 'Arrêt'
            else:
              new_value = 'STOPPED'
          except:
            pass
        elif server_mode in (MediaProvider.SERVER_MODE_RANDOM, DLNAWebInterfaceServer.SERVER_MODE_NONE) and wi_cmd:
          if accept_ranges and wi_cmd[0:4] == 'Seek':
            if not renderer_stopped_position:
              try:
                self.DLNARendererControlerInstance.send_Seek(renderer, wi_cmd[5:])
              except:
                pass
            else:
              renderer_stopped_position = wi_cmd[5:]
        wi_cmd = self.ControlDataStore.Command
        if wi_cmd:
          self.ControlDataStore.IncomingEvent.set()
    transport_status = ""
    stop_reason = ""
    if not self.shutdown_requested:
      try:
        transport_status = self.DLNARendererControlerInstance.get_TransportInfo(renderer)[1]
        stop_reason = self.DLNARendererControlerInstance.get_StoppedReason(renderer)[0]
      except:
        pass
    try:
      self.DLNARendererControlerInstance.send_Stop(renderer)
    except:
      pass
    if server_mode == MediaProvider.SERVER_MODE_SEQUENTIAL:
      renderer_position = max_renderer_position
    self.MediaPosition = _seconds_to_position(max(0, _position_to_seconds(self.MediaPosition) + _position_to_seconds(renderer_position) - 5))
    self.ControlDataStore.Position = self.MediaPosition
    if self.MediaServerInstance:
      try:
        self.MediaServerInstance.shutdown()
        self.MediaServerInstance = None
      except:
        pass
    self.html_ready = False
    self.DLNARendererControlerInstance.send_event_unsubscription(event_listener)
    self.logger.log('Arrêt du gestionnaire de contrôleur de lecture pour serveur d\'interface Web%s%s%s%s' % (' - statut ' if transport_status or stop_reason else '', transport_status, ':' if transport_status and stop_reason else '', stop_reason), 2)
    if not self.shutdown_requested:
      self.ControlDataStore.Redirect = True
    self.WebSocketServerControlInstance.shutdown()

  def _start_webserver(self):
    with ThreadedDualStackServer(self.DLNAWebInterfaceServerAddress, DLNAWebInterfaceRequestHandler, verbosity=self.verbosity) as self.DLNAWebInterfaceServerInstance:
      self.logger.log('Démarrage du serveur d\'interface Web', 0)
      self.DLNAWebInterfaceServerInstance.Interface = self
      self.DLNAWebInterfaceServerInstance.post_lock = threading.Lock()
      self.DLNAWebInterfaceServerInstance.serve_forever()

  def run(self):
    if self.Status != None:
      self.logger.log('Serveur d\'interface Web déjà en place', 1)
      return
    webserver_thread = threading.Thread(target=self._start_webserver)
    webserver_thread.start()
    if self.TargetStatus in (DLNAWebInterfaceServer.INTERFACE_DISPLAY_RENDERERS, DLNAWebInterfaceServer.INTERFACE_START, DLNAWebInterfaceServer.INTERFACE_CONTROL):
      self.RenderersEvent = self.DLNARendererControlerInstance.start_advertisement_listening()
    while (self.Status == None or self.TargetStatus==DLNAWebInterfaceServer.INTERFACE_START) and not self.shutdown_requested:
      if self.TargetStatus == DLNAWebInterfaceServer.INTERFACE_DISPLAY_RENDERERS:
        self.Status = DLNAWebInterfaceServer.INTERFACE_DISPLAY_RENDERERS
        self.manage_start()
      elif self.TargetStatus == DLNAWebInterfaceServer.INTERFACE_START:
        self.Status = DLNAWebInterfaceServer.INTERFACE_START
        self.manage_start()
        self.TargetStatus = DLNAWebInterfaceServer.INTERFACE_CONTROL
      if self.TargetStatus == DLNAWebInterfaceServer.INTERFACE_CONTROL and not self.shutdown_requested:
        self.Status = DLNAWebInterfaceServer.INTERFACE_CONTROL
        self.manage_control()
        self.TargetStatus = DLNAWebInterfaceServer.INTERFACE_START
      if self.shutdown_requested:
        self.TargetStatus = DLNAWebInterfaceServer.INTERFACE_NOT_RUNNING
        self.Status = DLNAWebInterfaceServer.INTERFACE_NOT_RUNNING
    if self.RenderersEvent:
      self.DLNARendererControlerInstance.stop_advertisement_listening()
      self.RenderersEvent = None
    self.TargetStatus = DLNAWebInterfaceServer.INTERFACE_NOT_RUNNING
    self.Status = DLNAWebInterfaceServer.INTERFACE_NOT_RUNNING

  def shutdown(self):
    if not self.shutdown_requested:
      self.logger.log('Fermeture du serveur d\'interface Web', 0)
      self.shutdown_requested = True
      if self.Status == DLNAWebInterfaceServer.INTERFACE_CONTROL:
        self.ControlDataStore.IncomingEvent.set()
        if self.MediaServerInstance:
          try:
            self.MediaServerInstance.shutdown()
          except:
            pass
      self.TargetStatus = DLNAWebInterfaceServer.INTERFACE_NOT_RUNNING
      self.Status = DLNAWebInterfaceServer.INTERFACE_NOT_RUNNING
      self.DLNAWebInterfaceServerInstance.shutdown()
      for sock in self.DLNAWebInterfaceServerInstance.conn_sockets:
        try:
          sock.shutdown(socket.SHUT_RDWR)
        except:
          pass


if __name__ == '__main__':
  
  formatter = lambda prog: argparse.HelpFormatter(prog, max_help_position=50, width=119)
  CustomArgumentParser = partial(argparse.ArgumentParser, formatter_class=formatter)
  parser = CustomArgumentParser()
  subparsers = parser.add_subparsers(dest='command', parser_class=CustomArgumentParser)
  
  common_parser = CustomArgumentParser(add_help=False)
  common_parser.add_argument('--ip', '-i', metavar='SERVER_IP_ADDRESS', help='adresse IP du serveur [adresse sur le réseau par défaut]', default='')
  common_parser.add_argument('--port', '-p', metavar='SERVER_TCP_PORT', help='port TCP du serveur [8000 par défaut]', default=8000, type=int)
  
  server_parser = CustomArgumentParser(add_help=False)
  server_parser.add_argument('--typeserver', '-t', metavar='TYPE_SERVER', help='type de serveur (a:auto, s:séquentiel, r:aléatoire, n:aucun) [a par défaut]', choices=['a', 's', 'r', 'n'], default='a')
  server_parser.add_argument('--buffersize', '-b', metavar='BUFFER_SIZE', help='taille du tampon en blocs de 1 Mo [75 par défaut]', default=75, type=int)
  server_parser.add_argument('--bufferahead', '-a', metavar='BUFFER_AHEAD', help='taille du sous-tampon de chargement par anticipation en blocs de 1 Mo [25 par défaut]', default=25, type=int)
  server_parser.add_argument('--muxcontainer', '-m', metavar='MUX_CONTAINER', help='type de conteneur de remuxage précédé de ! pour qu\'il soit systématique [MP4 par défaut]', choices=['MP4', 'MPEGTS', '!MP4', '!MPEGTS'], default='MP4', type=str.upper)
  
  subparser_display_renderers = subparsers.add_parser('display_renderers', aliases=['r'], parents=[common_parser], help='Affiche les renderers présents sur le réseau')
  subparser_display_renderers.add_argument('--verbosity', '-v', metavar='VERBOSE', help='niveau de verbosité de 0 à 2 [0 par défaut]', type=int, choices=[0, 1, 2], default=0)

  subparser_start = subparsers.add_parser('start', aliases=['s'], parents=[common_parser, server_parser], help='Démarre l\'interface à partir de la page de lancement')
  subparser_start.add_argument('--mediasrc', '-c', metavar='MEDIA_ADDRESS', help='adresse du contenu multimédia [aucune par défaut]', default='')
  subparser_start.add_argument('--mediasubsrc', '-s', metavar='MEDIA_SUBADDRESS', help='adresse du contenu de sous-titres [aucun par défaut]', default='')
  subparser_start.add_argument('--mediasublang', '-l', metavar='MEDIA_SUBLANG', help='langue de sous-titres, . pour pas de sélection [fr,fre,fra par défaut]', default='fr,fre,fra')
  subparser_start.add_argument('--mediastartfrom', '-f', metavar='MEDIA_START_FROM', help='position temporel de démarrage au format H:MM:SS [début par défaut]', default=None)
  subparser_start.add_argument('--verbosity', '-v', metavar='VERBOSE', help='niveau de verbosité de 0 à 2 [0 par défaut]', type=int, choices=[0, 1, 2], default=0)

  subparser_control = subparsers.add_parser('control', aliases=['c'], parents=[common_parser, server_parser], help='Démarre l\'interface à partir de la page de contrôle')
  subparser_control.add_argument('--uuid', '-u', metavar='RENDERER_UUID', help='uuid du renderer [premier renderer sans sélection sur l\'uuid par défaut]', default=None)
  subparser_control.add_argument('--name', '-n', metavar='RENDERER_NAME', help='nom du renderer [premier renderer sans sélection sur le nom par défaut]', default=None)
  subparser_control.add_argument('mediasrc', metavar='MEDIA_ADDRESS', help='adresse du contenu multimédia')
  subparser_control.add_argument('--mediasubsrc', '-s', metavar='MEDIA_SUBADDRESS', help='adresse du contenu de sous-titres [aucun par défaut]', default='')
  subparser_control.add_argument('--mediasublang', '-l', metavar='MEDIA_SUBLANG', help='langue de sous-titres, . pour pas de sélection [fr,fre,fra par défaut]', default='fr,fre,fra')
  subparser_control.add_argument('--mediastartfrom', '-f', metavar='MEDIA_START_FROM', help='position temporel de démarrage au format H:MM:SS [début par défaut]', default=None)
  subparser_control.add_argument('--verbosity', '-v', metavar='VERBOSE', help='niveau de verbosité de 0 à 2 [0 par défaut]', type=int, choices=[0, 1, 2], default=0)


  args = parser.parse_args()
  if not args.command:
    parser.print_help()
    exit()

  if args.command in ('display_renderers', 'r'):
    DLNAWebInterfaceServerInstance = DLNAWebInterfaceServer((args.ip, args.port), Launch=DLNAWebInterfaceServer.INTERFACE_DISPLAY_RENDERERS, verbosity=args.verbosity)
  elif args.command in ('start', 's'):
    DLNAWebInterfaceServerInstance = DLNAWebInterfaceServer((args.ip, args.port), Launch=DLNAWebInterfaceServer.INTERFACE_START, MediaServerMode={'a':MediaProvider.SERVER_MODE_AUTO, 's':MediaProvider.SERVER_MODE_SEQUENTIAL, 'r':MediaProvider.SERVER_MODE_RANDOM, 'n':DLNAWebInterfaceServer.SERVER_MODE_NONE}.get(args.typeserver,None) , MediaSrc=args.mediasrc, MediaStartFrom=args.mediastartfrom, MediaBufferSize=args.buffersize, MediaBufferAhead=args.bufferahead, MediaMuxContainer=args.muxcontainer, MediaSubSrc=args.mediasubsrc, MediaSubLang=args.mediasublang if args.mediasublang != '.' else '', verbosity=args.verbosity)
  elif args.command in ('control', 'c'):
    DLNAWebInterfaceServerInstance = DLNAWebInterfaceServer((args.ip, args.port), Launch=DLNAWebInterfaceServer.INTERFACE_CONTROL, Renderer_uuid=args.uuid, Renderer_name=args.name, MediaServerMode={'a':MediaProvider.SERVER_MODE_AUTO, 's':MediaProvider.SERVER_MODE_SEQUENTIAL, 'r':MediaProvider.SERVER_MODE_RANDOM, 'n':DLNAWebInterfaceServer.SERVER_MODE_NONE}.get(args.typeserver,None), MediaSrc=args.mediasrc, MediaStartFrom=args.mediastartfrom, MediaBufferSize=args.buffersize, MediaBufferAhead=args.bufferahead, MediaMuxContainer=args.muxcontainer, MediaSubSrc=args.mediasubsrc, MediaSubLang=args.mediasublang if args.mediasublang != '.' else '', verbosity=args.verbosity)

  DLNAWebInterfaceServerInstance.start()
  webbrowser.open('http://%s:%s/' % DLNAWebInterfaceServerInstance.DLNAWebInterfaceServerAddress)
  print('Appuyez sur "S" pour stopper')
  remux_list = ('MP4', 'MPEGTS', '!MP4', '!MPEGTS')
  server_modes = {MediaProvider.SERVER_MODE_AUTO: 'auto', MediaProvider.SERVER_MODE_SEQUENTIAL: 'séquentiel', MediaProvider.SERVER_MODE_RANDOM: 'aléatoire'}
  if DLNAWebInterfaceServerInstance.Status in (DLNAWebInterfaceServer.INTERFACE_START, DLNAWebInterfaceServer.INTERFACE_CONTROL):
    if args.typeserver != 'n':
      print('Appuyez sur "!" et "M" pour alterner entre les modes de remuxage (MP4, MPEGTS, !MP4, !MPEGTS) pour la prochaine session de lecture - mode actuel: %s' % args.muxcontainer)
      print('Appuyez sur "T" pour alterner entre les types de serveur (auto, séquentiel, aléatoire) pour la prochaine session de lecture - mode actuel: %s' % server_modes.get({'a':MediaProvider.SERVER_MODE_AUTO, 's':MediaProvider.SERVER_MODE_SEQUENTIAL, 'r':MediaProvider.SERVER_MODE_RANDOM}.get(args.typeserver,''),''))
  while DLNAWebInterfaceServerInstance.Status != DLNAWebInterfaceServer.INTERFACE_NOT_RUNNING:
    k = msvcrt.getch()
    if k == b'\xe0':
      k = msvcrt.getch()
      k = b''
    if k.upper() == b'S':
        break
    if DLNAWebInterfaceServerInstance.Status in (DLNAWebInterfaceServer.INTERFACE_START, DLNAWebInterfaceServer.INTERFACE_CONTROL) and args.typeserver != 'n':
      if k.upper() == b'M':
        DLNAWebInterfaceServerInstance.MediaMuxContainer = remux_list[(remux_list.index(DLNAWebInterfaceServerInstance.MediaMuxContainer)+1)%2+remux_list.index(DLNAWebInterfaceServerInstance.MediaMuxContainer)//2*2]
        print('Mode de remuxage pour la prochaine session de lecture: %s' % DLNAWebInterfaceServerInstance.MediaMuxContainer)
      elif k.upper() == b'!' :
        DLNAWebInterfaceServerInstance.MediaMuxContainer = remux_list[(remux_list.index(DLNAWebInterfaceServerInstance.MediaMuxContainer)+2)%4]
        print('Mode de remuxage pour la prochaine session de lecture: %s' % DLNAWebInterfaceServerInstance.MediaMuxContainer)
      elif k.upper() == b'T':
        DLNAWebInterfaceServerInstance.MediaServerMode = (DLNAWebInterfaceServerInstance.MediaServerMode + 1) % 3
        print('Type de serveur pour la prochaine session de lecture: %s' % server_modes.get(DLNAWebInterfaceServerInstance.MediaServerMode,None))
  DLNAWebInterfaceServerInstance.shutdown()