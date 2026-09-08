# Windows x64 / Blender 5.2 portable setup. No global PATH or registry changes.
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$InstallRoot,
    [Parameter(Mandatory = $true)][ValidatePattern('^5\.2\.\d+$')][string]$Version,
    [string]$ArchivePath,
    [string]$ChecksumPath,
    [switch]$PlanOnly
)

$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT' -or $env:PROCESSOR_ARCHITECTURE -ne 'AMD64') {
    throw 'This helper supports native Windows x64 only.'
}
if ($InstallRoot -notmatch '^[A-Za-z]:[\\/]') {
    throw 'Choose an absolute local directory, for example D:\Blender.'
}
$root = [IO.Path]::GetFullPath($InstallRoot).TrimEnd('\', '/')
if ($root.Length -le 3) { throw 'Choose a folder, not an entire drive root.' }
$drive = Get-PSDrive -Name $root.Substring(0, 1) -PSProvider FileSystem
$packageName = "blender-$Version-windows-x64.zip"
$appName = "blender-$Version-windows-x64"
$appDir = Join-Path $root $appName
$baseUrl = 'https://download.blender.org/release/Blender5.2/'
$packageUrl = $baseUrl + $packageName
$checksumUrl = $baseUrl + "blender-$Version.sha256"
if ([bool]$ArchivePath -ne [bool]$ChecksumPath) {
    throw 'For an offline installation, supply both ArchivePath and ChecksumPath.'
}
$plan = [ordered]@{
    root = $root
    version = $Version
    executable = Join-Path $appDir 'blender.exe'
    configuration = Join-Path $appDir 'portable\config'
    package_url = $packageUrl
    checksum_url = $checksumUrl
    free_bytes = $drive.Free
    folders = @('downloads', 'projects', 'renders', 'temp', 'verification')
    source = $(if ($ArchivePath) { 'local-archive' } else { 'official-download' })
    plan_only = [bool]$PlanOnly
}
if ($PlanOnly) { $plan | ConvertTo-Json -Depth 4; return }
if (Test-Path -LiteralPath $root) {
    if (@(Get-ChildItem -LiteralPath $root -Force).Count -ne 0) {
        throw 'Destination is not empty. Reuse an existing Blender or choose a new setup folder.'
    }
}
if ($drive.Free -lt 4GB) { throw 'Allow at least 4 GB free for the portable application and setup.' }
$configureScript = Join-Path $PSScriptRoot 'configure_blender.py'
if (-not (Test-Path -LiteralPath $configureScript -PathType Leaf)) {
    throw 'configure_blender.py is missing from the skill.'
}
New-Item -ItemType Directory -Path $root -Force | Out-Null
$downloads = Join-Path $root 'downloads'
New-Item -ItemType Directory -Path $downloads | Out-Null
if ($ArchivePath) {
    $archive = (Resolve-Path -LiteralPath $ArchivePath).Path
    $checksums = (Resolve-Path -LiteralPath $ChecksumPath).Path
} else {
    $archive = Join-Path $downloads $packageName
    $checksums = Join-Path $downloads "blender-$Version.sha256"
    & curl.exe --fail --location --silent --show-error --retry 2 --connect-timeout 30 --max-time 900 --output $checksums $checksumUrl
    if ($LASTEXITCODE -ne 0) { throw 'Official checksum download failed.' }
    & curl.exe --fail --location --silent --show-error --retry 2 --connect-timeout 30 --max-time 900 --output $archive $packageUrl
    if ($LASTEXITCODE -ne 0) { throw 'Official archive download failed.' }
}
$pattern = '^([0-9a-fA-F]{64})\s+\*?' + [regex]::Escape($packageName) + '$'
$matchesFound = @(Get-Content -LiteralPath $checksums | Select-String -Pattern $pattern)
if ($matchesFound.Count -ne 1) { throw 'Expected ZIP checksum is missing or ambiguous.' }
$expected = $matchesFound[0].Matches[0].Groups[1].Value
$actual = (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash
if ($actual -ne $expected) { throw 'SHA256 mismatch; the archive was not extracted or executed.' }

Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [IO.Compression.ZipFile]::OpenRead($archive)
try {
    $expandedBytes = 0L
    $allowedPrefix = $appDir + [IO.Path]::DirectorySeparatorChar
    foreach ($entry in $zip.Entries) {
        $target = [IO.Path]::GetFullPath((Join-Path $root $entry.FullName))
        if ($target -ne $appDir -and -not $target.StartsWith($allowedPrefix, [StringComparison]::OrdinalIgnoreCase)) {
            throw "Unexpected archive path: $($entry.FullName)"
        }
        $expandedBytes += $entry.Length
    }
    $available = (Get-PSDrive -Name $root.Substring(0, 1) -PSProvider FileSystem).Free
    if ($available -lt $expandedBytes + 1GB) { throw 'Not enough free space to unpack and verify Blender.' }
} finally { $zip.Dispose() }
[IO.Compression.ZipFile]::ExtractToDirectory($archive, $root)
$executable = Join-Path $appDir 'blender.exe'
if (-not (Test-Path -LiteralPath $executable -PathType Leaf)) { throw 'Blender executable is missing.' }
New-Item -ItemType Directory -Path (Join-Path $appDir 'portable') | Out-Null
$signature = Get-AuthenticodeSignature -LiteralPath $executable
if ($signature.Status -eq 'HashMismatch') { throw 'Executable signature reports a hash mismatch.' }
& $executable --version | Out-File -LiteralPath (Join-Path $root 'version.log') -Encoding utf8
if ($LASTEXITCODE -ne 0) { throw 'Blender could not start.' }
$sessionTemp = Join-Path $root 'temp'
New-Item -ItemType Directory -Path $sessionTemp | Out-Null
$previousTemp, $previousTmp = $env:TEMP, $env:TMP
try {
    $env:TEMP, $env:TMP = $sessionTemp, $sessionTemp
    & $executable --background --factory-startup --disable-autoexec --python-exit-code 1 --python $configureScript -- --root $root *> (Join-Path $root 'setup.log')
    if ($LASTEXITCODE -ne 0) { throw "Configuration failed. Inspect $root\setup.log before retrying." }
} finally {
    $env:TEMP, $env:TMP = $previousTemp, $previousTmp
}
$setupResult = Get-Content -LiteralPath (Join-Path $root 'verification\setup.json') -Raw | ConvertFrom-Json
if ($setupResult.blender_version -notmatch ('^' + [regex]::Escape($Version) + '(\s|$)')) {
    throw 'The executable version does not match the requested package version.'
}
$plan['plan_only'] = $false
$plan['sha256'] = $actual
$plan['signature_status'] = [string]$signature.Status
$plan['installed_at'] = (Get-Date).ToString('o')
$plan['setup_report'] = Join-Path $root 'verification\setup.json'
$plan | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $root 'installation.json') -Encoding utf8
$plan | ConvertTo-Json -Depth 4
