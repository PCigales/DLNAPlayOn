@set "youtube-dl_path="C:\Program Files\SMPlayer\mpv\youtube-dl.exe""

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
for /F "delims=/ tokens=3,5,6" %%a in ("!mediabuilder_url!") do (set "youtube-dl_lng=%%a" & set "youtube-dl_url=https://www.arte.tv/hbbtvv2/services/web/index.php/OPA/v3/streams/%%b/SHOW/%%a" & echo.%%c)
if /I "!youtube-dl_lng!"=="de" (set youtube-dl_slng=A) else set youtube-dl_slng=F
set youtube-dl_urlvl=""
set youtube-dl_urlvo=""
set youtube-dl_urlvlh=0
set youtube-dl_urlvoh=0
for /F "delims=[] tokens=2" %%a in ('curl -s --ssl-no-revoke "!youtube-dl_url!"') do set "youtube-dl_json=%%a"
if "!youtube-dl_json!" == "}" for /F "delims=[] tokens=2" %%a in ('curl -s --ssl-no-revoke "!youtube-dl_url:/SHOW/=/BONUS/!"') do set "youtube-dl_json=%%a"
set youtube-dl_json=!youtube-dl_json:{=!
set youtube-dl_json=!youtube-dl_json:},=^

!
set youtube-dl_json=!youtube-dl_json:}=!
for /F "usebackq delims=" %%a in ('!youtube-dl_json!') do @(
set "youtubebe-dl_j=%%a"
set youtubebe-dl_j=!youtubebe-dl_j:,=^

!
set youtube-dl_url=""
set youtube-dl_asl=""
set youtube-dl_h=0
for /F "usebackq delims=: tokens=1,*" %%b in ('!youtubebe-dl_j!') do (
set youtube-dl_s=F
if /I "%%b"==""url"" (
set "youtube-dl_url=%%c"
set youtube-dl_s=T
) else if /I "%%b"==""audioShortLabel"" (
set "youtube-dl_asl=%%c"
set "youtube-dl_asl=!youtube-dl_asl:,=!"
set "youtube-dl_asl=!youtube-dl_asl:O=!"
set youtube-dl_s=T
) else if /I "%%b"==""height"" (
set "youtube-dl_h=%%c"
set youtube-dl_s=T
)
if !youtube-dl_s!==T (
if /I "!youtube-dl_asl!"==""V!youtube-dl_slng!"" (if !youtube-dl_h! GEQ !youtube-dl_urlvlh! set "youtube-dl_urlvl=!youtube-dl_url!" & set "youtube-dl_urlvlh=!youtube-dl_h!") else if /I "!youtube-dl_asl!"==""VST!youtube-dl_slng!"" (if !youtube-dl_h! GEQ !youtube-dl_urlvoh! set "youtube-dl_urlvo=!youtube-dl_url!" & set "youtube-dl_urlvoh=!youtube-dl_h!") else if /I "!youtube-dl_asl!"==""!youtube-dl_lng!"" (if !youtube-dl_h! GEQ !youtube-dl_urlvlh! set "youtube-dl_urlvl=!youtube-dl_url!" & set "youtube-dl_urlvlh=!youtube-dl_h!")
)
)
)
if !youtube-dl_urlvl!=="" (set youtube-dl_url=!youtube-dl_urlvo:\/=/!) else set youtube-dl_url=!youtube-dl_urlvl:\/=/!
set youtube-dl_url=!youtube-dl_url:~1,-1!
echo.!youtube-dl_url!
echo ###PlayOn_Separator###
)

if "%1" == "mux" for /F "delims=" %%a in ('@!youtube-dl_path! --no-playlist --youtube-skip-dash-manifest --encoding utf-8 -e --get-filename -o  ###PlayOn_Separator### -g -f "%youtube-dl_vpref%+%youtube-dl_apref%/%youtube-dl_pref%" !mediabuilder_url!') do (set "youtube-dl_url=%%a" & echo !youtube-dl_url:.m3u8=.mp4!)

if "%1" == "sub" for /F "delims=" %%a in ('@!youtube-dl_path! --no-playlist --youtube-skip-dash-manifest --encoding utf-8 --write-sub --print "^{\"requested_subtitles\":%%(requested_subtitles)j^}" %youtube-dl_spref% !mediabuilder_url!') do (set "youtube-dl_url=%%a" & echo !youtube-dl_url:.m3u8=.vtt!)

:end
endlocal
echo on>nul