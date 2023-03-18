import serial.tools.list_ports
import PySimpleGUI as sg
import datetime
from time import sleep

# find all COM Port Number
ports = [port[0] for port in list(serial.tools.list_ports.comports())]

# Create PySimpleGUI windows
layout = [
    [sg.Text('Please Select COM Port')],
    [sg.Combo(ports, size=(20, 1), key='PORT')],
    [sg.Button('Connect', key='CONNECT'), sg.Button('Close')],
    [sg.Text('LAMP A')],
    [sg.Button('Red A', key='RED_A', button_color='gray'), sg.Button(
        'Yellow A', key='YELLOW_A', button_color='gray'), sg.Button('Green A', key='GREEN_A', button_color='gray')],
    [sg.Text('LAMP B')],
    [sg.Button('Red B', key='RED_B', button_color='gray'), sg.Button(
        'Yellow B', key='YELLOW_B', button_color='gray'), sg.Button('Green B', key='GREEN_B', button_color='gray')],
]


def write_mesh_AtCmd(cmd):
    global ser
    atcmd = f'AT+{cmd}\r\n'.encode()
    ser.write(atcmd)


def ser_read():
    global ser
    if ser.in_waiting:
        msg = ser.readline().decode()
        print(msg)


window = sg.Window('MESH Prov Demo', layout, size=(
    800, 600), font=('Helvetica', 24))
keep_window_open = True
ble_connected = False
ser = None
button_colors = {'RED_A': None, 'YELLOW_A': None, 'GREEN_A': None,
                 'RED_B': None, 'YELLOW_B': None, 'GREEN_B': None}
while keep_window_open:
    event, values = window.read()
    if event in (sg.WIN_CLOSED, 'Close'):
        keep_window_open = False
        break
    elif event == 'CONNECT':
        port = values['PORT']
        if port:
            ser = serial.Serial(port, baudrate=115200,
                                bytesize=8, parity='N', stopbits=1, timeout=1)
            print(f'Connected {port}')

    elif event in button_colors:
        button = event
        color = button_colors[button]
        if color is None:
            # Change button color to red
            window[button].update(button_color=('white', 'red'))
            button_colors[button] = 'red'
            # Send corresponding mesh CMD
            if button == 'RED_A':
                write_mesh_AtCmd('MDTS 0x100 0 0 1 05')
            elif button == 'YELLOW_A':
                write_mesh_AtCmd('MDTS 0x100 0 0 1 03')
            elif button == 'GREEN_A':
                write_mesh_AtCmd('MDTS 0x100 0 0 1 01')
            elif button == 'RED_B':
                write_mesh_AtCmd('MDTS 0x104 0 0 1 05')
            elif button == 'YELLOW_B':
                write_mesh_AtCmd('MDTS 0x104 0 0 1 03')
            elif button == 'GREEN_B':
                write_mesh_AtCmd('MDTS 0x104 0 0 1 01')
        else:
            # Change button color back to white
            window[button].update(button_color=('white', 'gray'))
            button_colors[button] = None
            # Send corresponding mesh CMD
            if button == 'RED_A':
                write_mesh_AtCmd('MDTS 0x100 0 0 1 06')
            elif button == 'YELLOW_A':
                write_mesh_AtCmd('MDTS 0x100 0 0 1 04')
            elif button == 'GREEN_A':
                write_mesh_AtCmd('MDTS 0x100 0 0 1 02')
            elif button == 'RED_B':
                write_mesh_AtCmd('MDTS 0x104 0 0 1 06')
            elif button == 'YELLOW_B':
                write_mesh_AtCmd('MDTS 0x104 0 0 1 04')
            elif button == 'GREEN_B':
                write_mesh_AtCmd('MDTS 0x104 0 0 1 02')
if ser is not None and ser.is_open:
    ser.close()
window.close()
