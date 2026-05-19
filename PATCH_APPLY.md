# How to Apply

Apply this patch over your current Web3Guard project root.

## PowerShell example
```powershell
cd C:\web\web3guard
Expand-Archive -Path "$env:USERPROFILE\Downloads\web3guard_scroll_animated_ui_patch.zip" -DestinationPath "$env:TEMP\web3guard_scroll_patch" -Force
robocopy "$env:TEMP\web3guard_scroll_patch" "C:\web\web3guard" /E
```

## Validate
```powershell
cd frontend
npm run typecheck
npm run build
```

## Push
```powershell
git status
git add .
git commit -m "Add scroll animated cinematic UI"
git push origin main
```

## Pages to check
- `/`
- `/scanner`
- `/scanner/unified-url`
- `/results`
- `/report`
- `/pricing`
- `/docs`
- `/advanced`
- `/risk-intelligence`
