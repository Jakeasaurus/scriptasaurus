New-Item -Path C:\cloud_endure_uninstall -ItemType directory
Move-item "C:\Program Files (x86)\CloudEndure\dist" "C:\cloud_endure_uninstall"
C:\cloud_endure_uninstall\install_agent_windows.exe --remove