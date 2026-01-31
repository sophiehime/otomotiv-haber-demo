Write-Host "🧹 TAM TEMİZLİK BAŞLIYOR..." -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan

# 1. PowerShell Geçmişi Temizle
Write-Host "[1/6] PowerShell geçmişi temizleniyor..." -ForegroundColor Gray
Clear-History
$historyPath = "$env:USERPROFILE\AppData\Roaming\Microsoft\Windows\PowerShell\PSReadLine\ConsoleHost_history.txt"
if (Test-Path $historyPath) {
    Remove-Item $historyPath -Force -ErrorAction SilentlyContinue
}
Write-Host "   ✓ Geçmiş temizlendi" -ForegroundColor Green

# 2. Oluşturulan Dosyaları Sil (Güvenli)
Write-Host "[2/6] Oluşturulan dosyalar aranıyor..." -ForegroundColor Gray
$deletePatterns = @(
    "otomotiv_haberleri_*.xlsx",
    "otomotiv_haberleri_*.pdf",
    "*_cevirili.xlsx",
    "*_rapor.pdf",
    "secilen_haberler.xlsx",
    "haber_raporu*.pdf",
    "demo_*.pdf",
    "test_*.pdf"
)

$deletedFiles = @()
foreach ($pattern in $deletePatterns) {
    $files = Get-ChildItem -Path . -Filter $pattern -ErrorAction SilentlyContinue
    foreach ($file in $files) {
        try {
            Remove-Item $file.FullName -Force -ErrorAction Stop
            $deletedFiles += $file.Name
            Write-Host "   ✗ $($file.Name) silindi" -ForegroundColor Red
        }
        catch {
            Write-Host "   ⚠️ $($file.Name) silinemedi" -ForegroundColor Yellow
        }
    }
}

if ($deletedFiles.Count -gt 0) {
    Write-Host "   ✓ $($deletedFiles.Count) dosya silindi" -ForegroundColor Green
} else {
    Write-Host "   ℹ️ Silinecek dosya bulunamadı" -ForegroundColor Blue
}

# 3. Temp Dosyaları Temizle
Write-Host "[3/6] Geçici dosyalar temizleniyor..." -ForegroundColor Gray
$tempFiles = Get-ChildItem -Path . -Filter "~$*" -ErrorAction SilentlyContinue
$tempFiles += Get-ChildItem -Path . -Filter "*.tmp" -ErrorAction SilentlyContinue
$tempFiles += Get-ChildItem -Path . -Filter ".~*" -ErrorAction SilentlyContinue

foreach ($file in $tempFiles) {
    try {
        Remove-Item $file.FullName -Force -ErrorAction SilentlyContinue
    }
    catch {}
}
Write-Host "   ✓ Geçici dosyalar temizlendi" -ForegroundColor Green

# 4. __pycache__ ve Python Cache Temizle
Write-Host "[4/6] Python cache dosyaları temizleniyor..." -ForegroundColor Gray
$pythonCache = Get-ChildItem -Path . -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue
foreach ($dir in $pythonCache) {
    try {
        Remove-Item $dir.FullName -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "   ✗ $($dir.Name) silindi" -ForegroundColor Red
    }
    catch {}
}

# .pyc, .pyo dosyalarını sil
$pycFiles = Get-ChildItem -Path . -Recurse -Filter "*.pyc" -ErrorAction SilentlyContinue
$pycFiles += Get-ChildItem -Path . -Recurse -Filter "*.pyo" -ErrorAction SilentlyContinue
foreach ($file in $pycFiles) {
    try {
        Remove-Item $file.FullName -Force -ErrorAction SilentlyContinue
    }
    catch {}
}
Write-Host "   ✓ Python cache temizlendi" -ForegroundColor Green

# 5. PowerShell Değişkenlerini Temizle
Write-Host "[5/6] PowerShell değişkenleri temizleniyor..." -ForegroundColor Gray
$protectedVars = @('_', '$', 'null', 'true', 'false', 'pshome', 'psversiontable', 
                   'pwd', 'home', 'host', 'args', 'error', 'foreach', 'input', 
                   'match', 'myinvocation', 'psboundparameters', 'pscmdlet', 
                   'pscommandpath', 'psscriptroot', 'sender', 'this')

Get-Variable | Where-Object { 
    $_.Name -notin $protectedVars -and 
    $_.Name -notmatch '^__' 
} | Remove-Variable -Force -ErrorAction SilentlyContinue
Write-Host "   ✓ Değişkenler temizlendi" -ForegroundColor Green

# 6. Ekranı Temizle
Write-Host "[6/6] Ekran temizleniyor..." -ForegroundColor Gray
Start-Sleep -Milliseconds 500
Clear-Host

# SONUÇ
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "🎉 TAM TEMİZLİK TAMAMLANDI!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
if ($deletedFiles.Count -gt 0) {
    Write-Host "Silinen dosyalar:" -ForegroundColor Yellow
    foreach ($file in $deletedFiles) {
        Write-Host "  • $file" -ForegroundColor Gray
    }
}
Write-Host ""
Write-Host "📁 Mevcut klasördeki dosyalar:" -ForegroundColor Yellow
Get-ChildItem -Path . -File | Select-Object -First 10 Name, Length, LastWriteTime | Format-Table -AutoSize
