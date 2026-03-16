import os
import sys
import json
import platform
from pathlib import Path

# Platform-specific imports
if platform.system() == "Windows":
    import winreg

def register():
    current_os = platform.system()
    
    # 1. Setup paths
    project_root = Path(__file__).parent.parent.parent.parent.absolute()
    host_script = project_root / 'src' / 'zyron_linux' / 'core' / 'browser_host.py'
    manifest_template = project_root / 'src' / 'zyron_linux' / 'core' / 'native_manifest.json'
    
    if current_os == "Windows":
        manifest_output = project_root / 'src' / 'zyron_linux' / 'core' / 'zyron_native_host.json'
        
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
            print(f"✅ Successfully registered Zyron Native Host in Windows Registry.")
            print(f"📍 Manifest: {manifest_output}")
            print(f"🚀 Host: {bat_path}")
        except Exception as e:
            print(f"❌ Registry error: {e}")
    
    elif current_os == "Linux":
        # Linux uses ~/.mozilla/native-messaging-hosts/
        mozilla_native_dir = Path.home() / '.mozilla' / 'native-messaging-hosts'
        mozilla_native_dir.mkdir(parents=True, exist_ok=True)
        
        manifest_output = mozilla_native_dir / 'zyron_native_host.json'
        
        # Create shell script to launch Python
        shell_script_content = f'''#!/bin/bash
"{sys.executable}" -u "{host_script}" "$@"
'''
        shell_script_path = project_root / 'zyron_host.sh'
        
        with open(shell_script_path, 'w') as f:
            f.write(shell_script_content)
        
        # Make shell script executable
        os.chmod(shell_script_path, 0o755)
        
        # 2. Update manifest
        with open(manifest_template, 'r') as f:
            manifest = json.load(f)
        
        manifest['path'] = str(shell_script_path)
        
        # 3. Write manifest to Mozilla directory
        with open(manifest_output, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        print(f"✅ Successfully registered Zyron Native Host for Linux Firefox.")
        print(f"📍 Manifest: {manifest_output}")
        print(f"🚀 Host: {shell_script_path}")
    
    else:
        print(f"❌ Unsupported operating system: {current_os}")
        print("   Zyron currently supports Windows and Linux only.")

if __name__ == "__main__":
    register()
