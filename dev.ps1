Set-Variable -Name "FLOW_HOME" (Get-ChildItem -Dir -Path "~\scoop\apps\flow-launcher\current" -Filter 'app*').FullName
Remove-Item -Path "$FLOW_HOME\UserData\Plugins\DWDS-Flow-*" -Recurse -Force
New-Item -Path "$FLOW_HOME\UserData\Plugins\DWDS-Flow-Dev" -ItemType Junction -Value $PWD\..\dwds-api -Force
pip install -r "$FLOW_HOME\UserData\Plugins\DWDS-Flow-Dev\requirements.txt" -t "$FLOW_HOME\UserData\Plugins\DWDS-Flow-Dev\lib"

taskkill /f /im Flow*
Start-Process -FilePath "~\scoop\apps\flow-launcher\current\Flow.Launcher.exe"