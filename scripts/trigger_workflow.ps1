param(
    [string]$Token,
    [string]$Owner = "ViniciusCamargo10",
    [string]$Repo = "MFO",
    [string]$Ref = "main"
)

$uri = "https://api.github.com/repos/$Owner/$Repo/actions/workflows/dou_automation.yml/dispatches"
$body = @{ ref = $Ref } | ConvertTo-Json
$headers = @{ Authorization = "Bearer $Token" }

Invoke-RestMethod -Uri $uri -Method POST -Headers $headers -Body $body -ContentType "application/json"
Write-Output "Workflow triggered at $(Get-Date)"
