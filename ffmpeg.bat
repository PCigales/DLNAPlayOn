@set "ffmpeg_path="C:\Program Files\FFmpeg\bin\ffmpeg.exe""
@set "ffmpeg_user_agent="Lavf/ Mozilla/ AppleWebKit/ Chrome/""

@setlocal enabledelayedexpansion

@if "!mediabuilder_start!" NEQ "" (@set "ffmpeg_st=-ss !mediabuilder_start!") else (@set "ffmpeg_st= ")
@if "!mediabuilder_start!" NEQ "" (@set "ffmpeg_st-=-ss 0") else (@set "ffmpeg_st-= ")

@if "!mediabuilder_vid!" == "" (
 @set "ffmpeg_vid= "
 @set "ffmpeg_aud= "
) else (
 @if "!mediabuilder_vid:://=!" == "!mediabuilder_vid!" (@set "ffmpeg_vid=%ffmpeg_st% -i !mediabuilder_vid!") else (@set "ffmpeg_vid=%ffmpeg_st% -user_agent !ffmpeg_user_agent! -i !mediabuilder_vid!")
 @if "!mediabuilder_aud!" == "" (
  @set "ffmpeg_aud=-map 0"
 ) else (
  @if "!mediabuilder_aud:://=!" == "!mediabuilder_aud!" (@set "ffmpeg_aud=-thread_queue_size 300000 %ffmpeg_st% -i !mediabuilder_aud! -map 0:v -map 1:a") else (@set "ffmpeg_aud=-thread_queue_size 300000 %ffmpeg_st% -user_agent !ffmpeg_user_agent! -i !mediabuilder_aud! -map 0:v -map 1:a")
 )
)

@if "!mediabuilder_sub!" == "" (
 @set "ffmpeg_sub= "
 @set "ffmpeg_lang= "
) else (
 @if "!mediabuilder_subcharenc!" == "" (@set "ffmpeg_subcharenc= ") else (@set "ffmpeg_subcharenc=-sub_charenc cp1252")
 @if "!mediabuilder_sub:://=!" == "!mediabuilder_sub!" (@set "ffmpeg_sub=%ffmpeg_st% !ffmpeg_subcharenc! -i !mediabuilder_sub! %ffmpeg_st-%") else (@set "ffmpeg_sub=%ffmpeg_st% !ffmpeg_subcharenc! -user_agent !ffmpeg_user_agent! -i !mediabuilder_sub! %ffmpeg_st-%")
 @if "!mediabuilder_lang!" == "" (@set "ffmpeg_lang=-map 0:s:0") else (@set "ffmpeg_lang=-map 0:s:m:language:!mediabuilder_lang:,=? -map 0:s:m:language:!?")
)

@set "ffmpeg_par=-c:v copy -c:a copy -sn -dn -y -f !mediabuilder_mux!"

@if /I "!mediabuilder_mux!" == "MP4" @set "ffmpeg_par=-c:v copy -c:a copy -sn -dn -map_chapters -1 -y -f MP4 -movflags empty_moov+frag_keyframe"

@if /I "!mediabuilder_mux!" == "MP4-" @set "ffmpeg_par=-c:v copy -c:a copy -bsf:a aac_adtstoasc -sn -dn -map_chapters -1 -y -f MP4 -movflags empty_moov+delay_moov+frag_keyframe"

@if /I "!mediabuilder_mux!" == "MP4--" @set "ffmpeg_par=-c:v copy -c:a copy -sn -dn -map_chapters -1 -y -f MP4 -movflags empty_moov+delay_moov+frag_keyframe"

@if /I "!mediabuilder_mux!" == "MPEGTS" @set "ffmpeg_par=%ffmpeg_st-% -c:v copy -c:a copy -sn -dn -y -f MPEGTS -mpegts_flags latm"

@if /I "!mediabuilder_mux!" == "MPEGTS-" (@set "ffmpeg_par=%ffmpeg_st-% -c:v copy -c:a copy -sn -dn -y -f MPEGTS -mpegts_flags latm") & (@set "ffmpeg_vid=-fflags +genpts !ffmpeg_vid!")

@if /I "!mediabuilder_mux!" == "MPEGTS--" @exit 1

@if /I "!mediabuilder_mux!" == "SRT" @set "ffmpeg_par=!ffmpeg_lang! -vn -an -dn -c:s srt -f SRT"

@if /I "!mediabuilder_mux!" == "SRT-" @set "ffmpeg_par=-vn -an -dn -f SRT"

@if /I "!mediabuilder_mux!" == "SRT--" @exit 1

@%ffmpeg_path% !ffmpeg_vid! !ffmpeg_aud! !ffmpeg_sub! %ffmpeg_par% -listen 1 !mediabuilder_address!

@endlocal

@exit %ERRORLEVEL%