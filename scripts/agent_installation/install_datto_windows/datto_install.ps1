New-Item -Path C:\datto_rmm_install -ItemType directory
$url = "https://thinkstack-pub-20180927131742566400000001.s3.amazonaws.com/datto_agent/NAME_OF_EXECUTABLE"
$outpath = "C:\datto_rmm_install\NAME_OF_EXECUTABLE"
Invoke-WebRequest -Uri $url -OutFile $outpath
Start-Sleep 10
Start-Process -Filepath "C:\datto_rmm_install\NAME_OF_EXECUTABLE" -ArgumentList @("/q","/n")