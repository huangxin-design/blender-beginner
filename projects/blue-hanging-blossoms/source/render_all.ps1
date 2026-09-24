param([string]$Blender='blender',[string]$Python='python')
$ErrorActionPreference='Stop'
for ($first=1; $first -le 384; $first+=12) {
    $last=[Math]::Min(384,$first+11)
    & $Blender --background --disable-autoexec --python-exit-code 1 --python (Join-Path $PSScriptRoot 'render_final.py') -- render $first $last
    if ($LASTEXITCODE -ne 0) { throw "Rendering failed at $first-$last." }
}
& $Python (Join-Path $PSScriptRoot 'encode_and_verify.py')
if ($LASTEXITCODE -ne 0) { throw 'Encoding or verification failed.' }
