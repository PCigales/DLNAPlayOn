@set "youtube-dl_path="C:\Program Files\yt-dlp\yt-dlp.exe""

@echo off>nul
setlocal enabledelayedexpansion

set "youtube-dl_pref=best"
set "youtube-dl_vpref=bestvideo"
set "youtube-dl_apref=bestaudio"
if "%1" == "sub" (
if "!mediabuilder_lang!" == "" (set "youtube-dl_spref=--sub-format srt/ass/ssa/vtt/best") else (set "youtube-dl_spref=--sub-format srt/ass/ssa/vtt/best --sub-lang "!mediabuilder_lang!"")
)

if /I "!mediabuilder_profile!" == "[TV]Samsung LED40" (
set "youtube-dl_pref=best[vcodec*=?avc][width<=?1920][height<=?1080][fps<=?30][acodec*=?mp4]/best"
set "youtube-dl_vpref=bestvideo[vcodec*=?avc][width<=?1920][height<=?1080][fps<=?30]"
set "youtube-dl_apref=bestaudio[acodec*=?mp4]")

if /I "!mediabuilder_profile!" == "BubbleUPnP (SM-A530F)" (
set "youtube-dl_pref=best[vcodec*=?avc][width<=?1920][height<=?1080][acodec*=?mp4]/best"
set "youtube-dl_vpref=bestvideo[vcodec*=?avc][width<=?1920][height<=?1080]"
set "youtube-dl_apref=bestaudio[acodec*=?mp4]")

if not "!mediabuilder_url:://www.arte=!" == "!mediabuilder_url!" if not "%1" == "playlist" goto arte

if "%1" == "nomux" %youtube-dl_path% --no-playlist --youtube-skip-dash-manifest --encoding utf-8 -e --get-filename -o  ###PlayOn_Separator### -g -f "%youtube-dl_pref%" !mediabuilder_url!

if "%1" == "mux" %youtube-dl_path% --no-playlist --youtube-skip-dash-manifest --encoding utf-8 -e --get-filename -o  ###PlayOn_Separator### -g -f "%youtube-dl_vpref%+%youtube-dl_apref%/%youtube-dl_pref%" !mediabuilder_url!

if "%1" == "sub" %youtube-dl_path% --no-playlist --youtube-skip-dash-manifest --encoding utf-8 -j --write-sub %youtube-dl_spref% !mediabuilder_url!

if "%1" == "playlist" %youtube-dl_path% --flat-playlist --encoding utf-8 -j !mediabuilder_url!

goto end

:arte

if "%1" == "nomux" (
for /F "delims=/ tokens=3,5,6" %%a in ("!mediabuilder_url!") do (set "youtube-dl_lng=%%a" & set "youtube-dl_url=https://api.arte.tv/api/opa/v3/videoStreams?channel=FR&protocol=HTTPS&quality=SQ&kind=SHOW&limit=100&programId=%%b" & echo.%%c)
if /I "!youtube-dl_lng!"=="de" (set youtube-dl_lng=A) else set youtube-dl_lng=F
set youtube-dl_urlvl=""
set youtube-dl_urlvo=""
for /F "skip=15 tokens=1,* delims=: " %%a in ('curl -s -H "Authorization:Bearer Nzc1Yjc1ZjJkYjk1NWFhN2I2MWEwMmRlMzAzNjI5NmU3NWU3ODg4ODJjOWMxNTMxYzEzZGRjYjg2ZGE4MmIwOA" --ssl-no-revoke "!youtube-dl_url!"') do (
if "%%a"==""videoStreams"" (
set youtube-dl_url=""
set youtube-dl_asl=""
) else if "%%a"==""url"" (
set "youtube-dl_url=%%b"
if !youtube-dl_asl!=="V!youtube-dl_lng!" (set "youtube-dl_urlvl=!youtube-dl_url!") else if !youtube-dl_asl!=="VST!youtube-dl_lng!" (set "youtube-dl_urlvo=!youtube-dl_url!")
) else if "%%a"==""audioShortLabel"" (
set "youtube-dl_asl=%%b"
set "youtube-dl_asl=!youtube-dl_asl:,=!"
set "youtube-dl_asl=!youtube-dl_asl:O=!"
if !youtube-dl_asl!=="V!youtube-dl_lng!" (set "youtube-dl_urlvl=!youtube-dl_url!") else if !youtube-dl_asl!=="VST!youtube-dl_lng!" (set "youtube-dl_urlvo=!youtube-dl_url!")
)
)
if !youtube-dl_urlvl!=="" (set youtube-dl_url=!youtube-dl_urlvo:\/=/!) else set youtube-dl_url=!youtube-dl_urlvl:\/=/!
set youtube-dl_url=!youtube-dl_url:~1,-2!
echo.!youtube-dl_url!
echo ###PlayOn_Separator###
)

if "%1" == "mux" for /F "delims=" %%a in ('@!youtube-dl_path! --no-playlist --youtube-skip-dash-manifest --encoding utf-8 -e --get-filename -o  ###PlayOn_Separator### -g -f "%youtube-dl_vpref%+%youtube-dl_apref%/%youtube-dl_pref%" !mediabuilder_url!') do (set "youtube-dl_url=%%a" & echo !youtube-dl_url:.m3u8=.mp4!)

if "%1" == "sub" for /F "delims=" %%a in ('@!youtube-dl_path! --no-playlist --youtube-skip-dash-manifest --encoding utf-8 --write-sub --print "^{\"requested_subtitles\":%%(requested_subtitles)j^}" %youtube-dl_spref% !mediabuilder_url!') do (set "youtube-dl_url=%%a" & echo !youtube-dl_url:.m3u8=.vtt!)

:end
endlocal
echo on>nul