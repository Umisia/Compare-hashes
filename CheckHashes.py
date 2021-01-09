import tkinter, os
import tkinter.messagebox
from tkinter.filedialog import askopenfilename
import pyperclip, re
import hashlib 
import subprocess 
import threading
import time, sys
from tkinter.messagebox import showinfo
import os
import signal
import subprocess
import multiprocessing 
import time 

window = tkinter.Tk()
window.title("Compare hashes")
window.minsize(300, 200) 

thread = None

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
  
    
def add_label(frame, col, labels_list, name, hashh="", end="no"):    
    labels_list.append(tkinter.Label(frame,text=name+"\n"+hashh))
    if end == "no":
        labels_list[-1].grid(column = col, row=len(labels_list))
    elif end == "yes":
        labels_list[-1].grid(column = col, row=len(labels_list)+1)

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
            script_commands = {'boot_a':'adb shell dd if=/dev/block/mmcblk0p12 of=/sdcard/boot_a count=65536 bs=1024',
            'system_a':'adb shell dd if=/dev/block/mmcblk0p14 of=/sdcard/system_a count=3145728 bs=1024',
            'vendor_a':'adb shell dd if=/dev/block/mmcblk0p16 of=/sdcard/vendor_a count=1048576 bs=1024'            }
            
            for label, command in script_commands.items():               
                proc= subprocess.run(command, capture_output=True, shell=True, text = True)
                add_label(topFrame, 2, script_labels, f"{label}: ", proc.stderr[proc.stderr.index("transferred"):proc.stderr.index("(")-1], end="yes")
                time.sleep(2)
            
            reset_script_labels()              

            sha_commands = {"boot_a": 'adb shell sha256sum /sdcard/boot_a',
            "system_a":'adb shell sha256sum /sdcard/system_a',
            "vendor_a":'adb shell sha256sum /sdcard/vendor_a' }
            for label, command in sha_commands.items():             
                process = subprocess.run(command, capture_output=True, shell=True, text = True)
                add_label(topFrame, 2, script_labels, label, process.stdout.split()[0], end="no")                
        
            rm = subprocess.run('adb shell rm /sdcard/boot_a /sdcard/system_a /sdcard/vendor_a', shell=True)
            if rm.returncode != 0:
                label_script.config(text=(rm.stderr))
               
        else:
            label_script.config(text=("Not enough space, failed"))
    button_copy.grid(column=3, row=0)

def run_script(): 
    print(threading.active_count())
    if threading.active_count() > 1:
        showinfo("Warning", "Script is still runing!")
    else:             
        reset_script_labels()               
        label_script.config(text=("Please wait...")) 
        global thread
        thread = threading.Thread(target = script)
        thread.start()
        
def reset():
    print(threading.active_count())
    [flab.destroy() for flab in file_labels ]
    del file_labels[:]    
    [clab.destroy() for clab in clip_labels ]
    del clip_labels[:]    
    button_choose.config(text=("Chose file"))         
    button_copy.grid_forget()
    if threading.active_count() > 1:
        showinfo("Warning", "Script is still runing!")
    else:   
        reset_script_labels()
    
def reset_script_labels():    
    label_script.config(text=(""))
    [slab.destroy() for slab in script_labels ]        
    del script_labels[:]
   
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
  
def copy_to_clipboard():
    test = []
    for label in script_labels:
        test.append(label.cget("text").split())
    test = [item for sublist in test for item in sublist]
    pyperclip.copy("\n".join(test[1::2]))

def on_closing():
    if threading.active_count() > 1:
        showinfo("Warning", "Script is still runing!")
    else:
        window.destroy()

window.protocol("WM_DELETE_WINDOW", on_closing)

topFrame = tkinter.Frame(window)
topFrame.pack()

label_script = tkinter.Label(topFrame) 
label_script.grid(column=2, row=1)

button_choose = tkinter.Button(topFrame, text ="Chose file", command = select_files)
button_choose.grid(column=0, row=0, padx= (0,20), pady=(10, 10))

button_clipboard = tkinter.Button(topFrame, text="Paste Clipboard", command = paste_clip)
button_clipboard.grid(column=1, row=0, padx= (0,20), pady=(10, 10))

button_script = tkinter.Button(topFrame, text="Run script", command = run_script)
button_script.grid(column=2, row=0, padx= (0,20), pady=(10, 10))

button_copy = tkinter.Button(topFrame, text="copy", command= copy_to_clipboard, bg = "SpringGreen2")

bottomFrame = tkinter.Frame(window)
bottomFrame.pack(side="bottom")

compare_button = tkinter.Button(bottomFrame, text ="Compare", command = compare, bg="SkyBlue3")
compare_button.grid(column=2, row=3,columnspan=2,padx=(100, 0), pady=(10, 10))

reset_button = tkinter.Button(bottomFrame, text ="Reset", command = reset, bg = "OrangeRed2")
reset_button.grid(column=0, row=3, padx = (10,0))


window.mainloop()

