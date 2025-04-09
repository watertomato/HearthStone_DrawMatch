import PyInstaller.__main__
import os
import shutil

# 清理旧的构建文件和分发文件
def cleanup():
    print("Cleaning up old build files...")
    for folder in ['build', 'dist']:
        if os.path.exists(folder):
            shutil.rmtree(folder)
    spec_files = [f for f in os.listdir('.') if f.endswith('.spec')]
    for spec_file in spec_files:
        os.remove(spec_file)
    print("Cleanup complete.")

# 定义要打包的脚本和选项
scripts_to_package = [
    {
        'script': 'main.py',
        'name': 'HearthstoneTool',
        'options': [
            '--onefile',
            '--windowed', # GUI application
            # '--add-data', 'hsJSON卡牌数据;hsJSON卡牌数据', 
            '--exclude-module', 'PyQt6' # Exclude conflicting Qt binding
            # Add other necessary hidden imports or data if needed
            # e.g., '--hidden-import=pandas._libs.tslibs.timedeltas'
        ]
    }
]

def build():
    cleanup()
    for item in scripts_to_package:
        script = item['script']
        name = item['name']
        options = item['options']
        
        if not os.path.exists(script):
            print(f"Error: Script '{script}' not found. Skipping...")
            continue
            
        print(f"\n--- Building {name} from {script} ---")
        command = [
            script,
            '--name', name
        ] + options
        
        try:
            print(f"Running PyInstaller with command: pyinstaller {' '.join(command)}")
            PyInstaller.__main__.run(command)
            print(f"--- Finished building {name} ---")
        except Exception as e:
            print(f"!!! Error building {name}: {e} !!!")

if __name__ == '__main__':
    build()
    print("\nBuild process finished. Executables are in the 'dist' folder.") 