import os
import sys
import json
import winreg
from pathlib import Path

def register():
    # 1. Setup paths
    project_root = Path(__file__).parent.parent.parent.parent.absolute()
    host_script = project_root / 'src' / 'zyron' / 'core' / 'browser_host.py'
    manifest_template = project_root / 'src' / 'zyron' / 'core' / 'native_manifest.json'
    manifest_output = project_root / 'src' / 'zyron' / 'core' / 'zyron_native_host.json'
    
    # Batch file to launch python invisibly or at least with correct env
    # Using 'pythonw' if available to avoid a console window popping up
    python_exe = sys.executable
    pythonw_exe = python_exe.replace("python.exe", "pythonw.exe")
    
    if os.path.exists(pythonw_exe):
        exe_to_use = pythonw_exe
    else:
        exe_to_use = python_exe

    bat_content = f'@echo off\n"{exe_to_use}" -u "{host_script}" %*'
    bat_path = project_root / 'zyron_host.bat'
    
    with open(bat_path, 'w') as f:
        f.write(bat_content)
    
    # 2. Update manifest
    with open(manifest_template, 'r') as f:
        manifest = json.load(f)
    
    manifest['path'] = str(bat_path)
    
    with open(manifest_output, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    # 3. Registry update
    reg_key = r"Software\Mozilla\NativeMessagingHosts\zyron.native.host"
    try:
        winreg.CreateKey(winreg.HKEY_CURRENT_USER, reg_key)
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_key, 0, winreg.KEY_WRITE) as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, str(manifest_output))
        print(f"✅ Successfully registered Zyron Native Host in Registry.")
        print(f"📍 Manifest: {manifest_output}")
        print(f"🚀 Host: {bat_path}")
    except Exception as e:
        print(f"❌ Registry error: {e}")

if __name__ == "__main__":
    register()
