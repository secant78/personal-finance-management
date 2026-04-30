# Registers bank-sync as a weekly Windows Task Scheduler job.
# Run once as Administrator: .\setup_scheduler.ps1

$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BankSync   = (Get-Command bank-sync -ErrorAction SilentlyContinue).Source

if (-not $BankSync) {
    Write-Error "bank-sync command not found. Run: pip install -e . first."
    exit 1
}

$TaskName = "StripeBankSync"
$LogFile  = Join-Path $ProjectDir "sync_job.log"

$Action   = New-ScheduledTaskAction -Execute $BankSync -WorkingDirectory $ProjectDir
$Trigger  = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At "08:00AM"
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
Write-Host "Useful commands:"
Write-Host "  Trigger now:   bank-sync"
Write-Host "  Run scheduled: Start-ScheduledTask -TaskName '$TaskName'"
Write-Host "  Check status:  Get-ScheduledTask  -TaskName '$TaskName'"
Write-Host "  Remove:        Unregister-ScheduledTask -TaskName '$TaskName'"
