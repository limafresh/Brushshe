import tkinter

root = tkinter.Tk()

mods = {
    0x0001: 'Shift',
    0x0002: 'Caps Lock',
    0x0004: 'Control',
    0x0008: 'Left-hand Alt',
    0x0010: 'Num Lock',
    0x0080: 'Right-hand Alt',
    0x0100: 'Mouse button 1',
    0x0200: 'Mouse button 2',
    0x0400: 'Mouse button 3'
}

def key_handler(event):
    print(event.char, event.keysym, event.keycode, event.state)

root.bind("<Key>", key_handler)

root.mainloop()
