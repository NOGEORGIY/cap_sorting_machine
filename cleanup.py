# cleanup.py
import os
import signal
import psutil
import time

def cleanup():
    """Закрыть все процессы и подключения"""
    current_pid = os.getpid()
    
    # Находим все процессы Python
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] == 'python.exe' or proc.info['name'] == 'python':
                if proc.info['pid'] != current_pid:
                    # Проверяем, что это наш проект
                    cmdline = ' '.join(proc.info['cmdline'])
                    if 'capsSortFastAPI' in cmdline or 'CV_project' in cmdline:
                        print(f"🛑 Завершаем процесс PID: {proc.info['pid']}")
                        proc.terminate()
                        time.sleep(0.5)
                        if proc.is_running():
                            proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    print("✅ Все процессы завершены")

if __name__ == "__main__":
    cleanup()