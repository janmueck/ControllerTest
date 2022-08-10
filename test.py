import socket
from typing import Tuple,Any
import tkinter as tk 
from tkinter import font as tkFont
from tkinter import ttk
import time 
import re
ADRESS='/tmp/MOsoMMLh9a'







class ControllerProxy():
    def __init__(self,) -> None:
        self.s=socket.socket(socket.AF_UNIX, socket.SOCK_STREAM, 0) 
        self.s.connect('/tmp/MOsoMMLh9a')
        self.TESTS=[('led set {color}',['{color}','unknown']),
                    ('modem test',['success','fail']),
                    ('modem ICCID',['1234567890']),
                    ('SomeInvString',['Supported requests: \n\t [] led set <color>, with <color>=red|green|blue\n\t [] modem test'])]
        self.leds=['red','green','blue']
        self.statusQueue=[]
        self.statusQueue.append('Connected to device')
        

    def log(self,message:str)->None:
        self.statusQueue.append(message)
    def send(self,message:bytes):
        self.s.sendall(message)

    def sendRecv(self,message:bytes)->bytes:
        self.send(message)
        return self.s.recv(2048).decode('utf8')

    def runTest(self,testPair:Tuple[str,Any])->Tuple[bool,str]:
        message,expectedResults=testPair
        recv=self.sendRecv(bytes(message,'utf8'))
        #print(recv)
        #we split at the null-terminated end to get the message
        msg=recv.split('\x00',1)[0]
        #print((retMsg,), result)
        valid = msg in expectedResults 
        return valid,msg

    def testModem(self)->bool:
        self.log('\n')
        self.log('Starting Modem Test')
        flag,res=self.runTest(self.TESTS[1])
        result=flag and res=='success'
        
        
        self.log(f'Modem Test finished with result: {result} ')
        return result

    def testColors(self,) -> bool:
        self.log('\n')
        validColors=['red','green','blue']
        otherColors=['purple']
        res=[]
        
        for testColor in validColors:
            flag,color=self.runTest((self.TESTS[0][0].format(color=testColor),list(map(lambda x: x.format(color=testColor),self.TESTS[0][1]))))
            
            resI=flag and color==testColor
            res.append(resI)
            self.log(f'Tested for: {testColor}, recived: {color}, res: {resI}')
        for testColor in otherColors:
            flag,color=self.runTest((self.TESTS[0][0].format(color=testColor),list(map(lambda x: x.format(color=testColor),self.TESTS[0][1]))))
            
            resI=flag and color =='unknown'
            res.append(resI)
            self.log(f'Tested for: {testColor}, recived: {color}, res: {resI}')
        return all(res)


    def testColorsHW(self,UI) -> bool:
        self.log('\n')
        validColors=['red','green','blue']
        otherColors=['purple']
        
        res=[]
        
        for testColor in validColors:
            
            
            flag,color=self.runTest((self.TESTS[0][0].format(color=testColor),list(map(lambda x: x.format(color=testColor),self.TESTS[0][1]))))
            
            resI=flag and color==testColor
            if resI:
                UI.leds[testColor].config(background='light green')
            UI.root.wait_variable(UI.operatorReady)
            
            answer=UI.operatorChoice[testColor]
            
            resI=resI and answer
            res.append(resI)
            UI.operatorChoice[testColor]=False
            self.log(f'Tested for: {testColor}, recived: {color}, res: {resI}, confirmed; {answer}')
            UI.leds[testColor].config(background='black')
            
        
        return all(res)

    def readICCID(self,)->int:
        self.log('\n')
        self.log('Getting ICCID')
        res=self.sendRecv(bytes('modem ICCID','utf8'))
        result=int(res.split('\x00',1)[0])
        self.log(f'ICCID : {result}')
        return result

class UI():
    

    def __init__(self,)->None:
        
        self.operatorChoice={'red':False,'green':False,'blue':False}
        self.exit=False
        self.operatorReady=False
        
        
        self.root = tk.Tk()
        self.root.title('Controller Test')
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.root.attributes('-zoomed', True)
        self.ledNames=['red','green','blue']
        # self.root.columnconfigure(0, weight=1, minsize=575)
        # self.root.rowconfigure(0, weight=1, minsize=520)
        # self.root.columnconfigure(1, weight=1, minsize=575)
        # self.root.rowconfigure(1, weight=1, minsize=520)
        
        self.operatorReady=tk.BooleanVar()

        self.frm = ttk.Frame(self.root, padding=10)
        self.frm.grid(sticky=tk.NSEW)
        
        self.frm.columnconfigure(0, weight=1)
        self.frm.rowconfigure(0, weight=1)
        self.frm.columnconfigure(1, weight=1)
        self.frm.rowconfigure(1, weight=1)
        self.frm.columnconfigure(2, weight=0)
        self.frm.rowconfigure(2, weight=0)


        self.text=tk.Text(self.frm,font=("Helvetica", 32))
        self.text.grid(column=0,row=0,sticky=tk.NSEW)
        # fontExample = tkFont.Font(family="Arial", size=16, weight="bold", slant="italic")
        # self.text.configure()
        self.root.protocol("WM_DELETE_WINDOW", self.quit)

        self.led_choices=ttk.Frame(self.frm,padding=10)
        self.led_choices.grid(column=1,row=0,sticky=tk.NSEW)
        self.led_choices.rowconfigure(0, weight=1, minsize=100)
        self.led_choices.rowconfigure(1, weight=1, minsize=100)

        
        for i,led_name in enumerate(self.ledNames):
            self.led_choices.columnconfigure(i, weight=1, minsize=120)
            
            def P(color:str):
                def info():
                    self.operatorReady.set(True)
                    self.operatorChoice[color]=True
                return info
            def N(color:str):
                def info():
                    self.operatorReady.set(True)
                    self.operatorChoice[color]=False
                return info
            ttk.Button(self.led_choices, text=f"{led_name} Available", command= P(led_name)).grid(column=i, row=0,sticky=tk.NSEW)
            ttk.Button(self.led_choices, text=f"{led_name} Unavailable", command= N(led_name)).grid(column=i, row=1,sticky=tk.NSEW)
        



        self.led_display=ttk.Frame(self.frm,padding=10)

        self.led_display.grid(column=1, row=1,sticky=tk.NSEW)
        self.led_display.rowconfigure(0, weight=1, minsize=100)
        self.led_display.rowconfigure(1, weight=1, minsize=100)
        
        self.leds={}
        for i,led_name in enumerate(self.ledNames):
            self.led_display.columnconfigure(i, weight=1, minsize=120)
            ttk.Label(self.led_display, text=led_name, background=led_name,width=25).grid(column=i, row=0,sticky=tk.NSEW)
            self.leds[led_name]=ttk.Label(self.led_display, background='black')
            self.leds[led_name].grid(column=i, row=1,sticky=tk.NSEW)
        
        ttk.Button(self.frm, text="StartTest", command=self.run_Tests).grid(column=0, row=1,sticky=tk.NSEW)

        try:
            self.con=ControllerProxy()
            self.connectionFailed=False
        except ConnectionRefusedError:
            self.update(message='The connection to the controller could not be established please restart ')
            self.connectionFailed=True

    def run_Tests(self,):
        if not self.con.testModem():
            self.con.log('Modem test completed: Fail')
            self.update()
            return
        self.update()

        if not self.con.testColors():
            self.con.log('Symbolic LED test completed: Fail')
            self.update()
            return
        self.update()
        self.con.readICCID()
        self.update()
        if not self.con.testColorsHW(self):
            self.con.log('Hardware LED test completed: Fail')
            self.update()
            return
        
        self.con.log('Full test completed: Succes')
        self.update()

    def quit(self,):
        self.root.destroy() 
        self.exit=True


    def update(self,message=None):
        if message!=None:
            self.text.insert(tk.END,f'\n{message}')
            self.text.see('end')
            self.root.update_idletasks()
            self.root.update()  
            return
        if not self.connectionFailed:
            while len(self.con.statusQueue)>0:
                message=self.con.statusQueue.pop(0)
                self.text.insert(tk.END,f'\n{message}')
                self.text.see('end')
        self.root.update_idletasks()
        self.root.update()
    def mainloop(self,):
        
        while not self.exit:
            if not self.connectionFailed:
                while len(self.con.statusQueue)>0:
                    message=self.con.statusQueue.pop(0)
                    self.text.insert(tk.END,f'\n{message}')
                    self.text.see('end')
            
            self.root.update_idletasks()
            self.root.update()

        

if __name__ =='__main__':
    start=UI()
    start.mainloop()
    


    
    
    