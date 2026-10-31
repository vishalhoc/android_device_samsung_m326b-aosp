import os
import subprocess
import shutil

EARLY_SRC = """
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/mount.h>
#include <sys/wait.h>
#include <sys/syscall.h>
#include <linux/reboot.h>
#include <errno.h>

static void write_kmsg(const char *msg) {
    int fd = open("/dev/kmsg", O_WRONLY | O_NOCTTY);
    if (fd >= 0) {
        write(fd, msg, strlen(msg));
        close(fd);
    }
}

static void write_file(const char *path, const char *val) {
    int fd = open(path, O_WRONLY | O_CREAT | O_TRUNC, 0666);
    if (fd >= 0) {
        write(fd, val, strlen(val));
        close(fd);
    }
}

static void run_early_adb_and_watchdog(void) {
    // MediaTek USB driver pinning
    write_kmsg("[early_init] Pinning MTK USB controller to peripheral mode...\\n");
    write_file("/sys/class/udc/musb-hdrc/device/cmode", "3\\n");

    // ConfigFS USB Gadget Setup
    write_kmsg("[early_init] Configuring USB Gadget for Early ADB...\\n");
    mkdir("/config/usb_gadget", 0775);
    mkdir("/config/usb_gadget/g1", 0770);
    write_file("/config/usb_gadget/g1/idVendor", "0x04e8\\n");
    write_file("/config/usb_gadget/g1/idProduct", "0x6860\\n");
    write_file("/config/usb_gadget/g1/bcdDevice", "0x0400\\n");
    write_file("/config/usb_gadget/g1/bcdUSB", "0x0200\\n");

    mkdir("/config/usb_gadget/g1/strings/0x409", 0770);
    write_file("/config/usb_gadget/g1/strings/0x409/serialnumber", "RZCR904AE4Z\\n");
    write_file("/config/usb_gadget/g1/strings/0x409/manufacturer", "Samsung\\n");
    write_file("/config/usb_gadget/g1/strings/0x409/product", "Galaxy M32 5G\\n");

    mkdir("/config/usb_gadget/g1/functions/ffs.adb", 0770);
    mkdir("/config/usb_gadget/g1/configs/b.1", 0777);
    mkdir("/config/usb_gadget/g1/configs/b.1/strings/0x409", 0770);
    write_file("/config/usb_gadget/g1/configs/b.1/strings/0x409/configuration", "adb\\n");
    write_file("/config/usb_gadget/g1/configs/b.1/MaxPower", "500\\n");
    symlink("/config/usb_gadget/g1/functions/ffs.adb", "/config/usb_gadget/g1/configs/b.1/f1");

    mkdir("/dev/usb-ffs", 0775);
    mkdir("/dev/usb-ffs/adb", 0770);
    mount("adb", "/dev/usb-ffs/adb", "functionfs", 0, "uid=0,gid=0");

    // Launch adbd
    write_kmsg("[early_init] Starting static/early adbd...\\n");
    pid_t adbd_pid = fork();
    if (adbd_pid == 0) {
        char *argv[] = {"/system/bin/adbd", "--root_seclabel=u:r:su:s0", NULL};
        char *envp[] = {"PATH=/system/bin:/sbin", "LD_LIBRARY_PATH=/system/lib64", NULL};
        execve("/system/bin/adbd", argv, envp);
        _exit(1);
    }

    // Wait 500ms for adbd to initialize ep0, then bind to UDC
    usleep(500000);
    write_kmsg("[early_init] Binding UDC musb-hdrc to USB Gadget...\\n");
    write_file("/config/usb_gadget/g1/UDC", "musb-hdrc\\n");

    // Watchdog loop (90 seconds)
    write_kmsg("[early_init] Autonomous 90-second boot watchdog armed.\\n");
    int timeout = 90;
    int elapsed = 0;
    while (elapsed < timeout) {
        sleep(2);
        elapsed += 2;
        
        // Check sys.boot_completed
        int fd = open("/dev/__properties__/sys.boot_completed", O_RDONLY);
        if (fd >= 0) {
            close(fd);
        }
        // Also check via getprop
        FILE *fp = popen("/system/bin/getprop sys.boot_completed 2>/dev/null", "r");
        if (fp) {
            char val[16] = {0};
            if (fgets(val, sizeof(val), fp)) {
                if (val[0] == '1') {
                    pclose(fp);
                    write_kmsg("[early_init] Watchdog: sys.boot_completed=1 confirmed. Disarmed.\\n");
                    _exit(0);
                }
            }
            pclose(fp);
        }
    }

    write_kmsg("[early_init] Watchdog: 90s deadline reached! Auto-rebooting to TWRP Recovery...\\n");
    sync();
    // Reboot to recovery via kernel syscall
    syscall(__NR_reboot, LINUX_REBOOT_MAGIC1, LINUX_REBOOT_MAGIC2, LINUX_REBOOT_CMD_RESTART2, "recovery");
    sleep(3);
    // Sysrq force fallback
    write_file("/proc/sysrq-trigger", "b\\n");
    _exit(0);
}

int main(int argc, char **argv, char **envp) {
    // 1. Mount virtual filesystems needed for early userspace
    mkdir("/dev", 0755);
    mount("devtmpfs", "/dev", "devtmpfs", 0, NULL);
    mkdir("/dev/pts", 0755);
    mount("devpts", "/dev/pts", "devpts", 0, NULL);
    mkdir("/proc", 0755);
    mount("proc", "/proc", "proc", 0, NULL);
    mkdir("/sys", 0755);
    mount("sysfs", "/sys", "sysfs", 0, NULL);
    mkdir("/config", 0775);
    mount("none", "/config", "configfs", 0, NULL);

    write_kmsg("[early_init] DeepMind Antigravity Early Init Started (PID 1)\\n");

    // 2. Fork background daemon for early ADB and Watchdog
    pid_t pid = fork();
    if (pid == 0) {
        run_early_adb_and_watchdog();
        _exit(0);
    }

    // 3. Chainload real Android first-stage init
    write_kmsg("[early_init] Chainloading Android First-Stage /init.real...\\n");
    execve("/init.real", argv, envp);

    // If execve fails
    write_kmsg("[early_init] FATAL: Failed to execve /init.real!\\n");
    while (1) sleep(1000);
    return 0;
}
"""

with open("/tmp/early_init.c", "w") as f:
    f.write(EARLY_SRC)

print("Compiling static early_init binary...")
subprocess.run(["aarch64-linux-gnu-gcc", "-static", "-O2", "/tmp/early_init.c", "-o", "/tmp/early_init"], check=True)
res = subprocess.run(["file", "/tmp/early_init"], capture_output=True, text=True).stdout
print(res.strip())
