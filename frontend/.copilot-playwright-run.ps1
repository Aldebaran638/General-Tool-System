$wd = "D:\path\to\your\project\frontend"
$spec = "tests/navigation.spec.ts"
$out = Join-Path $wd "playwright.out.log"
$err = Join-Path $wd "playwright.err.log"
if (Test-Path $out) { Remove-Item $out -Force }
if (Test-Path $err) { Remove-Item $err -Force }
$p = Start-Process -FilePath "cmd.exe" -ArgumentList "/d /s /c npx playwright test $spec --reporter=line" -WorkingDirectory $wd -RedirectStandardOutput $out -RedirectStandardError $err -PassThru
$deadline = (Get-Date).AddSeconds(600)
while (-not $p.HasExited) {
  Start-Sleep -Seconds 2
  $p.Refresh()
  if ((Get-Date) -ge $deadline) {
    Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
    Write-Output "TIMEOUT_REACHED=600s"
    if (Test-Path $out) { Write-Output "--- STDOUT (tail) ---"; Get-Content $out -Tail 120 }
    if (Test-Path $err) { Write-Output "--- STDERR (tail) ---"; Get-Content $err -Tail 120 }
    exit 124
  }
  $stdoutTail = if (Test-Path $out) { (Get-Content $out -Tail 40) -join "`n" } else { "" }
  $stderrTail = if (Test-Path $err) { (Get-Content $err -Tail 40) -join "`n" } else { "" }
  $combined = "$stdoutTail`n$stderrTail"
  if ($combined -match "Error:|FAILED|failed|Timed out|Test timeout|ERR_|SyntaxError|ReferenceError") {
    Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
    Write-Output "PLAYWRIGHT_FAILED_EARLY=1"
    if (Test-Path $out) { Write-Output "--- STDOUT (tail) ---"; Get-Content $out -Tail 120 }
    if (Test-Path $err) { Write-Output "--- STDERR (tail) ---"; Get-Content $err -Tail 120 }
    exit 1
  }
}
Write-Output "EXIT_CODE=$($p.ExitCode)"
if (Test-Path $out) { Write-Output "--- STDOUT (tail) ---"; Get-Content $out -Tail 120 }
if (Test-Path $err) { Write-Output "--- STDERR (tail) ---"; Get-Content $err -Tail 120 }
if ($p.ExitCode -ne 0) { exit $p.ExitCode }
