[CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = 'High')]
param(
    [Parameter(Mandatory = $true)]
    [string]$RepositoryPath,

    [Parameter(Mandatory = $true)]
    [string]$PythonExecutable,

    [string]$TaskName = 'Joe CCASS Daily Collector',
    [string]$DailyAt = '07:30',
    [string]$Watchlist = '01592',
    [Parameter(Mandatory = $true)]
    [string]$CsvOutputPath,
    [string]$SqlitePath = 'data\ccass_snapshots.db'
)

$resolvedRepository = (Resolve-Path -LiteralPath $RepositoryPath).Path
$resolvedPython = (Resolve-Path -LiteralPath $PythonExecutable).Path
$collectorArguments = @(
    '-m', 'ccass_core.collector',
    '--watchlist', $Watchlist,
    '--sqlite', $SqlitePath,
    '--output', $CsvOutputPath
)
$quotedArguments = ($collectorArguments | ForEach-Object { '"' + $_.Replace('"', '\"') + '"' }) -join ' '

$action = New-ScheduledTaskAction `
    -Execute $resolvedPython `
    -Argument $quotedArguments `
    -WorkingDirectory $resolvedRepository
$trigger = New-ScheduledTaskTrigger -Daily -At $DailyAt
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew

if ($PSCmdlet.ShouldProcess($TaskName, 'Register daily low-frequency CCASS collector task')) {
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Description 'Daily low-frequency public-mirror CCASS snapshot collector; never accesses HKEX SDW.'
}
