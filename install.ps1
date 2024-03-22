Set-Variable -Name "FLOW_HOME" (Get-ChildItem -Dir -Path "~\scoop\apps\flow-launcher\current" -Filter 'app*').FullName

$tag = (Invoke-RestMethod -Uri https://api.github.com/repos/CoDen256/dwds-flow/releases/latest).tag_name
Invoke-WebRequest https://github.com/CoDen256/dwds-flow/releases/latest/download/DWDS-Flow-$tag.zip -OutFile ~\Downloads\DWDS-Flow-$tag.zip
Remove-Item "$FLOW_HOME\UserData\Plugins\DWDS-Flow-*" -Recurse -Force
Expand-Archive -Path ~\Downloads\DWDS-Flow-$tag.zip -DestinationPath "$FLOW_HOME\UserData\Plugins\DWDS-Flow-$tag"
Remove-Item -Path ~\Downloads\DWDS-Flow-$tag.zip

taskkill /f /im Flow*
Start-Process -FilePath "~\scoop\apps\flow-launcher\current\Flow.Launcher.exe"
