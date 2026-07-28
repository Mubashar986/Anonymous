# =====================================================================
# Comprehensive FastAPI Endpoint & Real User Regression Test Script
# User: mubasharashraf (mubashirmaitlo@gmail.com)
# =====================================================================

$baseUrl = "http://127.0.0.1:8000"
$v1Url = "$baseUrl/api/v1"

Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "   FastAPI Auth System Real User Regression Test     " -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host ""

function Print-TestResult($testName, $status, $response) {
    if ($status -eq "PASS") {
        Write-Host "[PASS] $testName" -ForegroundColor Green
    } else {
        Write-Host "[FAIL] $testName" -ForegroundColor Red
    }
    if ($response) {
        Write-Host "       Response: $($response | ConvertTo-Json -Compress)" -ForegroundColor Gray
    }
    Write-Host ""
}

# ---------------------------------------------------------------------
# 1. Health Check Endpoint
# ---------------------------------------------------------------------
try {
    $res = Invoke-RestMethod -Uri "$baseUrl/health" -Method Get
    Print-TestResult "GET /health" "PASS" $res
} catch {
    Print-TestResult "GET /health" "FAIL" $_.Exception.Message
}

$userEmail = "mubashirmaitlo@gmail.com"
$userUsername = "mubasharashraf"
$userPassword = "Password123!"

# ---------------------------------------------------------------------
# 2. User Registration (Signup)
# ---------------------------------------------------------------------
$signupBody = @{
    email = $userEmail
    username = $userUsername
    password = $userPassword
} | ConvertTo-Json

try {
    $userRes = Invoke-RestMethod -Uri "$v1Url/auth/signup" -Method Post -Body $signupBody -ContentType "application/json"
    Print-TestResult "POST /auth/signup (User: $userEmail)" "PASS" $userRes
} catch {
    Write-Host "[INFO] User may already exist. Attempting to proceed..." -ForegroundColor Yellow
}

# ---------------------------------------------------------------------
# 3. User Login (Authentication)
# ---------------------------------------------------------------------
$loginBody = @{
    email = $userEmail
    password = $userPassword
} | ConvertTo-Json

try {
    $tokenRes = Invoke-RestMethod -Uri "$v1Url/auth/login" -Method Post -Body $loginBody -ContentType "application/json"
    Print-TestResult "POST /auth/login (Valid Credentials)" "PASS" @{ access_token_prefix = $tokenRes.access_token.Substring(0, 20) + "..." }
    $accessToken = $tokenRes.access_token
    $refreshToken = $tokenRes.refresh_token
} catch {
    Print-TestResult "POST /auth/login (Valid Credentials)" "FAIL" $_.Exception.Message
}

# ---------------------------------------------------------------------
# 4. Protected Route: GET /users/me
# ---------------------------------------------------------------------
$headers = @{ Authorization = "Bearer $accessToken" }
try {
    $profileRes = Invoke-RestMethod -Uri "$v1Url/users/me" -Method Get -Headers $headers
    Print-TestResult "GET /users/me (Fetch Profile)" "PASS" $profileRes
} catch {
    Print-TestResult "GET /users/me (Fetch Profile)" "FAIL" $_.Exception.Message
}

# ---------------------------------------------------------------------
# 5. Token Refresh: POST /auth/refresh (Rotation)
# ---------------------------------------------------------------------
$refreshBody = @{
    refresh_token = $refreshToken
} | ConvertTo-Json

try {
    $newTokenRes = Invoke-RestMethod -Uri "$v1Url/auth/refresh" -Method Post -Body $refreshBody -ContentType "application/json"
    Print-TestResult "POST /auth/refresh (Token Rotation)" "PASS" @{ new_access_token_prefix = $newTokenRes.access_token.Substring(0, 20) + "..." }
    $newRefreshToken = $newTokenRes.refresh_token
} catch {
    Print-TestResult "POST /auth/refresh (Token Rotation)" "FAIL" $_.Exception.Message
}

# ---------------------------------------------------------------------
# 6. Forgot Password Request (Triggers Reset Email!)
# ---------------------------------------------------------------------
try {
    $forgotRes = Invoke-RestMethod -Uri "$v1Url/auth/forgot-password?email=$userEmail" -Method Post
    Print-TestResult "POST /auth/forgot-password (Reset Request for $userEmail)" "PASS" $forgotRes
} catch {
    Print-TestResult "POST /auth/forgot-password" "FAIL" $_.Exception.Message
}

Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "   Test Suite Complete! Check Uvicorn Terminal Output " -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan
