from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import os
import requests
from urllib.parse import urljoin
import subprocess
import sys

# 配置选项 - 用户可修改这里
DEFAULT_DOWNLOAD_DIR = "G:\\Python_Code\\Justice_Epstein_DataSet_DownloaderGUI"  # 默认下载根目录

# ==================== 方案1：版本检查函数 ====================
def check_chromedriver_version():
    """检查Chrome和ChromeDriver版本是否匹配"""
    try:
        print("=" * 60)
        print("ChromeDriver版本检查")
        print("=" * 60)
        
        # 获取Chrome浏览器版本
        chrome_version = None
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"D:\Program Files\Google\Chrome\Application\chrome.exe",
            r"D:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe")
        ]
        
        for path in chrome_paths:
            if os.path.exists(path):
                try:
                    result = subprocess.run([path, '--version'], capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        chrome_version = result.stdout.strip()
                        print(f"✓ 找到Chrome: {chrome_version}")
                        break
                except:
                    continue
        
        if not chrome_version:
            print("⚠️ 未找到Chrome浏览器，请确保已安装Google Chrome")
            return False
            
        # 提取版本号
        import re
        match = re.search(r'(\d+\.\d+\.\d+\.\d+)', chrome_version)
        if match:
            chrome_version_num = match.group(1)
            major_version = chrome_version_num.split('.')[0]
            print(f"Chrome主版本号: {major_version}")
            
            # 尝试检查ChromeDriver版本
            try:
                # 尝试创建临时driver来获取版本
                temp_options = Options()
                temp_options.add_argument('--headless')
                temp_options.add_argument('--disable-gpu')
                temp_options.add_argument('--no-sandbox')
                temp_options.add_argument('--disable-dev-shm-usage')
                
                driver = webdriver.Chrome(options=temp_options)
                driver_version = driver.capabilities['chrome']['chromedriverVersion'].split(' ')[0]
                print(f"当前ChromeDriver版本: {driver_version}")
                driver.quit()
                
                # 检查版本是否匹配
                driver_major_version = driver_version.split('.')[0]
                if driver_major_version != major_version:
                    print(f"❌ 版本不匹配: Chrome({major_version}) vs ChromeDriver({driver_major_version})")
                    print("\n解决方案:")
                    print("1. 自动方案: 程序将尝试使用webdriver-manager自动管理")
                    print("2. 手动方案: 下载对应版本的ChromeDriver")
                    print(f"   下载地址: https://chromedriver.chromium.org/downloads")
                    print(f"   查找版本: {major_version}.x.x.x")
                    print("\n按回车键继续...")
                    input()
                    return False
                else:
                    print("✓ Chrome和ChromeDriver版本匹配")
                    return True
            except Exception as e:
                print(f"检查ChromeDriver时出错: {e}")
                print("将尝试使用webdriver-manager自动管理...")
                return False
        else:
            print("无法解析Chrome版本号")
            return False
            
    except Exception as e:
        print(f"版本检查出错: {e}")
        return True  # 出错时继续尝试

# ==================== 方案2：智能驱动设置函数 ====================
def setup_driver(download_dir, retry_count=0):
    """
    智能设置Chrome驱动选项
    按优先级尝试：webdriver-manager → 直接创建 → 兼容模式
    """
    chrome_options = Options()
    
    # 通用兼容性选项
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # 禁用自动化控制提示
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # 设置下载路径
    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True,
        "profile.default_content_settings.popups": 0,
        "safebrowsing.enabled": True
    }
    chrome_options.add_experimental_option("prefs", prefs)
    
    # 创建下载目录（如果不存在）
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)
    
    # 根据重试次数选择不同的策略
    strategy = retry_count % 3  # 0, 1, 2 三种策略循环
    
    try:
        if strategy == 0:
            # 策略1：尝试webdriver-manager（如果可用）
            print("尝试策略1: 使用webdriver-manager自动管理...")
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                from selenium.webdriver.chrome.service import Service
                
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=chrome_options)
                print("✓ 策略1成功: 使用webdriver-manager")
                return driver
            except ImportError:
                print("webdriver-manager未安装，尝试策略2...")
                # 继续尝试策略2
        
        if strategy == 1:
            # 策略2：尝试直接创建（默认方式）
            print("尝试策略2: 直接创建Chrome驱动...")
            try:
                driver = webdriver.Chrome(options=chrome_options)
                print("✓ 策略2成功: 直接创建")
                return driver
            except Exception as e:
                print(f"策略2失败: {e}")
                # 继续尝试策略3
        
        # 策略3：尝试兼容模式（添加更多选项）
        print("尝试策略3: 兼容模式...")
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-software-rasterizer')
        chrome_options.add_argument('--disable-features=VizDisplayCompositor')
        chrome_options.add_argument('--log-level=3')
        chrome_options.add_argument('--silent')
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            print("✓ 策略3成功: 兼容模式")
            return driver
        except Exception as e:
            print(f"策略3失败: {e}")
            
            # 如果所有策略都失败，提供详细错误信息
            if retry_count < 2:  # 最多重试2次
                print(f"\n驱动创建失败，将在3秒后重试 (第{retry_count + 1}/3次)...")
                time.sleep(3)
                return setup_driver(download_dir, retry_count + 1)
            else:
                raise Exception("所有驱动创建策略都失败")
                
    except Exception as e:
        print(f"\n❌ Chrome驱动创建失败: {e}")
        print("\n请尝试以下解决方案:")
        print("1. 安装webdriver-manager: pip install webdriver-manager")
        print("2. 下载正确版本的ChromeDriver: https://chromedriver.chromium.org/")
        print("3. 确保Chrome浏览器已安装并更新到最新版本")
        print("4. 将chromedriver.exe放在:")
        print("   - Python安装目录 (如: D:\\Program Files\\Python310\\Scripts\\)")
        print("   - 或系统PATH中的任意目录")
        print("   - 或项目目录中")
        raise

# ==================== 方案3：增强的错误处理和重试 ====================
def safe_download_wrapper(func, *args, **kwargs):
    """安全下载包装器，提供重试机制"""
    max_retries = 3
    retry_delay = 5  # 秒
    
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"\n❌ 第{attempt + 1}次尝试失败: {e}")
            
            if attempt < max_retries - 1:
                print(f"等待{retry_delay}秒后重试...")
                time.sleep(retry_delay)
                
                # 如果是驱动相关错误，尝试重新创建驱动
                if "session not created" in str(e) or "ChromeDriver" in str(e):
                    print("检测到驱动问题，尝试重新创建驱动...")
                    # 这里可以添加重新创建驱动的逻辑
            else:
                print(f"❌ 所有{max_retries}次尝试都失败")
                raise



def setup_driver(download_dir):
    """设置Chrome驱动选项"""
    chrome_options = Options()
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    # 设置下载路径 - 确保路径存在
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)
        print(f"已创建下载目录: {download_dir}")
    
    # 将路径转换为绝对路径
    download_dir = os.path.abspath(download_dir)
    
    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True,
        "profile.default_content_settings.popups": 0,
        "safebrowsing.enabled": True,
        "safebrowsing.disable_download_protection": True
    }
    chrome_options.add_experimental_option("prefs", prefs)
    
    # 添加额外的选项确保下载到指定目录
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=chrome_options)
    
    # 设置页面加载超时和脚本超时
    driver.set_page_load_timeout(30)  # 页面加载超时30秒
    driver.set_script_timeout(30)     # 脚本执行超时30秒
    
    return driver

def perform_age_verification(driver, max_retries=3):
    """执行年龄验证，带重试机制"""
    for attempt in range(max_retries):
        try:
            print(f"访问年龄验证页面 (尝试 {attempt + 1}/{max_retries})...")
            
            # 设置页面加载超时
            driver.set_page_load_timeout(30)
            
            driver.get("https://www.justice.gov/age-verify")
            time.sleep(3)
            
            # 防御性检查：确保current_url不为None
            current_url = driver.current_url
            if current_url is None:
                print(f"尝试 {attempt + 1}: driver.current_url 为 None")
                if attempt < max_retries - 1:
                    print("等待2秒后重试...")
                    time.sleep(2)
                    continue
                else:
                    print("所有重试都失败，返回空cookies")
                    return []
            
            # 检查是否已经在年龄验证页面
            if "age-verify" in current_url:
                print(f"尝试 {attempt + 1}: 点击Yes按钮...")
                try:
                    yes_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.ID, "age-button-yes"))
                    )
                    yes_button.click()
                    time.sleep(3)
                    print("年龄验证完成")
                    
                    # 获取cookies
                    cookies = driver.get_cookies()
                    return cookies
                    
                except Exception as e:
                    print(f"尝试 {attempt + 1}: 点击Yes按钮失败: {e}")
                    if attempt < max_retries - 1:
                        print("等待2秒后重试...")
                        time.sleep(2)
                        continue
                    else:
                        print("所有重试都失败，返回空cookies")
                        return []
            else:
                print(f"尝试 {attempt + 1}: 已通过年龄验证或不在验证页面")
                # 获取当前cookies
                cookies = driver.get_cookies()
                return cookies
                
        except Exception as e:
            print(f"尝试 {attempt + 1}: 访问年龄验证页面失败: {e}")
            if attempt < max_retries - 1:
                print("等待2秒后重试...")
                time.sleep(2)
                continue
            else:
                print("所有重试都失败，返回空cookies")
                return []
    
    # 如果所有重试都失败
    return []


def perform_age_verification_old1(driver, max_retries=3):
    """执行年龄验证"""
    print("访问年龄验证页面...")
    
    try:
        driver.get("https://www.justice.gov/age-verify")
        time.sleep(3)
    except Exception as e:
        print(f"访问年龄验证页面失败: {e}")
        # 返回空cookies列表，让后续逻辑处理
        return []
    
    # 防御性检查：确保current_url不为None
    current_url = driver.current_url
    if current_url is None:
        print("警告: driver.current_url 为 None，可能页面加载失败")
        # 尝试重新加载页面
        try:
            driver.refresh()
            time.sleep(3)
            current_url = driver.current_url
            if current_url is None:
                print("页面重新加载后仍然失败，返回空cookies")
                return []
        except Exception as e:
            print(f"重新加载页面失败: {e}")
            return []
    
    # 检查是否已经在年龄验证页面
    if current_url and "age-verify" in current_url:

        try:
            yes_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "age-button-yes"))
            )
            yes_button.click()
            time.sleep(3)
            print("年龄验证完成")
        except Exception as e:
            print(f"点击Yes按钮失败: {e}")
    else:
        print("已通过年龄验证或不在验证页面")
    
    return driver.get_cookies()

def download_dataset(driver, dataset_name, base_url, start_num, end_num, file_prefix, download_dir=None):
    """下载指定数据集"""
    # 获取cookies
    cookies = perform_age_verification(driver)
    
    # 防御性检查：确保cookies不为None
    if cookies is None:
        print("警告: 获取到的cookies为None，使用空列表")
        cookies = []
    
    print(f"获取到 {len(cookies)} 个cookies")
    
    # 创建requests会话并添加cookies
    session = requests.Session()
    if cookies:
        for cookie in cookies:
            # 确保cookie是字典类型且有必要的键
            if isinstance(cookie, dict) and 'name' in cookie and 'value' in cookie:
                session.cookies.set(cookie['name'], cookie['value'])
            else:
                print(f"警告: 跳过无效的cookie: {cookie}")
    else:
        print("警告: 没有获取到有效的cookies，可能影响下载")

    
    # 设置请求头
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/pdf,text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache'
    }
    
    # 获取下载目录 - 从Chrome选项的prefs中获取
    if download_dir is None:
        try:
            # 尝试从driver的prefs中获取下载目录
            prefs = driver.capabilities.get('chrome', {}).get('userDataDir', {})
            # 或者从Chrome选项获取
            chrome_options = driver.capabilities.get('chromeOptions', {})
            if 'prefs' in chrome_options and 'download.default_directory' in chrome_options['prefs']:
                download_dir = chrome_options['prefs']['download.default_directory']
            else:
                # 如果无法获取，使用当前目录下的dataset目录
                download_dir = os.path.join(os.getcwd(), "dataset")
        except:
            # 如果获取失败，使用当前目录下的dataset目录
            download_dir = os.path.join(os.getcwd(), "dataset")
    
    # 创建下载目录（如果不存在）
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)
        print(f"已创建下载目录: {download_dir}")
    
    total_files = end_num - start_num + 1
    downloaded_count = 0
    failed_count = 0
    
    print(f"\n开始下载 {dataset_name}")
    print(f"文件范围: {start_num} 到 {end_num}")
    print(f"总计 {total_files} 个文件")
    print(f"下载目录: {download_dir}")
    print("-" * 50)
    
    for num in range(start_num, end_num + 1):
        # 生成文件名
        file_num = f"{num}"  # 直接使用数字，不格式化位数
        pdf_filename = f"{file_prefix}{file_num}.pdf"
        pdf_url = f"{base_url}{pdf_filename}"
        
        current_num = num - start_num + 1
        print(f"正在下载 ({current_num}/{total_files}): {pdf_filename}")
        
        try:
            # 使用requests库下载
            response = session.get(pdf_url, headers=headers, timeout=30)
            
            # 检查响应状态码
            if response.status_code == 200:
                # 检查内容类型
                content_type = response.headers.get('content-type', '').lower()
                
                if 'pdf' in content_type or '%pdf' in response.text[:100].lower():
                    # 保存PDF文件 - 确保使用正确的下载目录
                    file_path = os.path.join(download_dir, pdf_filename)
                    with open(file_path, 'wb') as f:
                        f.write(response.content)
                    print(f"✓ 文件保存到: {file_path}")
                    downloaded_count += 1
                    print(f"✓ 成功下载: {pdf_filename} ({len(response.content)} bytes)")
                else:
                    # 检查是否为HTML页面（可能是验证页面）
                    if '<html' in response.text[:100].lower():
                        print(f"✗ 可能遇到验证页面: {pdf_filename}")
                        
                        # 尝试使用Selenium再次验证
                        print("尝试使用Selenium重新验证...")
                        driver.get(pdf_url)
                        time.sleep(2)
                        
                        # 检查是否在年龄验证页面
                        if "age-verify" in driver.current_url:
                            try:
                                yes_button = WebDriverWait(driver, 5).until(
                                    EC.element_to_be_clickable((By.ID, "age-button-yes"))
                                )
                                yes_button.click()
                                time.sleep(3)
                                
                                # 重新获取cookies
                                cookies = driver.get_cookies()
                                for cookie in cookies:
                                    session.cookies.set(cookie['name'], cookie['value'])
                                print("重新验证成功")
                                
                                # 再次尝试下载
                                response = session.get(pdf_url, headers=headers, timeout=30)
                                if response.status_code == 200 and ('pdf' in response.headers.get('content-type', '').lower() or '%pdf' in response.text[:100].lower()):
                                    file_path = os.path.join(download_dir, pdf_filename)
                                    with open(file_path, 'wb') as f:
                                        f.write(response.content)
                                    downloaded_count += 1
                                    print(f"✓ 重新验证后成功下载: {pdf_filename}")
                                else:
                                    failed_count += 1
                                    print(f"✗ 重新验证后仍然失败: {pdf_filename}")
                            except:
                                failed_count += 1
                                print(f"✗ 无法重新验证: {pdf_filename}")
                    else:
                        failed_count += 1
                        print(f"✗ 不是PDF文件: {pdf_filename} (Content-Type: {content_type})")
                        
            elif response.status_code == 404:
                failed_count += 1
                print(f"✗ 文件不存在: {pdf_filename}")
            else:
                failed_count += 1
                print(f"✗ 下载失败，状态码: {response.status_code}")
                
            # 下载间隔
            time.sleep(0.5)
            
        except Exception as e:
            failed_count += 1
            print(f"✗ 下载 {pdf_filename} 时发生错误: {e}")
            continue
    
    print("-" * 50)
    print(f"下载完成!")
    print(f"成功: {downloaded_count}, 失败: {failed_count}, 总计: {total_files}")

def download_data9():
    """下载DataSet 9"""
    download_dir = os.path.join(DEFAULT_DOWNLOAD_DIR, "DataSet9")
    print(f"DataSet 9 下载目录: {download_dir}")
    
    try:
        driver = setup_driver(download_dir)
        
        # DataSet 9配置
        base_url = "https://www.justice.gov/epstein/files/DataSet%209/"
        start_num = 25
        end_num = 882
        file_prefix = "EFTA00039"
        
        download_dataset(driver, "DataSet 9", base_url, start_num, end_num, file_prefix, download_dir)
        
    except Exception as e:
        print(f"发生全局错误: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if 'driver' in locals():
            driver.quit()

def download_data10():
    """下载DataSet 10"""
    download_dir = os.path.join(DEFAULT_DOWNLOAD_DIR, "DataSet10")
    print(f"DataSet 10 下载目录: {download_dir}")
    
    try:
        driver = setup_driver(download_dir)
        
        # DataSet 10配置
        base_url = "https://www.justice.gov/epstein/files/DataSet%2010/"
        start_num = 1262782
        end_num = 1056784
        file_prefix = "EFTA"
        
        # 注意：DataSet 10是从大到小的范围，所以需要调整
        if start_num > end_num:
            start_num, end_num = end_num, start_num
        
        download_dataset(driver, "DataSet 10", base_url, start_num, end_num, file_prefix)
        
    except Exception as e:
        print(f"发生全局错误: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if 'driver' in locals():
            driver.quit()

def download_data11():
    """下载DataSet 11"""
    download_dir = os.path.join(DEFAULT_DOWNLOAD_DIR, "DataSet11")
    print(f"DataSet 11 下载目录: {download_dir}")
    
    try:
        driver = setup_driver(download_dir)
        
        # DataSet 11配置
        base_url = "https://www.justice.gov/epstein/files/DataSet%2011/"
        start_num = 2205655
        end_num = 2730262
        file_prefix = "EFTA0"
        
        download_dataset(driver, "DataSet 11", base_url, start_num, end_num, file_prefix)
        
    except Exception as e:
        print(f"发生全局错误: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if 'driver' in locals():
            driver.quit()

def show_menu():
    """显示菜单"""
    print("=" * 60)
    print("PDF批量下载器 - 司法部Epstein文件下载")
    print("=" * 60)
    print("1. 下载 DataSet 9")
    print("   - 文件范围: EFTA00039025.pdf 到 EFTA00039882.pdf")
    print("   - 总计: 857 个文件")
    print()
    print("2. 下载 DataSet 10")
    print("   - 文件范围: EFTA01262782.pdf 到 EFTA01056784.pdf")
    print("   - 总计: 206,999 个文件 (注意：范围从大到小，需要确认实际有效范围)")
    print()
    print("3. 下载 DataSet 11")
    print("   - 文件范围: EFTA02205655.pdf 到 EFTA02730262.pdf")
    print("   - 总计: 524,608 个文件")
    print()
    print("4. 自定义下载 DataSet 9/10/11 (可指定开始和结束数字)")
    print("5. 完全自定义下载 (指定前缀、开始值、结束值)")
    print("6. 退出程序")
    print("=" * 60)

def download_fully_custom():
    """完全自定义下载"""
    print("\n" + "=" * 60)
    print("完全自定义下载")
    print("=" * 60)
    
    # 获取下载目录
    download_dir = input("请输入下载目录路径 (直接回车使用当前目录): ").strip()
    if not download_dir:
        download_dir = os.getcwd()
    
    # 创建下载目录（如果不存在）
    if not os.path.exists(download_dir):
        try:
            os.makedirs(download_dir)
            print(f"已创建目录: {download_dir}")
        except Exception as e:
            print(f"创建目录失败: {e}")
            return
    
    # 获取基础URL
    base_url = input("请输入基础URL (例如: https://www.justice.gov/epstein/files/DataSet%209/): ").strip()
    if not base_url:
        print("错误: 必须提供基础URL")
        return
    
    # 确保URL以斜杠结尾
    if not base_url.endswith('/'):
        base_url += '/'
    
    # 获取文件前缀
    file_prefix = input("请输入文件前缀 (例如: EFTA00039): ").strip()
    if not file_prefix:
        print("错误: 必须提供文件前缀")
        return
    
    # 获取开始数字
    while True:
        start_input = input("请输入开始数字: ").strip()
        if start_input:
            try:
                start_num = int(start_input)
                break
            except ValueError:
                print("错误: 请输入有效的数字")
        else:
            print("错误: 必须提供开始数字")
    
    # 获取结束数字
    while True:
        end_input = input("请输入结束数字: ").strip()
        if end_input:
            try:
                end_num = int(end_input)
                break
            except ValueError:
                print("错误: 请输入有效的数字")
        else:
            print("错误: 必须提供结束数字")
    
    # 验证范围
    if start_num > end_num:
        print(f"注意: 开始数字 {start_num} 大于结束数字 {end_num}，自动交换")
        start_num, end_num = end_num, start_num
    
    total_files = end_num - start_num + 1
    print(f"\n下载配置:")
    print(f"下载目录: {download_dir}")
    print(f"基础URL: {base_url}")
    print(f"文件范围: {file_prefix}{start_num}.pdf 到 {file_prefix}{end_num}.pdf")
    print(f"总计: {total_files} 个文件")
    
    # 确认下载
    if total_files > 1000:
        confirm = input(f"警告: 将下载 {total_files} 个文件，可能需要很长时间。确定继续吗? (y/n): ").strip().lower()
        if confirm != 'y':
            print("已取消下载")
            return
    else:
        confirm = input("确定开始下载吗? (y/n): ").strip().lower()
        if confirm != 'y':
            print("已取消下载")
            return
    
    # 设置驱动并下载
    # driver = setup_driver(download_dir)
    
    try:
        driver = setup_driver(download_dir)
        download_dataset(driver, "自定义数据集", base_url, 
                        start_num, end_num, file_prefix)
    except Exception as e:
        print(f"发生全局错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'driver' in locals():
            driver.quit()


def download_dataset_custom(dataset_choice):
    """下载指定数据集，支持自定义开始和结束数字"""
    
    # 数据集配置
    datasets = {
        '9': {
            'name': 'DataSet 9',
            'base_url': 'https://www.justice.gov/epstein/files/DataSet%209/',
            'default_start': 25,
            'default_end': 882,
            'file_prefix': 'EFTA00039',
            'download_dir': os.path.join(DEFAULT_DOWNLOAD_DIR, 'DataSet9')
        },
        '10': {
            'name': 'DataSet 10',
            'base_url': 'https://www.justice.gov/epstein/files/DataSet%2010/',
            'default_start': 1056784,  # 注意：这里已经调整为从小到大
            'default_end': 1262782,
            'file_prefix': 'EFTA',
            'download_dir': os.path.join(DEFAULT_DOWNLOAD_DIR, 'DataSet10')
        },
        '11': {
            'name': 'DataSet 11',
            'base_url': 'https://www.justice.gov/epstein/files/DataSet%2011/',
            'default_start': 2205655,
            'default_end': 2730262,
            'file_prefix': 'EFTA0',
            'download_dir': os.path.join(DEFAULT_DOWNLOAD_DIR, 'DataSet11')
        }
    }
    
    if dataset_choice not in datasets:
        print(f"错误: 不支持的数据集 {dataset_choice}")
        return
    
    config = datasets[dataset_choice]
    
    print(f"\n配置 {config['name']}")
    print(f"默认范围: {config['default_start']} 到 {config['default_end']}")
    print(f"文件前缀: {config['file_prefix']}")
    print(f"下载目录: {config['download_dir']}")
    print("-" * 50)
    
    # 获取自定义的开始数字
    start_input = input(f"请输入开始数字 (直接回车使用默认值 {config['default_start']}): ").strip()
    if start_input:
        try:
            start_num = int(start_input)
        except ValueError:
            print(f"输入无效，使用默认值 {config['default_start']}")
            start_num = config['default_start']
    else:
        start_num = config['default_start']
    
    # 获取自定义的结束数字
    end_input = input(f"请输入结束数字 (直接回车使用默认值 {config['default_end']}): ").strip()
    if end_input:
        try:
            end_num = int(end_input)
        except ValueError:
            print(f"输入无效，使用默认值 {config['default_end']}")
            end_num = config['default_end']
    else:
        end_num = config['default_end']
    
    # 验证范围
    if start_num > end_num:
        print(f"注意: 开始数字 {start_num} 大于结束数字 {end_num}，自动交换")
        start_num, end_num = end_num, start_num
    
    total_files = end_num - start_num + 1
    print(f"\n下载配置:")
    print(f"数据集: {config['name']}")
    print(f"文件范围: {config['file_prefix']}{start_num}.pdf 到 {config['file_prefix']}{end_num}.pdf")
    print(f"下载目录: {config['download_dir']}")
    print(f"总计: {total_files} 个文件")
    
    # 确认下载
    if total_files > 1000:
        confirm = input(f"警告: 将下载 {total_files} 个文件，可能需要很长时间。确定继续吗? (y/n): ").strip().lower()
        if confirm != 'y':
            print("已取消下载")
            return
    else:
        confirm = input("确定开始下载吗? (y/n): ").strip().lower()
        if confirm != 'y':
            print("已取消下载")
            return
    
    # 设置驱动并下载
    # driver = setup_driver(config['download_dir'])
    
    try:
        driver = setup_driver(config['download_dir'])
        download_dataset(driver, config['name'], config['base_url'], 
                        start_num, end_num, config['file_prefix'])
    except Exception as e:
        print(f"发生全局错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'driver' in locals():
            driver.quit()


def main():
    """主函数"""
    print("=" * 60)
    print("PDF批量下载器 - 司法部Epstein文件下载")
    print("智能驱动管理版本")
    print("=" * 60)
    
    # 检查ChromeDriver版本（非阻塞，仅提供信息）
    try:
        check_chromedriver_version()
    except:
        print("版本检查跳过，继续运行...")
    
    # 询问是否安装webdriver-manager
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        print("✓ webdriver-manager已安装")
    except ImportError:
        print("\n⚠️ webdriver-manager未安装")
        print("建议安装以获得更好的驱动兼容性")
        install_choice = input("是否现在安装webdriver-manager? (y/n): ").strip().lower()
        if install_choice == 'y':
            try:
                import subprocess
                subprocess.check_call([sys.executable, "-m", "pip", "install", "webdriver-manager"])
                print("✓ webdriver-manager安装成功")
                print("请重新启动程序")
                input("按回车键退出...")
                return
            except Exception as e:
                print(f"安装失败: {e}")
                print("将继续使用现有驱动")
    
    while True:
        show_menu()
        choice = input("请选择要下载的数据集 (1-6): ").strip()
        
        try:
            if choice == '1':
                print("\n开始下载 DataSet 9...")
                download_data9()
            elif choice == '2':
                print("\n开始下载 DataSet 10...")
                # 注意：DataSet 10的文件范围非常大，可能需要很长时间
                confirm = input("DataSet 10包含大量文件，下载可能需要很长时间。确定继续吗? (y/n): ").strip().lower()
                if confirm == 'y':
                    download_data10()
                else:
                    print("已取消下载DataSet 10")
            elif choice == '3':
                print("\n开始下载 DataSet 11...")
                # 注意：DataSet 11的文件范围也非常大
                confirm = input("DataSet 11包含大量文件，下载可能需要很长时间。确定继续吗? (y/n): ").strip().lower()
                if confirm == 'y':
                    download_data11()
                else:
                    print("已取消下载DataSet 11")
            elif choice == '4':
                print("\n自定义下载 DataSet 9/10/11")
                print("1. DataSet 9")
                print("2. DataSet 10")
                print("3. DataSet 11")
                dataset_choice = input("请选择数据集 (1-3): ").strip()
                
                if dataset_choice == '1':
                    download_dataset_custom('9')
                elif dataset_choice == '2':
                    download_dataset_custom('10')
                elif dataset_choice == '3':
                    download_dataset_custom('11')
                else:
                    print("无效选择")
            elif choice == '5':
                download_fully_custom()
            elif choice == '6':
                print("感谢使用，再见!")
                break
            else:
                print("无效选择，请重新输入!")
            
            # 询问是否继续
            if choice in ['1', '2', '3', '4', '5']:
                continue_choice = input("\n是否继续下载其他数据集? (y/n): ").strip().lower()
                if continue_choice != 'y':
                    print("感谢使用，再见!")
                    break
            print()
            
        except Exception as e:
            print(f"\n❌ 发生错误: {e}")
            print("\n错误处理建议:")
            print("1. 检查网络连接")
            print("2. 确保Chrome浏览器已安装")
            print("3. 尝试安装webdriver-manager: pip install webdriver-manager")
            print("4. 重启程序")
            
            retry = input("\n是否重试当前操作? (y/n): ").strip().lower()
            if retry != 'y':
                continue_choice = input("是否继续其他操作? (y/n): ").strip().lower()
                if continue_choice != 'y':
                    print("感谢使用，再见!")
                    break


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
    except Exception as e:
        print(f"\n❌ 程序发生未捕获的异常: {e}")
        import traceback
        traceback.print_exc()
        input("\n按回车键退出...")
