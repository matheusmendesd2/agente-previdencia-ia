# Build and test script for Legacy API
Write-Host "Building main project..." -ForegroundColor Green
dotnet build "$PSScriptRoot\..\services\legacy-api\LegacyApi.csproj" 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "Main project build failed!" -ForegroundColor Red
    exit 1
}

Write-Host "Copying dependency DLLs to test output..." -ForegroundColor Green
$mainOutput = "$PSScriptRoot\..\services\legacy-api\bin\Debug\net8.0"
$testOutput = "$PSScriptRoot\..\tests\LegacyApi.Tests\bin\Debug\net8.0"

New-Item -ItemType Directory -Path $testOutput -Force | Out-Null

# Copy main DLL and its dependencies
Get-ChildItem "$mainOutput\*.dll" | Copy-Item -Destination $testOutput -Force

Write-Host "Running tests..." -ForegroundColor Green
dotnet test "$PSScriptRoot\..\tests\LegacyApi.Tests\LegacyApi.Tests.csproj" 2>&1
