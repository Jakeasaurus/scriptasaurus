 Get-Service | where{$_.StartType -eq "Automatic"} | Select name,status, starttype