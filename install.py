#!/usr/bin/env python3
"""
自动安装脚本
检测操作系统并安装所需依赖
"""

import os
import sys
import platform
import subprocess


def run_command(command, shell=False):
    """运行系统命令"""
    try:
        result = subprocess.run(command, shell=shell, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ 成功: {' '.join(command) if isinstance(command, list) else command}")
            return True
        else:
            print(f"✗ 失败: {' '.join(command) if isinstance(command, list) else command}")
            print(f"  错误: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ 执行命令时出错: {e}")
        return False


def check_python_version():
    """检查Python版本"""
    print("检查Python版本...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"✗ Python版本过低: {version.major}.{version.minor}")
        print("  需要Python 3.8或更高版本")
        return False
    print(f"✓ Python版本: {version.major}.{version.minor}.{version.micro}")
    return True


def install_system_dependencies():
    """安装系统依赖"""
    print("\n安装系统依赖...")
    system = platform.system()
    
    if system == "Linux":
        distro = platform.linux_distribution()[0].lower() if hasattr(platform, 'linux_distribution') else ''
        
        # 检查是否有sudo权限
        if os.geteuid() != 0:
            print("需要管理员权限来安装系统依赖")
            print("请使用: sudo python install.py")
            return False
            
        if 'ubuntu' in distro or 'debian' in distro:
            commands = [
                ["apt-get", "update"],
                ["apt-get", "install", "-y", "python3-pyaudio", "portaudio19-dev", "python3-tk", "python3-dev"]
            ]
        elif 'fedora' in distro or 'centos' in distro:
            commands = [
                ["yum", "install", "-y", "portaudio-devel", "python3-tkinter", "python3-devel"]
            ]
        else:
            print("未知的Linux发行版，请手动安装portaudio和tkinter")
            return False
            
        for cmd in commands:
            if not run_command(cmd):
                return False
                
    elif system == "Darwin":  # macOS
        # 检查是否安装了Homebrew
        if not run_command(["which", "brew"]):
            print("未找到Homebrew，正在安装...")
            install_brew = '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
            if not run_command(install_brew, shell=True):
                print("Homebrew安装失败，请手动安装")
                return False
                
        # 安装portaudio
        if not run_command(["brew", "install", "portaudio"]):
            return False
            
    elif system == "Windows":
        print("Windows系统检测到")
        print("PyAudio在Windows上可能需要特殊处理")
        print("如果pip安装失败，请从以下链接下载预编译的wheel文件：")
        print("https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio")
        
    return True


def install_python_dependencies():
    """安装Python依赖"""
    print("\n安装Python依赖...")
    
    # 升级pip
    print("升级pip...")
    run_command([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    
    # 特殊处理PyAudio
    if platform.system() == "Windows":
        print("\n注意: 在Windows上安装PyAudio可能需要额外步骤")
        print("如果下面的安装失败，请：")
        print("1. 从 https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio 下载对应版本的.whl文件")
        print("2. 使用命令: pip install 下载的文件名.whl")
        input("\n按Enter继续...")
    
    # 安装requirements.txt中的依赖
    if os.path.exists("requirements.txt"):
        print("\n从requirements.txt安装依赖...")
        if not run_command([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]):
            print("\n部分依赖安装失败，尝试逐个安装...")
            
            # 逐个安装依赖
            with open("requirements.txt", "r") as f:
                for line in f:
                    package = line.strip()
                    if package and not package.startswith("#"):
                        print(f"\n安装 {package}...")
                        run_command([sys.executable, "-m", "pip", "install", package])
    else:
        print("✗ 未找到requirements.txt文件")
        return False
        
    return True


def check_installation():
    """检查安装是否成功"""
    print("\n检查安装...")
    
    required_modules = [
        "speech_recognition",
        "openai",
        "pyaudio",
        "numpy",
        "tkinter",
        "webrtcvad"
    ]
    
    all_ok = True
    for module in required_modules:
        try:
            if module == "tkinter":
                import tkinter
            else:
                __import__(module)
            print(f"✓ {module} 已安装")
        except ImportError:
            print(f"✗ {module} 未安装")
            all_ok = False
            
    return all_ok


def create_config_file():
    """创建配置文件模板"""
    print("\n创建配置文件...")
    
    if not os.path.exists("config.ini"):
        config_content = """[API]
openai_key = your-openai-api-key-here
openai_base_url = https://api.openai.com/v1

[Audio]
sample_rate = 16000
chunk_size = 1024
energy_threshold = 2000
pause_threshold = 0.8
phrase_threshold = 0.3
max_phrase_duration = 5

[Translation]
model = gpt-4-turbo-preview
temperature = 0.3
max_tokens = 500

[Display]
font_size_source = 14
font_size_target = 14
window_width = 1400
window_height = 800
"""
        
        with open("config.ini", "w") as f:
            f.write(config_content)
            
        print("✓ 配置文件已创建: config.ini")
        print("  请编辑config.ini并添加您的OpenAI API密钥")
    else:
        print("✓ 配置文件已存在")


def main():
    """主函数"""
    print("=" * 50)
    print("实时同声传译系统 - 自动安装脚本")
    print("=" * 50)
    
    # 检查Python版本
    if not check_python_version():
        sys.exit(1)
        
    # 安装系统依赖
    if not install_system_dependencies():
        print("\n系统依赖安装失败，但可以继续尝试安装Python依赖")
        
    # 安装Python依赖
    if not install_python_dependencies():
        print("\nPython依赖安装出现问题")
        
    # 检查安装
    if check_installation():
        print("\n✓ 所有依赖已成功安装！")
    else:
        print("\n✗ 部分依赖安装失败，请手动检查并安装")
        
    # 创建配置文件
    create_config_file()
    
    print("\n" + "=" * 50)
    print("安装完成！")
    print("\n下一步：")
    print("1. 编辑 config.ini 文件，添加您的OpenAI API密钥")
    print("2. 运行: python real_time_translator_v2.py")
    print("=" * 50)


if __name__ == "__main__":
    main()