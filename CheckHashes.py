#!/usr/bin/env python
# coding: utf-8

# In[56]:


import tkinter, os
import tkinter.messagebox
from tkinter.filedialog import askopenfilename
import pyperclip, re
import hashlib 
import subprocess 
import threading
from tkinter.messagebox import showinfo

window = tkinter.Tk()
window.title("Compare hashes")
window.minsize(200, 200) 


file_labels =[]
clip_labels = []
script_labels = []

def hash_file(filename):
    BUF_SIZE = 65536  # read stuff in 64kb chunks
    hasher = hashlib.sha1()
    with open(filename, 'rb') as file:
        buf = file.read()
        while len(buf) > 0:
            hasher.update(buf)
            buf = file.read(BUF_SIZE)
            hasz = hasher.hexdigest()
            return hasz


def select_files():  
    file_path = askopenfilename(initialdir="./", title = "Choose a file.") 
    if file_path:
        hash_str = hash_file(file_path)
        file_name = file_path.split("/")[-1]

        add_label(topFrame, 0, file_labels, file_name, hash_str)

        if file_labels:
            button_choose.config(text=("Add another"))
    #print(hash_str)
    
def add_label(frame, col, labels_list, name, hashh):    
    labels_list.append(tkinter.Label(frame,text=name+"\n"+hashh))
    labels_list[-1].grid(column = col, row=len(labels_list))
    
def paste_clip():
    clip = pyperclip.paste()
    
    regex = re.compile(r"[A-Fa-f0-9]{40,}|[A-Za-z0-9]{40,}")
    
    for line in clip.splitlines():
        if regex.search(line):
            match = regex.search(line).group()  
            remaining_str = line.replace(match, "")
            add_label(topFrame, 1, clip_labels, remaining_str, match)
            
        else:
            showinfo("Warning","Hash not found in \n {}".format(line))

def script():
    a = subprocess.run('adb shell df -H /dev/block/mmcblk0p65', capture_output=True, shell=True, text = True)   

    if a.returncode != 0:
        label_script.config(text=(a.stderr)) 

    else:
        available_space = a.stdout.split()[next(i for i in reversed(range(len(a.stdout.split()))) if "G" in a.stdout.split()[i])]

        if int(available_space[:-1]) >= 4:
            subprocess.run('adb shell dd if=/dev/block/mmcblk0p12 of=/sdcard/boot_a count=65536 bs=1024', shell=True)
            subprocess.run('adb shell dd if=/dev/block/mmcblk0p14 of=/sdcard/system_a count=3145728 bs=1024', shell=True)
            subprocess.run('adb shell dd if=/dev/block/mmcblk0p16 of=/sdcard/vendor_a count=1048576 bs=1024', shell=True)

            boot = subprocess.run('adb shell sha256sum /sdcard/boot_a', capture_output=True, shell=True, text = True)
            system = subprocess.run('adb shell sha256sum /sdcard/system_a', capture_output=True, shell=True, text = True)
            vendor = subprocess.run('adb shell sha256sum /sdcard/vendor_a', capture_output=True, shell=True, text = True)

            rm = subprocess.run('adb shell rm /sdcard/boot_a /sdcard/system_a /sdcard/vendor_a', shell=True)

            if rm.returncode != 0:
                label_script.config(text=(rm.stderr))

            sha_boot = boot.stdout.split()[0]
            sha_system = system.stdout.split()[0]
            sha_vendor = vendor.stdout.split()[0]
    
            add_label(topFrame, 2, script_labels, "boot_a", sha_boot)
            add_label(topFrame, 2, script_labels, "system_a", sha_system)
            add_label(topFrame, 2, script_labels, "vendor_a", sha_vendor)
          
        else:
            label_script.config(text=("Not enough space, failed"))
                   
def run_script():
    label_script.config(text=("Please wait...")) 
    thread = threading.Thread(target = script)
    thread.start()
    
def reset():
    [flab.destroy() for flab in file_labels ]
    del file_labels[:]
    
    [clab.destroy() for clab in clip_labels ]
    del clip_labels[:]
    
    button_choose.config(text=("Chose file"))

    if label_script.cget("text") != "Please wait...":
        label_script.config(text=(""))
        [slab.destroy() for slab in script_labels ]        
        del script_labels[:]
    else:
        showinfo("Warning", "Script is still runing! Clear failed.")
        
def compare():
    all_labels = [*file_labels, *clip_labels, *script_labels]

    if len(all_labels) < 2:
        showinfo("Warning","No hashes to compare.")
        return 
    
    else: 
        hashes = [x.cget("text").split("\n")[-1] for x in all_labels]
        hashes_match = " ".join([x for n, x in enumerate(hashes) if x in hashes[:n]])

        for label in all_labels:
            if label.cget("text").split("\n")[-1] in hashes_match:
                label.config(fg="green")
            else:
                label.config(fg="red") 
                
topFrame = tkinter.Frame(window)
topFrame.pack()

label_script = tkinter.Label(topFrame) 
label_script.grid(column=2, row=1)

button_choose = tkinter.Button(topFrame, text ="Chose file", command = select_files)
button_choose.grid(column=0, row=0,  padx=(20, 10),pady=(10, 10))

button_clipboard = tkinter.Button(topFrame, text="Paste Clipboard", command = paste_clip)
button_clipboard.grid(column=1, row=0,  padx=(20, 10),pady=(10, 10))

button_script = tkinter.Button(topFrame, text="Run script", command = run_script)
button_script.grid(column=2, row=0,  padx=(20, 10),pady=(10, 10))

bottomFrame = tkinter.Frame(window)
bottomFrame.pack(side="bottom")

compare_button = tkinter.Button(bottomFrame, text ="Compare", command = compare, bg="SkyBlue3")
compare_button.grid(column=2, row=3,columnspan=2,padx=(100, 0), pady=(10, 10))

reset_button = tkinter.Button(bottomFrame, text ="Reset", command = reset, bg = "OrangeRed2")
reset_button.grid(column=0, row=3, padx = (10,0))

window.mainloop()

