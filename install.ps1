Set-Variable -Name "FLOW_HOME" (Get-ChildItem -Dir -Path "~\scoop\apps\flow-launcher\current" -Filter 'app*').FullName


Invoke-WebRequest https://github.com/CoDen256/dwds-flow/releases/latest/download/DWDS-Flow.zip -OutFile -OutFile "$FLOW_HOME\UserData\Plugins\DWDS-Flow.zip"
$githubLatestRelease = Invoke-WebRequest https://api.github.com/repos/CoDen256/dwds-flow/releases/latest | ConvertFrom-Json
unzip DWDS-Flow.zip