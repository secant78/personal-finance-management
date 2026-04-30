# Registers sync_job.py as a weekly Windows Task Scheduler job.
# Run once as Administrator: .\setup_scheduler.ps1

$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonExe  = (Get-Command python).Source
$Script     = Join-Path $ProjectDir "sync_job.py"
$LogFile    = Join-Path $ProjectDir "sync_job.log"
$TaskName   = "StripeBankSync"

$Action  = New-ScheduledTaskAction -Execute $PythonExe -Argument $Script -WorkingDirectory $ProjectDir
$Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At "08:00AM"
$Settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -RunOnlyIfNetworkAvailable

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Description "Weekly Stripe bank transaction sync to Google Sheets" `
    -Force

Write-Host ""
Write-Host "Task '$TaskName' registered. Runs every Monday at 8:00 AM."
Write-Host "Logs written to: $LogFile"
Write-Host ""
Write-Host "Other useful commands:"
Write-Host "  Run now:    Start-ScheduledTask -TaskName '$TaskName'"
Write-Host "  Check status: Get-ScheduledTask -TaskName '$TaskName'"
Write-Host "  Remove:     Unregister-ScheduledTask -TaskName '$TaskName'"
