# How to Apply

From your project root, copy this patch over your existing project files.

## PowerShell example

```powershell
cd C:\web\web3guard
Expand-Archive -Path "$env:USERPROFILE\Downloads\web3guard_home_entry_ui_patch.zip" -DestinationPath "$env:TEMP\web3guard_home_entry_ui_patch" -Force
robocopy "$env:TEMP\web3guard_home_entry_ui_patch" "C:\web\web3guard" /E
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
git commit -m "Add clean Home entry UI"
git push origin main
```

## Pages to check
- `/`
- `/scanner/unified-url`
- `/results`
- `/report`
- `/pricing`
- `/docs`
- `/auth/login`
```
