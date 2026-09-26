# Registers the forward daily CCASS snapshot task (16:35 HKT, Mon-Fri).
# Follows the repo's existing install_collector_task.ps1 conventions:
# Windows Task Scheduler, SingleInstance=IgnoreNew, StartWhenAvailable.
[CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = 'High')]
param(
    [Parameter(Mandatory = $true)]
    [string]$RepositoryPath,

    [Parameter(Mandatory = $true)]
    [string]$PythonExecutable,

    [string]$TaskName = 'Joe CCASS Forward Daily Snapshot'
)

$resolvedRepository = (Resolve-Path -LiteralPath $RepositoryPath).Path
$resolvedPython = (Resolve-Path -LiteralPath $PythonExecutable).Path
$arguments = '-m', 'scripts.zc_forward_daily_snapshot'
$quotedArguments = ($arguments | ForEach-Object { '"' + $_.Replace('"', '\"') + '"' }) -join ' '

$action = New-ScheduledTaskAction `
    -Execute $resolvedPython `
    -Argument $quotedArguments `
    -WorkingDirectory $resolvedRepository
# 16:35 HKT Mon-Fri (repo convention: weekday schedule, no holiday calendar)
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday -At 16:35
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Hours 6)

if ($true) {
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Description 'Forward daily CCASS snapshot: ONE broker_holding_detail call per active stock. broker_holding_daily is never used by this job. Single-instance lock defers to any live CCASS production writer.'
}
