# Start the storyboard API without hot-reload and without broken system proxies.
$env:HTTP_PROXY = ""
$env:HTTPS_PROXY = ""
$env:ALL_PROXY = ""

Set-Location $PSScriptRoot
uvicorn api:app --host 127.0.0.1 --port 8000
