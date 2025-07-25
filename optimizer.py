import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import ctypes
import sys
import os
import winreg
import shutil
import ttkbootstrap as ttkb
import webbrowser

def run_command(command, shell=False):
    try:
        subprocess.run(
            command, shell=shell, check=True, capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        return True, "Comando executado com sucesso!"
    except subprocess.CalledProcessError as e:
        error_message = e.stderr.decode("cp850", errors="ignore") if e.stderr else str(e)
        return False, error_message
    except Exception as e:
        return False, str(e)

def create_restore_point():
    command = [
        "powershell", "-Command",
        'Checkpoint-Computer -Description "GhenoTweaks Backup" -RestorePointType "MODIFY_SETTINGS"',
    ]
    success, msg = run_command(command)
    if success:
        messagebox.showinfo("Sucesso", "Ponto de restauração criado com sucesso!")
    else:
        messagebox.showerror("Erro", f"Falha ao criar ponto de restauração:\n{msg}")

def clean_temp_files():
    if not messagebox.askyesno("Confirmação", "Isso deletará arquivos temporários permanentemente. Deseja continuar?", icon='warning'):
        return
    paths = [
        os.environ.get('TEMP'),
        os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'Temp'),
        os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'Prefetch')
    ]
    deleted_files, deleted_folders, errors = 0, 0, 0
    for path in filter(None, paths):
        if not os.path.exists(path): continue
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            try:
                if os.path.isfile(item_path) or os.path.islink(item_path):
                    os.unlink(item_path); deleted_files += 1
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path); deleted_folders += 1
            except Exception as e:
                print(f"Não foi possível deletar {item_path}: {e}")
                errors += 1
    messagebox.showinfo("Concluído", f"Limpeza finalizada.\n\nArquivos/Pastas deletados: {deleted_files + deleted_folders}\nErros (arquivos em uso): {errors}")

def clean_windows_update_cache():
    if not messagebox.askyesno("Confirmação", "Isso irá limpar o cache do Windows Update. Deseja continuar?", icon='question'):
        return
    commands = ["net stop wuauserv", "net stop bits", r'rd /s /q "%windir%\SoftwareDistribution"', "net start wuauserv", "net start bits"]
    errors = []
    for cmd in commands:
        success, msg = run_command(cmd, shell=True)
        if not success and "não foi iniciado" not in msg.lower() and "not started" not in msg.lower():
            errors.append(msg)
    if not errors:
        messagebox.showinfo("Sucesso", "O cache do Windows Update foi limpo com sucesso!")
    else:
        messagebox.showwarning("Concluído com Avisos", "Processo concluído, mas ocorreram alguns erros (geralmente normais).")

def add_ultimate_power_plan():
    try:
        list_proc = subprocess.run("powercfg /list", shell=True, capture_output=True, text=True, encoding="cp850")
        guid_to_activate = next((line.split(":")[1].strip().split(" ")[0] for line in list_proc.stdout.lower().splitlines() if "desempenho máximo" in line or "ultimate performance" in line), None)
        if not guid_to_activate:
            dup_proc = subprocess.run("powercfg -duplicatescheme e9a42b02-d5df-448d-aa00-03f14749eb61", shell=True, capture_output=True, text=True, check=True, encoding="cp850")
            guid_to_activate = dup_proc.stdout.strip().split(":")[1].strip().split(" ")[0]
        run_command(f"powercfg /setactive {guid_to_activate}", shell=True)
        messagebox.showinfo("Sucesso", "Plano de energia 'Desempenho Máximo' ativado.")
    except Exception as e:
        messagebox.showerror("Erro", f"Falha ao configurar plano de energia: {e}")

def restore_power_plan():
    balanced_guid = "381b4222-f694-41f0-9685-ff5bb260df2e"
    success, _ = run_command(f"powercfg /setactive {balanced_guid}", shell=True)
    if success:
        messagebox.showinfo("Sucesso", "Plano de energia restaurado para 'Equilibrado'.")
    else:
        messagebox.showerror("Erro", "Falha ao restaurar o plano de energia.")

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
    if not messagebox.askyesno("Aviso de Risco", "Esta função tentará modificar o registro para otimizar a NVIDIA. Recomenda-se criar um ponto de restauração antes.\n\nDeseja continuar?", icon='warning'):
        return
    nvidia_key_path = find_nvidia_key_path()
    if not nvidia_key_path:
        messagebox.showerror("Erro", "Dispositivo NVIDIA não encontrado no registro."); return
    commands = [f'reg add "{nvidia_key_path}" /v {val} /t REG_DWORD /d {d_val} /f' for val, d_val in [("PowerMizerEnable", 0), ("PerfLevelSrc", 8722), ("FxaaEnabled", 0), ("VSync", 0)]]
    all_success = all(run_command(cmd, shell=True)[0] for cmd in commands)
    if all_success: messagebox.showinfo("Sucesso", "Otimizações da NVIDIA aplicadas. Reinicie para garantir o efeito.")
    else: messagebox.showerror("Erro", "Falha ao aplicar otimizações da NVIDIA.")

def restore_nvidia():
    messagebox.showinfo("Restauração NVIDIA", "A forma mais segura de restaurar as configurações da NVIDIA é abrir o 'Painel de Controle da NVIDIA', ir para 'Gerenciar as configurações em 3D' e clicar no botão 'Restaurar'.")

def configure_game_mode():
    commands = [r'reg add "HKCU\Software\Microsoft\GameBar" /v AllowAutoGameMode /t REG_DWORD /d 1 /f', r'reg add "HKCU\Software\Microsoft\GameBar" /v ShowGameBar /t REG_DWORD /d 0 /f', r'reg add "HKCU\SYSTEM\GameConfigStore" /v GameDVR_Enabled /t REG_DWORD /d 0 /f']
    if all(run_command(cmd, shell=True)[0] for cmd in commands): 
        messagebox.showinfo("Sucesso", "Modo de Jogo otimizado.")
    else:
        messagebox.showerror("Erro", "Falha ao otimizar o Modo de Jogo.")

def restore_game_mode():
    commands = [r'reg add "HKCU\Software\Microsoft\GameBar" /v AllowAutoGameMode /t REG_DWORD /d 1 /f', r'reg add "HKCU\Software\Microsoft\GameBar" /v ShowGameBar /t REG_DWORD /d 1 /f', r'reg add "HKCU\SYSTEM\GameConfigStore" /v GameDVR_Enabled /t REG_DWORD /d 1 /f']
    if all(run_command(cmd, shell=True)[0] for cmd in commands):
        messagebox.showinfo("Sucesso", "Modo de Jogo restaurado ao padrão.")
    else: 
        messagebox.showerror("Erro", "Falha ao restaurar o Modo de Jogo.")

def optimize_input_lag():
    commands = [r'reg add "HKEY_CURRENT_USER\Control Panel\Mouse" /v MouseSpeed /t REG_SZ /d "0" /f', r'reg add "HKEY_CURRENT_USER\Control Panel\Mouse" /v MouseThreshold1 /t REG_SZ /d "0" /f', r'reg add "HKEY_CURRENT_USER\Control Panel\Mouse" /v MouseThreshold2 /t REG_SZ /d "0" /f', r'reg add "HKEY_CURRENT_USER\Control Panel\Keyboard" /v KeyboardDelay /t REG_SZ /d "0" /f', r'reg add "HKEY_CURRENT_USER\Control Panel\Keyboard" /v KeyboardSpeed /t REG_SZ /d "31" /f', r'reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games" /v "GPU Priority" /t REG_DWORD /d 8 /f', r'reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games" /v Priority /t REG_DWORD /d 6 /f']
    if all(run_command(cmd, shell=True)[0] for cmd in commands): 
        messagebox.showinfo("Sucesso", "Otimizações de Input Lag aplicadas.")
    else:
        messagebox.showerror("Erro", "Falha ao aplicar otimizações de Input Lag.")

def restore_input_lag():
    commands = [r'reg add "HKEY_CURRENT_USER\Control Panel\Mouse" /v MouseSpeed /t REG_SZ /d "1" /f', r'reg add "HKEY_CURRENT_USER\Control Panel\Mouse" /v MouseThreshold1 /t REG_SZ /d "6" /f', r'reg add "HKEY_CURRENT_USER\Control Panel\Mouse" /v MouseThreshold2 /t REG_SZ /d "10" /f', r'reg add "HKEY_CURRENT_USER\Control Panel\Keyboard" /v KeyboardDelay /t REG_SZ /d "1" /f', r'reg add "HKEY_CURRENT_USER\Control Panel\Keyboard" /v KeyboardSpeed /t REG_SZ /d "31" /f', r'reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games" /v "GPU Priority" /t REG_DWORD /d 2 /f', r'reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games" /v Priority /t REG_DWORD /d 2 /f']
    if all(run_command(cmd, shell=True)[0] for cmd in commands): 
        messagebox.showinfo("Sucesso", "Configurações de Input Lag restauradas.")
    else: 
        messagebox.showerror("Erro", "Falha ao restaurar configurações de Input Lag.")

def disable_background_apps():
    command = r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\BackgroundAccessApplications" /v GlobalUserDisabled /t REG_DWORD /d 1 /f'
    if run_command(command, shell=True)[0]: 
        messagebox.showinfo("Sucesso", "Apps em segundo plano desativados.")
    else:
        messagebox.showerror("Erro", "Falha ao desativar apps em segundo plano.")

def restore_background_apps():
    command = r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\BackgroundAccessApplications" /v GlobalUserDisabled /t REG_DWORD /d 0 /f'
    if run_command(command, shell=True)[0]: 
        messagebox.showinfo("Sucesso", "Apps em segundo plano reativados.")
    else: 
        messagebox.showerror("Erro", "Falha ao reativar apps em segundo plano.")

def configure_diagnostics():
    command = r'reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\DataCollection" /v AllowTelemetry /t REG_DWORD /d 1 /f'
    if run_command(command, shell=True)[0]: 
        messagebox.showinfo("Sucesso", "Diagnósticos configurados para o mínimo.")
    else:
        messagebox.showerror("Erro", "Falha ao configurar diagnósticos.")

def restore_diagnostics():
    command = r'reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\DataCollection" /v AllowTelemetry /t REG_DWORD /d 3 /f'
    if run_command(command, shell=True)[0]: 
        messagebox.showinfo("Sucesso", "Diagnósticos restaurados ao padrão (Completo).")
    else: 
        messagebox.showerror("Erro", "Falha ao restaurar diagnósticos.")

def disable_notifications_location():
    commands = [r'reg add "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\PushNotifications" /v ToastEnabled /t REG_DWORD /d 0 /f', r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\DeviceAccess\Global\{BFA794E4-F964-4FDB-90F6-51056BFE4B44}" /v Value /t REG_SZ /d "Deny" /f']
    if all(run_command(cmd, shell=True)[0] for cmd in commands): 
        messagebox.showinfo("Sucesso", "Notificações e localização desativadas.")
    else: 
        messagebox.showerror("Erro", "Falha ao desativar notificações.")

def restore_notifications_location():
    commands = [r'reg add "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\PushNotifications" /v ToastEnabled /t REG_DWORD /d 1 /f', r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\DeviceAccess\Global\{BFA794E4-F964-4FDB-90F6-51056BFE4B44}" /v Value /t REG_SZ /d "Allow" /f']
    if all(run_command(cmd, shell=True)[0] for cmd in commands):
        messagebox.showinfo("Sucesso", "Notificações e localização reativadas.")
    else: 
        messagebox.showerror("Erro", "Falha ao reativar notificações.")

def apply_advanced_tweaks():
    if not messagebox.askyesno("Aviso de Risco", "Você está prestes a aplicar tweaks avançados de sistema que modificam profundamente o registro. Recomenda-se criar um ponto de restauração antes.\n\nDeseja continuar?", icon='warning'):
        return
    commands = [
        r'reg add "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Serialize" /v StartupDelayInMSec /t REG_DWORD /d 0 /f',
        r'reg add "HKLM\SYSTEM\CurrentControlSet\Control\Power\PowerThrottling" /v PowerThrottlingOff /t REG_DWORD /d 1 /f',
        r'reg add "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management\PrefetchParameters" /v EnablePrefetcher /t REG_DWORD /d 0 /f',
        r'reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile" /v NetworkThrottlingIndex /t REG_DWORD /d 4294967295 /f',
        r'reg add "HKCU\Control Panel\Desktop" /v MenuShowDelay /t REG_SZ /d "0" /f',
        r'reg add "HKCU\Control Panel\Desktop" /v AutoEndTasks /t REG_SZ /d "1" /f',
        r'reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games" /v "SFIO Priority" /t REG_SZ /d "High" /f'
    ]
    if all(run_command(cmd, shell=True)[0] for cmd in commands): messagebox.showinfo("Sucesso", "Tweaks avançados de sistema foram aplicados. Uma reinicialização é recomendada.")
    else: messagebox.showerror("Erro", "Falha ao aplicar um ou mais tweaks avançados.")

def restore_advanced_tweaks():
    commands = [
        r'reg delete "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Serialize" /v StartupDelayInMSec /f',
        r'reg delete "HKLM\SYSTEM\CurrentControlSet\Control\Power\PowerThrottling" /v PowerThrottlingOff /f',
        r'reg add "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management\PrefetchParameters" /v EnablePrefetcher /t REG_DWORD /d 3 /f',
        r'reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile" /v NetworkThrottlingIndex /t REG_DWORD /d 10 /f',
        r'reg add "HKCU\Control Panel\Desktop" /v MenuShowDelay /t REG_SZ /d "400" /f',
        r'reg add "HKCU\Control Panel\Desktop" /v AutoEndTasks /t REG_SZ /d "0" /f',
        r'reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games" /v "SFIO Priority" /t REG_SZ /d "Normal" /f'
    ]
    if all(run_command(cmd, shell=True)[0] for cmd in commands): messagebox.showinfo("Sucesso", "Tweaks avançados foram restaurados para o padrão do Windows.")
    else: messagebox.showerror("Erro", "Falha ao restaurar um ou mais tweaks avançados.")

def open_github_link(event):
    webbrowser.open_new_tab("https://github.com/ghenosec")

def create_gui():
    root = ttkb.Window(themename="vapor")
    root.title("Gheno Tweaks")
    root.geometry("550x550")
    root.resizable(False, False)
    
    try:
        root.iconbitmap('icone.ico')
    except tk.TclError:
        print("Aviso: Arquivo 'icone.ico' não encontrado. Usando ícone padrão.")

    main_frame = ttkb.Frame(root, padding=10)
    main_frame.pack(expand=True, fill="both")

    header = ttkb.Label(main_frame, text="Gheno Tweaks 🚀", font=("Segoe UI", 18, "bold"), bootstyle="primary")
    header.pack(pady=(0, 10))

    notebook = ttkb.Notebook(main_frame)
    notebook.pack(expand=True, fill="both", pady=5)

    tab_limpeza = ttkb.Frame(notebook, padding=10)
    tab_desempenho = ttkb.Frame(notebook, padding=10)
    tab_sistema = ttkb.Frame(notebook, padding=10)
    tab_restaurar = ttkb.Frame(notebook, padding=10)

    notebook.add(tab_limpeza, text='Limpeza')
    notebook.add(tab_desempenho, text='Desempenho')
    notebook.add(tab_sistema, text='Sistema')
    notebook.add(tab_restaurar, text='Restaurar Padrões')

    ttkb.Button(tab_limpeza, text="Criar Ponto de Restauração", command=create_restore_point, bootstyle="success").pack(fill="x", pady=4, ipady=4)
    ttkb.Button(tab_limpeza, text="Limpar Arquivos Temporários", command=clean_temp_files, bootstyle="danger").pack(fill="x", pady=4, ipady=4)
    ttkb.Button(tab_limpeza, text="Limpar Cache do Windows Update", command=clean_windows_update_cache, bootstyle="danger").pack(fill="x", pady=4, ipady=4)

    ttkb.Button(tab_desempenho, text="Ativar Plano 'Desempenho Máximo'", command=add_ultimate_power_plan, bootstyle="primary").pack(fill="x", pady=4, ipady=4)
    ttkb.Button(tab_desempenho, text="Otimizar NVIDIA (Automático)", command=optimize_nvidia, bootstyle="primary").pack(fill="x", pady=4, ipady=4)
    ttkb.Button(tab_desempenho, text="Otimizar Modo de Jogo e Game Bar", command=configure_game_mode, bootstyle="primary").pack(fill="x", pady=4, ipady=4)
    ttkb.Button(tab_desempenho, text="Otimizar Teclado e Mouse (Input Lag)", command=optimize_input_lag, bootstyle="primary").pack(fill="x", pady=4, ipady=4)
    ttkb.Button(tab_desempenho, text="Aplicar Tweaks Avançados de Sistema", command=apply_advanced_tweaks, bootstyle="primary").pack(fill="x", pady=4, ipady=4)
    
    ttkb.Button(tab_sistema, text="Desativar Apps em Segundo Plano", command=disable_background_apps, bootstyle="primary").pack(fill="x", pady=4, ipady=4)
    ttkb.Button(tab_sistema, text="Minimizar Diagnósticos e Comentários", command=configure_diagnostics, bootstyle="primary").pack(fill="x", pady=4, ipady=4)
    ttkb.Button(tab_sistema, text="Desativar Notificações e Localização", command=disable_notifications_location, bootstyle="primary").pack(fill="x", pady=4, ipady=4)

    ttkb.Button(tab_restaurar, text="Restaurar Plano de Energia (Equilibrado)", command=restore_power_plan, bootstyle="warning").pack(fill="x", pady=4, ipady=4)
    ttkb.Button(tab_restaurar, text="Restaurar Configurações NVIDIA", command=restore_nvidia, bootstyle="warning").pack(fill="x", pady=4, ipady=4)
    ttkb.Button(tab_restaurar, text="Restaurar Modo de Jogo e Game Bar", command=restore_game_mode, bootstyle="warning").pack(fill="x", pady=4, ipady=4)
    ttkb.Button(tab_restaurar, text="Restaurar Teclado e Mouse", command=restore_input_lag, bootstyle="warning").pack(fill="x", pady=4, ipady=4)
    ttkb.Button(tab_restaurar, text="Restaurar Tweaks Avançados", command=restore_advanced_tweaks, bootstyle="warning").pack(fill="x", pady=4, ipady=4)
    ttkb.Button(tab_restaurar, text="Restaurar Apps em Segundo Plano", command=restore_background_apps, bootstyle="warning").pack(fill="x", pady=4, ipady=4)
    ttkb.Button(tab_restaurar, text="Restaurar Diagnósticos", command=restore_diagnostics, bootstyle="warning").pack(fill="x", pady=4, ipady=4)
    ttkb.Button(tab_restaurar, text="Restaurar Notificações e Localização", command=restore_notifications_location, bootstyle="warning").pack(fill="x", pady=4, ipady=4)

    footer_frame = ttkb.Frame(main_frame)
    footer_frame.pack(side="bottom", fill="x", pady=(10, 0))

    copyright_label = ttkb.Label(
        footer_frame, 
        text="copyright @ghenosec", 
        font=("Segoe UI", 8), 
        bootstyle="primary",
        cursor="hand2"
    )
    copyright_label.pack(side="right")
    copyright_label.bind("<Button-1>", open_github_link)

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
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)