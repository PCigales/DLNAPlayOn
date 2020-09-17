@set "youtube-dl_path="C:\Program Files\SMPlayer\mpv\youtube-dl.exe""

@setlocal enabledelayedexpansion

@set "youtube-dl_pref=best"
@set "youtube-dl_vpref=bestvideo"
@set "youtube-dl_apref=bestaudio"
@if "%1" == "sub" (
if "!mediabuilder_lang!" == "" (@set "youtube-dl_spref=--sub-format srt/ass/ssa/vtt/best") else (@set "youtube-dl_spref=--sub-format srt/ass/ssa/vtt/best --sub-lang !mediabuilder_lang!")
)

@if /I "!mediabuilder_profile!" == "[TV]Samsung LED40" (
@set "youtube-dl_pref=best[vcodec*=?avc][width<=?1920][height<=?1080][fps<=?30][acodec*=?mp4]/best"
@set "youtube-dl_vpref=bestvideo[vcodec*=?avc][width<=?1920][height<=?1080][fps<=?30]"
@set "youtube-dl_apref=bestaudio[acodec*=?mp4]")

@if /I "!mediabuilder_profile!" == "BubbleUPnP (SM-A530F)" (
@set "youtube-dl_pref=best[vcodec*=?avc][width<=?1920][height<=?1080][acodec*=?mp4]/best"
@set "youtube-dl_vpref=bestvideo[vcodec*=?avc][width<=?1920][height<=?1080]"
@set "youtube-dl_apref=bestaudio[acodec*=?mp4]")

@if "%1" == "nomux" @%youtube-dl_path% --no-playlist --youtube-skip-dash-manifest --encoding utf-8 -e --get-filename -o  ###PlayOn_Separator### -g -f "%youtube-dl_pref%" !mediabuilder_url!

@if "%1" == "mux" @%youtube-dl_path% --no-playlist --youtube-skip-dash-manifest --encoding utf-8 -e --get-filename -o  ###PlayOn_Separator### -g -f "%youtube-dl_vpref%+%youtube-dl_apref%/%youtube-dl_pref%" !mediabuilder_url!

@if "%1" == "sub" @%youtube-dl_path% --no-playlist --youtube-skip-dash-manifest --encoding utf-8 -j --write-sub %youtube-dl_spref% !mediabuilder_url!

@endlocal