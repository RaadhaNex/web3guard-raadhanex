# How to Apply

From your project root, copy the patch contents over your existing project.

PowerShell example:

```powershell
cd C:\web\web3guard
Expand-Archive -Path "$env:USERPROFILE\Downloads\web3guard_ui3d_home_patch.zip" -DestinationPath "$env:TEMP\web3guard_ui3d_home_patch" -Force
robocopy "$env:TEMP\web3guard_ui3d_home_patch" "C:\web\web3guard" /E
```

Then validate:

```powershell
cd frontend
npm run typecheck
npm run build
```

If backend was not touched, backend tests are not required for this patch. You can still run full checks if you want:

```powershell
cd ..\backend
python -m pytest -q
```

GitHub push:

```powershell
git status
git add .
git commit -m "Add cinematic UI 3D home"
git push origin main
```

Pages to check after deploy:

- `/`
- `/scanner/unified-url`
- `/pricing`
- `/results`
- `/report`
- `/docs`
- `/advanced`
- `/settings/language`
