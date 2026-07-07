$ErrorActionPreference = "Stop"

$python = "python"
$bundledPython = "C:\Users\sarab\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

if (Test-Path -LiteralPath $bundledPython) {
    $python = $bundledPython
}

& $python app.py --host 127.0.0.1 --port 8000
