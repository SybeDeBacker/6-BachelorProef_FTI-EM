import os
from time import sleep as delay
import threading

def thread1():
    os.system('C:/Users/Sybe/AppData/Local/Programs/Python/Python313/python.exe "C:/Users/Sybe/Documents/!UAntwerpen/6e Semester/6 - Bachelorproef/Code/Github/6-BachelorProef_FTI-EM_CoSysLab/2e semester/HTTPServer.py"')

def thread2():
    os.system('C:/Users/Sybe/AppData/Local/Programs/Python/Python313/python.exe "C:/Users/Sybe/Documents/!UAntwerpen/6e Semester/6 - Bachelorproef/Code/Github/6-BachelorProef_FTI-EM_CoSysLab/2e semester/User.py"')

threading.Thread(target=thread1()).start
delay(5)

i=0
while i<1:
    threading.Thread(target=thread2()).start
    delay(15)
    i+=1