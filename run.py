#!/usr/bin/env python3

import os
import subprocess
import multiprocessing
from prettytable import PrettyTable

here = os.path.dirname(os.path.realpath(__file__))
drives = os.path.join(here, "drives")

banner = """
                     ___  __    
  /\/\   __ _  ___  /___\/ _\   
 /    \ / _` |/ __|//  //\ \    
/ /\/\ \ (_| | (__/ \_// _\ \   
\/    \/\__,_|\___\___/  \__/   
Based on: https://github.com/foxlet/macOS-Simple-KVM

"""

releases = (
    ("High Sierra", "--high-sierra", "hs"),
    ("Mojave", "--mojave", "m"),
    ("Catalina", "--catalina", "c"),
)

def precheck():
    os.makedirs(drives, exist_ok=True)

def main():
    _clear_screen()
    print("Reminder! Run this container with a line similar to this: sudo docker run -it --name mac -v /tmp/.X11-unix/:/tmp/.X11-unix -e DISPLAY=$DISPLAY --network host --privileged --device /dev/kvm -v $HOME/.Xauthority/:/root/.Xauthority bannsec/macos-simple-kvm")

    precheck()
    #os.system("/bin/bash")

    main_menu()

def main_menu():

    while True:

        print(banner)

        for rel_name, rel_flag, s in releases:
            line = s + ") "

            if _is_release_init(rel_flag):
                line += "Start " + rel_name
            else:
                line += "Build " + rel_name

            print(line)

        print("q) Quit")

        selection = input("? ").lower()

        if selection == "q":
            return

        try:
            release = next(rel for rel in releases if rel[2] == selection)

        except StopIteration:
            print("Invalid selection.")
            continue

        release_menu(release)
        _clear_screen()

def release_menu(release):
    rel_name, rel_flag, rel_short = release

    if not _is_release_init(rel_flag):
        _download_release_base(rel_flag)
        subprocess.run(["qemu-img", "create", "-f", "qcow2", _rel_drive_path(rel_flag), "64G"], cwd=here)

    while True:

        _clear_screen()

        print(banner)
        print(rel_name)
        print("-"*len(rel_name))

        # Release info
        table = PrettyTable(["key", "value"])
        table.header = False
        table.border = False

        print(subprocess.check_output(["qemu-img", "snapshot", "-l", _rel_drive_path(rel_flag)], cwd=here).decode('latin-1').strip('\n'))
        print()

        options = (
                ("Run VM", "r", start_release),
                ("Snapshot Create", "sc", snapshot_create),
                ("Snapshot Delete", "sd", snapshot_delete),
                ("Snapshot Revert", "sr", snapshot_revert),
                ("Quit", "q", lambda x: exit()),
                )

        for option in options:
            print(option[1] + ") " + option[0])

        selection = input("? ").lower()

        try:
            next(option for option in options if option[1] == selection)[2](rel_flag)
        except StopIteration:
            print("Invalid selection.")

def snapshot_create(rel_flag):
    snap = input("Snapshot name? ")
    subprocess.check_output(["qemu-img", "snapshot", "-c", snap, _rel_drive_path(rel_flag)], cwd=here)

def snapshot_delete(rel_flag):
    snap = input("Snapshot name? ")
    subprocess.check_output(["qemu-img", "snapshot", "-d", snap, _rel_drive_path(rel_flag)], cwd=here)

def snapshot_revert(rel_flag):
    snap = input("Snapshot name? ")
    subprocess.check_output(["qemu-img", "snapshot", "-a", snap, _rel_drive_path(rel_flag)], cwd=here)

def start_release(rel_flag):

    firmware_dir = os.path.join(here, "firmware")

    qemu_cmd = [
        "qemu-system-x86_64",
        "-enable-kvm",
        "-m", "2G",
        "-machine", "q35,accel=kvm",
        "-smp", str(multiprocessing.cpu_count()),
        "-cpu", "Penryn,vendor=GenuineIntel,kvm=on,+sse3,+sse4.2,+aes,+xsave,+avx,+xsaveopt,+xsavec,+xgetbv1,+avx2,+bmi2,+smep,+bmi1,+fma,+movbe,+invtsc",
        "-device", "isa-applesmc,osk=ourhardworkbythesewordsguardedpleasedontsteal(c)AppleComputerInc",
        "-smbios", "type=2",
        "-drive", "if=pflash,format=raw,readonly,file={}".format(os.path.join(firmware_dir, "OVMF_CODE.fd")),
        "-drive", "if=pflash,format=raw,file={}".format(os.path.join(firmware_dir, "OVMF_VARS-1024x768.fd")),
        "-vga", "qxl",
        "-device", "ich9-intel-hda", "-device", "hda-output",
        "-usb", "-device", "usb-kbd", "-device", "usb-mouse",
        "-netdev", "user,id=net0",
        "-device", "e1000-82545em,netdev=net0,id=net0,mac=52:54:00:c2:28:27",
        "-device", "ich9-ahci,id=sata",
        "-drive", "id=ESP,if=none,format=qcow2,file=ESP.qcow2",
        "-device", "ide-hd,bus=sata.2,drive=ESP",
        "-drive", "id=InstallMedia,format=raw,if=none,file=BaseSystem.img",
        "-device", "ide-hd,bus=sata.3,drive=InstallMedia",
        "-drive", "id=SystemDisk,if=none,file={}".format(_rel_drive_path(rel_flag)),
        "-device", "ide-hd,bus=sata.4,drive=SystemDisk",
        "-monitor", "stdio",
    ]

    subprocess.run(qemu_cmd, cwd=here)
    input()

def _is_release_init(rel_flag): return os.path.exists(_rel_drive_path(rel_flag))
def _rel_drive_path(rel_flag): return os.path.join(drives, rel_flag.strip("-"))
def _clear_screen(): os.system('cls' if os.name == 'nt' else 'clear')
def _download_release_base(rel_flag): subprocess.run(["./jumpstart.sh", rel_flag], cwd=here)

if __name__ == "__main__":
    main()
