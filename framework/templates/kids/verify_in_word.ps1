param([string]$OutputDirectory, [string]$FilePattern = '*.docx', [switch]$Recurse)
$ErrorActionPreference = 'Stop'
$sourceDirectory = $PSScriptRoot
[System.IO.Directory]::CreateDirectory($OutputDirectory) | Out-Null
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try {
    foreach ($file in Get-ChildItem -LiteralPath $sourceDirectory -Filter $FilePattern -Recurse:$Recurse) {
        $document = $word.Documents.Open($file.FullName, $false, $true)
        try {
            $document.Repaginate()
            $pages = $document.ComputeStatistics(2)
            $pdfPath = Join-Path $OutputDirectory ($file.BaseName + '.pdf')
            $document.ExportAsFixedFormat($pdfPath, 17)
            Write-Output ($file.Name + ': ' + $pages + ' pages')
        } finally { $document.Close(0) }
    }
} finally { $word.Quit() }
