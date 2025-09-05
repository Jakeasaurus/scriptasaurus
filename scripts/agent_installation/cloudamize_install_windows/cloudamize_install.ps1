New-Item -Path C:\cloudamize_install -ItemType directory
$url = "https://agentmanager1.cloudamize.com/cxf/downloadFile/cloudamizeAgent.msi"
$outpath = "C:\cloudamize_install\cloudamize_agent.msi"
Invoke-WebRequest -Uri $url -OutFile $outpath
Start-Sleep 10
msiexec /i  "C:\cloudamize_install\cloudamize_agent.msi" customerkey=CUSTOMER-KEY-HERE /qn