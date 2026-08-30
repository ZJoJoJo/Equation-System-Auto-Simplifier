using System;
using System.Diagnostics;
using System.IO;
using System.Text;

namespace EquationSimplifierLauncher
{
    class Program
    {
        static void Main(string[] args)
        {
            string scriptDir = Path.GetDirectoryName(
                System.Reflection.Assembly.GetExecutingAssembly().Location
            );

            Console.WriteLine("========================================");
            Console.WriteLine("  方程组自动化简软件 - 启动器");
            Console.WriteLine("========================================");
            Console.WriteLine();
            Console.WriteLine("工作目录: " + scriptDir);
            Console.WriteLine();

            // 检查 app.py
            string appPy = Path.Combine(scriptDir, "app.py");
            if (!File.Exists(appPy))
            {
                Console.WriteLine("错误：未找到 app.py！");
                Console.WriteLine("请确保此启动器与软件文件在同一文件夹中。");
                Pause();
                return;
            }

            // 确保 .venv 虚拟环境存在且依赖完整
            Console.WriteLine("[环境检测] 正在检查运行环境...");
            string venvPython = EnsureVenv(scriptDir);
            if (venvPython == null)
            {
                Console.WriteLine();
                Console.WriteLine("错误：无法设置运行环境！");
                Console.WriteLine("请安装 Python 3.8+ 并勾选 'Add Python to PATH'，");
                Console.WriteLine("下载地址：https://www.python.org/downloads/");
                Pause();
                return;
            }
            Console.WriteLine("  运行环境就绪: " + venvPython);
            Console.WriteLine();

            // 启动参数
            string arguments = "app.py";
            if (args.Length > 0 && args[0] == "--web")
            {
                arguments = "app.py --web";
            }

            Console.WriteLine("[启动] 正在启动软件...");
            Console.WriteLine();

            try
            {
                ProcessStartInfo psi = new ProcessStartInfo();
                psi.FileName = venvPython;
                psi.Arguments = arguments;
                psi.WorkingDirectory = scriptDir;
                psi.UseShellExecute = false;
                psi.CreateNoWindow = false;

                Process proc = Process.Start(psi);
                if (proc != null)
                {
                    proc.WaitForExit();
                    if (proc.ExitCode != 0)
                    {
                        Console.WriteLine();
                        Console.WriteLine("程序异常退出，退出码: " + proc.ExitCode);
                        Pause();
                    }
                }
            }
            catch (Exception e)
            {
                Console.WriteLine("启动失败：" + e.Message);
                Pause();
            }
        }

        /// <summary>
        /// 确保 .venv 虚拟环境存在且依赖完整。
        /// 如果不存在，自动创建并安装依赖。
        /// 返回 .venv 中的 Python 路径，失败返回 null。
        /// </summary>
        static string EnsureVenv(string scriptDir)
        {
            string venvDir = Path.Combine(scriptDir, ".venv");
            string venvPython = Path.Combine(venvDir, "Scripts", "python.exe");

            // 情况1：.venv 存在且依赖完整 → 直接使用
            if (File.Exists(venvPython) && CheckDependencies(venvPython))
            {
                return venvPython;
            }

            // 情况2：.venv 存在但依赖缺失 → 安装依赖
            if (File.Exists(venvPython))
            {
                Console.WriteLine("  检测到虚拟环境，但依赖不完整，正在安装依赖...");
                if (InstallInVenv(venvPython, scriptDir))
                {
                    if (CheckDependencies(venvPython))
                    {
                        return venvPython;
                    }
                }
                Console.WriteLine("  依赖安装失败，尝试重建虚拟环境...");
            }

            // 情况3：.venv 不存在或重建 → 查找系统Python，创建.venv
            Console.WriteLine("  正在设置虚拟环境（首次运行需要，约1-2分钟）...");
            string systemPython = FindPython();
            if (systemPython == null)
            {
                Console.WriteLine("  未找到系统 Python！");
                return null;
            }
            Console.WriteLine("  使用系统 Python: " + systemPython);

            // 删除已损坏的 .venv
            if (Directory.Exists(venvDir))
            {
                try { Directory.Delete(venvDir, true); }
                catch { Console.WriteLine("  警告：无法删除旧虚拟环境，将继续尝试"); }
            }

            // 创建 .venv
            Console.WriteLine("  正在创建虚拟环境...");
            if (!CreateVenv(systemPython, venvDir))
            {
                Console.WriteLine("  创建虚拟环境失败！");
                return null;
            }

            if (!File.Exists(venvPython))
            {
                Console.WriteLine("  虚拟环境创建后未找到 python.exe！");
                return null;
            }

            // 安装依赖
            Console.WriteLine("  正在安装依赖库（flask, sympy, pywebview, waitress）...");
            if (!InstallInVenv(venvPython, scriptDir))
            {
                Console.WriteLine("  依赖安装失败！");
                return null;
            }

            // 验证
            if (!CheckDependencies(venvPython))
            {
                Console.WriteLine("  依赖验证失败！");
                return null;
            }

            Console.WriteLine("  虚拟环境设置完成！");
            return venvPython;
        }

        /// <summary>
        /// 用系统 Python 创建虚拟环境
        /// </summary>
        static bool CreateVenv(string systemPython, string venvDir)
        {
            try
            {
                ProcessStartInfo psi = new ProcessStartInfo();
                psi.FileName = systemPython;
                psi.Arguments = "-m venv \"" + venvDir + "\"";
                psi.UseShellExecute = false;
                psi.CreateNoWindow = true;
                psi.RedirectStandardOutput = true;
                psi.RedirectStandardError = true;

                Process p = Process.Start(psi);
                p.WaitForExit();
                return p.ExitCode == 0;
            }
            catch (Exception e)
            {
                Console.WriteLine("  创建虚拟环境出错: " + e.Message);
                return false;
            }
        }

        /// <summary>
        /// 在 .venv 中安装依赖（优先从 requirements.txt）
        /// </summary>
        static bool InstallInVenv(string venvPython, string scriptDir)
        {
            string requirements = Path.Combine(scriptDir, "requirements.txt");
            string args;
            if (File.Exists(requirements))
            {
                args = "-m pip install -r \"" + requirements + "\"";
            }
            else
            {
                args = "-m pip install flask sympy pywebview waitress";
            }

            try
            {
                ProcessStartInfo psi = new ProcessStartInfo();
                psi.FileName = venvPython;
                psi.Arguments = args;
                psi.UseShellExecute = false;
                psi.CreateNoWindow = false;

                Process p = Process.Start(psi);
                p.WaitForExit();
                return p.ExitCode == 0;
            }
            catch (Exception e)
            {
                Console.WriteLine("  安装依赖出错: " + e.Message);
                return false;
            }
        }

        /// <summary>
        /// 检测所有必需的依赖库是否可用
        /// </summary>
        static bool CheckDependencies(string pythonPath)
        {
            string checkScript = "import flask, sympy, webview, waitress; print('OK')";
            try
            {
                ProcessStartInfo psi = new ProcessStartInfo();
                psi.FileName = pythonPath;
                psi.Arguments = "-c \"" + checkScript + "\"";
                psi.UseShellExecute = false;
                psi.RedirectStandardOutput = true;
                psi.RedirectStandardError = true;
                psi.CreateNoWindow = true;

                Process p = Process.Start(psi);
                string output = p.StandardOutput.ReadToEnd();
                p.WaitForExit();
                return p.ExitCode == 0 && output.Contains("OK");
            }
            catch
            {
                return false;
            }
        }

        /// <summary>
        /// 查找系统中的 Python 可执行文件
        /// </summary>
        static string FindPython()
        {
            // 方法1：从 PATH 查找
            try
            {
                ProcessStartInfo psi = new ProcessStartInfo();
                psi.FileName = "where";
                psi.Arguments = "python";
                psi.UseShellExecute = false;
                psi.RedirectStandardOutput = true;
                psi.CreateNoWindow = true;
                Process p = Process.Start(psi);
                string output = p.StandardOutput.ReadToEnd();
                p.WaitForExit();
                string[] lines = output.Split(
                    new[] { '\r', '\n' },
                    StringSplitOptions.RemoveEmptyEntries
                );
                foreach (string line in lines)
                {
                    if (line.EndsWith(".exe", StringComparison.OrdinalIgnoreCase) && File.Exists(line))
                    {
                        // 跳过 .venv 中的 python（我们要找系统Python）
                        if (!line.Contains("\\.venv\\") && !line.Contains("/.venv/"))
                        {
                            return line;
                        }
                    }
                }
            }
            catch { }

            // 方法2：常见安装路径
            string[] commonPaths = new[]
            {
                Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                    "Programs\\Python\\Python313\\python.exe"),
                Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                    "Programs\\Python\\Python312\\python.exe"),
                Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                    "Programs\\Python\\Python311\\python.exe"),
                Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                    "Programs\\Python\\Python310\\python.exe"),
                "C:\\Python313\\python.exe",
                "C:\\Python312\\python.exe",
                "C:\\Python311\\python.exe",
                "C:\\Python310\\python.exe",
            };
            foreach (string p in commonPaths)
            {
                if (File.Exists(p)) return p;
            }

            return null;
        }

        static void Pause()
        {
            Console.WriteLine();
            Console.WriteLine("按任意键退出...");
            Console.ReadKey();
        }
    }
}
