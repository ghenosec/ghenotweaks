import tkinter as tk
from tkinter import messagebox, ttk
import subprocess
import ctypes
import sys
import os
import winreg
import shutil

def run_command(command, shell=False):
    try:
        subprocess.run(
            command,
            shell=shell,
            check=True,
            capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        return True, "Comando executado com sucesso!"
    except subprocess.CalledProcessError as e:
        error_message = e.stderr.decode("cp850", errors="ignore") if e.stderr else str(e)
        print(f"Erro ao executar '{command}': {error_message}")
        return False, error_message
    except Exception as e:
        print(f"Exceção ao executar '{command}': {e}")
        return False, str(e)

def create_restore_point():
    command = [
        "powershell",
        "-Command",
        'Checkpoint-Computer -Description "Ponto de Restauracao Otimizador" -RestorePointType "MODIFY_SETTINGS"',
    ]
    success, msg = run_command(command)
    if success:
        messagebox.showinfo("Sucesso", "Ponto de restauração criado com sucesso!")
    else:
        messagebox.showerror("Erro", f"Falha ao criar ponto de restauração:\n{msg}")

def clean_temp_files():
    response = messagebox.askyesno(
        "Confirmação",
        "Isso tentará deletar arquivos das pastas temporárias do sistema, do usuário e da pasta Prefetch. Alguns arquivos em uso podem não ser deletados.\n\nDeseja continuar?",
        icon='question'
    )
    if not response:
        return

    paths_to_clean = [
        os.environ.get('TEMP'),
        os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'Temp'),
        os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'Prefetch')
    ]
    
    deleted_files, deleted_folders, errors = 0, 0, 0

    for path in paths_to_clean:
        if not path or not os.path.exists(path):
            continue
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            try:
                if os.path.isfile(item_path) or os.path.islink(item_path):
                    os.unlink(item_path)
                    deleted_files += 1
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                    deleted_folders += 1
            except Exception as e:
                print(f"Não foi possível deletar {item_path}: {e}")
                errors += 1
    
    if errors > 0:
        messagebox.showwarning("Concluído com Avisos", f"Limpeza concluída.\n\nArquivos deletados: {deleted_files}\nPastas deletadas: {deleted_folders}\nErros (arquivos em uso): {errors}")
    else:
        messagebox.showinfo("Sucesso", f"Limpeza de arquivos temporários concluída!\n\nArquivos deletados: {deleted_files}\nPastas deletadas: {deleted_folders}")

def add_ultimate_power_plan():
    ULTIMATE_PERFORMANCE_GUID_TEMPLATE = "e9a42b02-d5df-448d-aa00-03f14749eb61"
    try:
        list_command = "powercfg /list"
        process = subprocess.run(list_command, shell=True, capture_output=True, text=True, encoding="cp850", creationflags=subprocess.CREATE_NO_WINDOW)
        
        guid_to_activate = None
        plan_name_pt = "desempenho máximo"
        plan_name_en = "ultimate performance"

        for line in process.stdout.lower().splitlines():
            if plan_name_pt in line or plan_name_en in line:
                guid_to_activate = line.split(":")[1].strip().split(" ")[0]
                break
        
        if not guid_to_activate:
            duplicate_command = f"powercfg -duplicatescheme {ULTIMATE_PERFORMANCE_GUID_TEMPLATE}"
            create_process = subprocess.run(
                duplicate_command, shell=True, capture_output=True, text=True, check=True, encoding="cp850",
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            output_line = create_process.stdout.strip()
            guid_to_activate = output_line.split(":")[1].strip().split(" ")[0]

        if guid_to_activate:
            activate_command = f"powercfg /setactive {guid_to_activate}"
            subprocess.run(activate_command, shell=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
            messagebox.showinfo("Sucesso", "Plano de energia 'Desempenho Máximo' foi ATIVADO com sucesso!")
        else:
            raise ValueError("Não foi possível encontrar ou criar o plano de energia.")

    except subprocess.CalledProcessError as e:
        error_text = (e.stderr or e.stdout).decode("cp850", errors="ignore")
        messagebox.showerror("Erro", f"Falha ao executar o comando powercfg.\n\nSeu sistema pode não suportar o plano 'Desempenho Máximo'.\n\nDetalhes: {error_text}")
    except (IndexError, ValueError) as e:
        messagebox.showerror("Erro", f"Falha ao processar a saída do comando:\n{e}")
    except Exception as e:
        messagebox.showerror("Erro", f"Ocorreu um erro inesperado:\n{str(e)}")

def find_nvidia_key_path():
    try:
        video_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Video")
        i = 0
        while True:
            try:
                device_guid = winreg.EnumKey(video_key, i)
                device_key_path = f"SYSTEM\\CurrentControlSet\\Control\\Video\\{device_guid}\\0000"
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, device_key_path) as sub_key:
                    provider, _ = winreg.QueryValueEx(sub_key, "ProviderName")
                    if "NVIDIA" in provider.upper():
                        winreg.CloseKey(video_key)
                        return f"HKLM\\{device_key_path}"
            except OSError:
                break
            i += 1
        winreg.CloseKey(video_key)
    except Exception as e:
        print(f"Erro ao procurar chave NVIDIA no registro: {e}")
    return None

def optimize_nvidia():
    response = messagebox.askyesno(
        "Aviso de Risco",
        "Esta função tentará modificar o registro para otimizar a NVIDIA automaticamente. É recomendado criar um ponto de restauração antes.\n\nDeseja continuar?",
        icon='warning'
    )
    if not response:
        return

    nvidia_key_path = find_nvidia_key_path()
    if not nvidia_key_path:
        messagebox.showerror("Erro", "Não foi possível encontrar o dispositivo NVIDIA no registro. A otimização automática foi cancelada.")
        return

    commands = [
        f'reg add "{nvidia_key_path}" /v PowerMizerEnable /t REG_DWORD /d 0 /f',
        f'reg add "{nvidia_key_path}" /v PerfLevelSrc /t REG_DWORD /d 8722 /f',
        f'reg add "{nvidia_key_path}" /v FxaaEnabled /t REG_DWORD /d 0 /f',
        f'reg add "{nvidia_key_path}" /v VSync /t REG_DWORD /d 0 /f',
    ]
    
    all_success = all(run_command(cmd, shell=True)[0] for cmd in commands)
    if all_success:
        messagebox.showinfo("Sucesso", "Otimizações de desempenho da NVIDIA foram aplicadas. É recomendado reiniciar o computador.")
    else:
        messagebox.showerror("Erro", "Falha ao aplicar uma ou mais otimizações da NVIDIA.")

def disable_background_apps():
    commands = [
        r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\BackgroundAccessApplications" /v GlobalUserDisabled /t REG_DWORD /d 1 /f',
        r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Privacy" /v TailoredExperiencesWithDiagnosticDataEnabled /t REG_DWORD /d 0 /f',
    ]
    all_success = all(run_command(cmd, shell=True)[0] for cmd in commands)
    if all_success:
        messagebox.showinfo("Sucesso", "A permissão para aplicativos rodarem em segundo plano foi desativada globalmente.")
    else:
        messagebox.showerror("Erro", "Não foi possível aplicar todas as otimizações de segundo plano.")

def configure_diagnostics():
    commands = [
        r'reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\DataCollection" /v AllowTelemetry /t REG_DWORD /d 1 /f',
        r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\Explorer" /v NoWindowsFeedback /t REG_DWORD /d 1 /f',
    ]
    all_success = all(run_command(cmd, shell=True)[0] for cmd in commands)
    if all_success:
        messagebox.showinfo("Sucesso", "Diagnósticos e comentários configurados para o mínimo.")
    else:
        messagebox.showerror("Erro", "Falha ao configurar diagnósticos.")

def disable_notifications_location():
    commands = [
        r'reg add "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\PushNotifications" /v ToastEnabled /t REG_DWORD /d 0 /f',
        r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\DeviceAccess\Global\{BFA794E4-F964-4FDB-90F6-51056BFE4B44}" /v Value /t REG_SZ /d "Deny" /f',
    ]
    all_success = all(run_command(cmd, shell=True)[0] for cmd in commands)
    if all_success:
        messagebox.showinfo("Sucesso", "Notificações e localização foram desativadas.")
    else:
        messagebox.showerror("Erro", "Falha ao desativar notificações ou localização.")

def configure_game_mode():
    commands = [
        r'reg add "HKCU\Software\Microsoft\GameBar" /v AllowAutoGameMode /t REG_DWORD /d 1 /f',
        r'reg add "HKCU\Software\Microsoft\GameBar" /v ShowGameBar /t REG_DWORD /d 0 /f',
        r'reg add "HKCU\SYSTEM\GameConfigStore" /v GameDVR_Enabled /t REG_DWORD /d 0 /f',
    ]
    all_success = all(run_command(cmd, shell=True)[0] for cmd in commands)
    if all_success:
        messagebox.showinfo("Sucesso", "Modo de Jogo ativado e Xbox Game Bar desativada.")
    else:
        messagebox.showerror("Erro", "Falha ao configurar o Modo de Jogo.")

def optimize_input_lag():
    commands = [
        r'reg add "HKEY_CURRENT_USER\Control Panel\Mouse" /v MouseSpeed /t REG_SZ /d "0" /f',
        r'reg add "HKEY_CURRENT_USER\Control Panel\Mouse" /v MouseThreshold1 /t REG_SZ /d "0" /f',
        r'reg add "HKEY_CURRENT_USER\Control Panel\Mouse" /v MouseThreshold2 /t REG_SZ /d "0" /f',
        r'reg add "HKEY_CURRENT_USER\Control Panel\Keyboard" /v KeyboardDelay /t REG_SZ /d "0" /f',
        r'reg add "HKEY_CURRENT_USER\Control Panel\Keyboard" /v KeyboardSpeed /t REG_SZ /d "31" /f',
        r'reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile" /v NetworkThrottlingIndex /t REG_DWORD /d 4294967295 /f',
        r'reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games" /v "GPU Priority" /t REG_DWORD /d 8 /f',
        r'reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games" /v Priority /t REG_DWORD /d 6 /f',
    ]
    all_success = all(run_command(cmd, shell=True)[0] for cmd in commands)
    if all_success:
        messagebox.showinfo("Sucesso", "Otimizações de teclado, mouse e sistema para baixo input lag foram aplicadas.")
    else:
        messagebox.showerror("Erro", "Falha ao aplicar otimizações de input lag.")

def create_gui():
    root = tk.Tk()
    root.title("Task Optimizer")
    root.geometry("450x650")
    root.resizable(False, False)

    style = ttk.Style()
    style.configure("TButton", padding=6, relief="flat", font=("Segoe UI", 10))
    style.configure("TLabel", font=("Segoe UI", 11))
    style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"))

    main_frame = ttk.Frame(root, padding="10 10 10 10")
    main_frame.pack(expand=True, fill="both")

    header_label = ttk.Label(main_frame, text="Painel de Otimização 🙉", style="Header.TLabel")
    header_label.pack(pady=(0, 20))

    buttons = [
        ("Criar Ponto de Restauração (Recomendado!)", create_restore_point),
        ("Limpar Arquivos Temporários", clean_temp_files),
        ("Adicionar e Ativar Plano 'Desempenho Máximo'", add_ultimate_power_plan),
        ("Otimizar NVIDIA para Desempenho (Automático)", optimize_nvidia),
        ("Otimizar Modo de Jogo e Xbox Game Bar", configure_game_mode),
        ("Otimizar Teclado e Mouse (Input Lag)", optimize_input_lag),
        ("Desativar Apps em Segundo Plano (Global)", disable_background_apps),
        ("Configurar Diagnósticos e Comentários", configure_diagnostics),
        ("Desativar Notificações e Localização", disable_notifications_location),
    ]

    for text, command in buttons:
        button = ttk.Button(main_frame, text=text, command=command)
        button.pack(fill="x", pady=5, ipady=5)

    footer_label = ttk.Label(
        main_frame,
        text="Execute como Administrador. Use por sua conta e risco.",
        font=("Segoe UI", 8),
    )
    footer_label.pack(side="bottom", pady=(20, 0))

    root.mainloop()

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if __name__ == "__main__":
    if is_admin():
        create_gui()
    else:
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )