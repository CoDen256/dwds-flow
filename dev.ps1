Set-Variable -Name "FLOW_HOME" (Get-ChildItem -Dir -Path "~\scoop\apps\flow-launcher\current" -Filter 'app*').FullName
Remove-Item -Path "$FLOW_HOME\UserData\Plugins\DWDS-Flow-Dev" -Recurse -Force
New-Item -Path "$FLOW_HOME\UserData\Plugins\DWDS-Flow-Dev" -ItemType Junction -Value $PWD -Force

taskkill /f /im Flow*
Start-Process -FilePath "~\scoop\apps\flow-launcher\current\Flow.Launcher.exe"