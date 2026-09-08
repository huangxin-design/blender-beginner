$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false

$taskProjectDir = $PSScriptRoot
$taskWorkspaceDir = Split-Path (Split-Path $taskProjectDir -Parent) -Parent
$taskOutputDir = Join-Path $taskWorkspaceDir '渲染/09_紫色悬浮几何动画'
$taskFramesDir = Join-Path $taskOutputDir 'frames'
$taskAudioPath = Join-Path $taskProjectDir '参考音轨.m4a'
$taskVideoPath = Join-Path $taskOutputDir '09_悬浮几何_五套配色_30秒.mp4'
$taskReportPath = Join-Path $taskProjectDir 'encode_report.json'
$taskEncodeLog = Join-Path $taskProjectDir 'encode_ffmpeg.log'
$taskDecodeLog = Join-Path $taskProjectDir 'decode_errors.log'
$taskBinDir = 'C:/Users/YOUR_USERNAME/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg.Essentials_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-8.1.1-essentials_build/bin'
$taskFfmpeg = Join-Path $taskBinDir 'ffmpeg.exe'
$taskFfprobe = Join-Path $taskBinDir 'ffprobe.exe'
$taskTimer = [Diagnostics.Stopwatch]::StartNew()
$taskReport = [ordered]@{
    status = 'running'
    started_utc = [DateTime]::UtcNow.ToString('o')
    output = $taskVideoPath
    frames_directory = $taskFramesDir
    source_audio = $taskAudioPath
    source_audio_note = 'AAC copied from the user-provided reference video without audio re-encoding.'
    intended_video = @{ width = 720; height = 1280; fps = 30; frame_count = 900; duration_seconds = 30 }
    encoding = @{ codec = 'libx264'; crf = 18; preset = 'slow'; pixel_format = 'yuv420p'; faststart = $true }
    color_conversion = 'Explicit full-range RGB PNG to limited-range YUV using the BT.709 matrix. No transfer-function conversion filter was applied; actual matrix, primaries and transfer metadata are recorded in probe.streams.'
}

try {
    if (-not (Test-Path -LiteralPath $taskAudioPath -PathType Leaf)) {
        throw "Missing reference audio: $taskAudioPath"
    }
    $taskFrameFiles = @(Get-ChildItem -LiteralPath $taskFramesDir -Filter 'frame_*.png' -File)
    if ($taskFrameFiles.Count -ne 900) {
        throw "Expected 900 PNG frames; found $($taskFrameFiles.Count). Encoding has not started."
    }
    $taskHeader = New-Object byte[] 24
    foreach ($taskFrameNumber in 1..900) {
        $taskFramePath = Join-Path $taskFramesDir ('frame_{0:D4}.png' -f $taskFrameNumber)
        $taskFrameStream = [IO.File]::OpenRead($taskFramePath)
        try {
            if ($taskFrameStream.Read($taskHeader, 0, 24) -ne 24) { throw "Truncated PNG: $taskFramePath" }
        } finally {
            $taskFrameStream.Dispose()
        }
        if (($taskHeader[0..7] -join ',') -ne '137,80,78,71,13,10,26,10') {
            throw "Invalid PNG signature: $taskFramePath"
        }
        $taskWidth = ([int]$taskHeader[16] * 16777216) + ([int]$taskHeader[17] * 65536) + ([int]$taskHeader[18] * 256) + [int]$taskHeader[19]
        $taskHeight = ([int]$taskHeader[20] * 16777216) + ([int]$taskHeader[21] * 65536) + ([int]$taskHeader[22] * 256) + [int]$taskHeader[23]
        if ($taskWidth -ne 720 -or $taskHeight -ne 1280) {
            throw "Unexpected PNG dimensions ${taskWidth}x${taskHeight}: $taskFramePath"
        }
    }
    $taskReport['input_png_headers_verified'] = 900
    $taskEncodeArgs = @(
        '-hide_banner', '-loglevel', 'warning', '-nostdin', '-y',
        '-framerate', '30', '-start_number', '1',
        '-i', (Join-Path $taskFramesDir 'frame_%04d.png'),
        '-i', $taskAudioPath,
        '-map', '0:v:0', '-map', '1:a:0',
        '-vf', 'scale=in_range=pc:out_range=tv:out_color_matrix=bt709,format=yuv420p',
        '-c:v', 'libx264', '-preset', 'slow', '-crf', '18',
        '-r', '30', '-fps_mode', 'cfr', '-frames:v', '900', '-t', '30',
        '-pix_fmt', 'yuv420p', '-color_range', 'tv',
        '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709',
        '-c:a', 'copy', '-movflags', '+faststart', $taskVideoPath
    )
    & $taskFfmpeg @taskEncodeArgs 2> $taskEncodeLog
    if ($LASTEXITCODE -ne 0) { throw "Encoding failed; see $taskEncodeLog" }

    $taskProbeArgs = @(
        '-v', 'error', '-count_frames',
        '-show_entries', 'format=duration,size:stream=index,codec_type,codec_name,width,height,avg_frame_rate,r_frame_rate,nb_frames,nb_read_frames,duration,pix_fmt,color_range,color_space,color_transfer,color_primaries,sample_rate,channels',
        '-of', 'json', $taskVideoPath
    )
    $taskProbeText = & $taskFfprobe @taskProbeArgs
    if ($LASTEXITCODE -ne 0) { throw 'Encoded MP4 could not be inspected by ffprobe.' }
    $taskProbe = ($taskProbeText -join "`n") | ConvertFrom-Json
    $taskVideo = @($taskProbe.streams | Where-Object { $_.codec_type -eq 'video' })
    $taskAudio = @($taskProbe.streams | Where-Object { $_.codec_type -eq 'audio' })
    if ($taskVideo.Count -ne 1 -or $taskAudio.Count -ne 1) { throw 'Expected one video stream and one audio stream.' }
    $taskVideo = $taskVideo[0]
    $taskAudio = $taskAudio[0]
    if ($taskVideo.codec_name -ne 'h264' -or $taskVideo.width -ne 720 -or $taskVideo.height -ne 1280) { throw 'Unexpected video codec or dimensions.' }
    if ($taskVideo.r_frame_rate -ne '30/1' -or $taskVideo.avg_frame_rate -ne '30/1') { throw 'Video is not constant 30 fps.' }
    if ([int]$taskVideo.nb_read_frames -ne 900 -or [int]$taskVideo.nb_frames -ne 900) { throw 'Encoded video does not contain 900 readable frames.' }
    if ([Math]::Abs([double]$taskVideo.duration - 30) -gt 0.001) { throw 'Video stream duration is not 30 seconds.' }
    if ($taskVideo.pix_fmt -ne 'yuv420p' -or $taskVideo.color_space -ne 'bt709' -or $taskVideo.color_range -ne 'tv') { throw 'Unexpected encoded pixel format, matrix, or range.' }
    if ($taskAudio.codec_name -ne 'aac' -or [double]$taskAudio.duration -lt 29.9 -or [double]$taskAudio.duration -gt 30.1) { throw 'AAC stream is missing or has unexpected duration.' }

    & $taskFfmpeg '-hide_banner' '-loglevel' 'error' '-nostdin' '-xerror' '-i' $taskVideoPath '-map' '0:v:0' '-map' '0:a:0' '-f' 'null' '-' 2> $taskDecodeLog
    if ($LASTEXITCODE -ne 0) { throw "Full MP4 decode failed; see $taskDecodeLog" }
    $taskDecodeErrorText = Get-Content -LiteralPath $taskDecodeLog -Raw
    if (-not [string]::IsNullOrWhiteSpace($taskDecodeErrorText)) { throw "Full MP4 decode reported errors; see $taskDecodeLog" }

    $taskReport['probe'] = $taskProbe
    $taskReport['full_video_and_audio_decode'] = 'passed without reported errors'
    $taskReport['status'] = 'passed'
    $taskReport['completed_utc'] = [DateTime]::UtcNow.ToString('o')
    $taskReport['elapsed_seconds'] = [Math]::Round($taskTimer.Elapsed.TotalSeconds, 3)
    $taskReport | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $taskReportPath -Encoding utf8
    Write-Output "Encoded and verified 900 frames, 30 seconds, 720x1280 at 30 fps, with source AAC."
    Write-Output $taskVideoPath
    Write-Output $taskReportPath
} catch {
    $taskReport['status'] = 'failed'
    $taskReport['error'] = $_.Exception.Message
    $taskReport['elapsed_seconds'] = [Math]::Round($taskTimer.Elapsed.TotalSeconds, 3)
    $taskReport | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $taskReportPath -Encoding utf8
    throw
}
