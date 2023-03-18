'''
must to install 
pip install pyserial
pip install pysimplegui

1. 建立 Serial COM 連線
2. Serial COM Port 送  MESH AT COMMAND "?" ，回應command 列表
    開啟一個 thread  read UART 回應 訊息，持續接收 UART 資料
3. 按鍵 Send AT+MRG\r\n , 詢問 MESH Module 是哪一種 "DEVICE /PROVISIONER"
4. 增加一個可以輸入  AT CMD 命令列 , 並建立一個可選CMD清單
'''
import serial.tools.list_ports
import serial
import PySimpleGUI as sg
import datetime
from time import sleep
import threading

# find all COM Port Number
# Get a list of available serial ports using the serial.tools.list_ports module.
# Extract only the name of each port using a list comprehension.
ports = [port[0] for port in list(serial.tools.list_ports.comports())]

# Define a list of AT CMD options.
at_cmd_options = ['VER', 'MRG', 'REBOOT', 'NL',
                  'DIS 1', 'DIS 0', 'PBADVCON', 'PROV 1']

# Create PySimpleGUI windows
layout = [
    [sg.Text('Please Select COM Port')],
    [sg.Combo(ports, size=(20, 1), key='PORT'),
     sg.Text('Close', key='STATUS', background_color='grey')],
    [sg.Button('Connect', key='CONNECT', disabled=False), sg.Button('Close')],
    [sg.Button('Test AT CMD'), sg.Text('', key='ROLE', text_color='red')],
    [sg.Text('AT CMD List:'),
     sg.Combo(at_cmd_options, size=(30, 1), key='ATCMD'), sg.Button('SEND')],

    [sg.Multiline(size=(60, 20), key='OUTPUT', font=(
        'Helvetica', 12), autoscroll=True)],
]

# Define a function for writing Mesh AT commands to the serial port.


def write_mesh_AtCmd(cmd):
    global ser
    if cmd == '?':
        atcmd = f'{cmd}\r\n'.encode()
    else:
        atcmd = f'AT+{cmd}\r\n'.encode()
    ser.write(atcmd)
    # output atcmd to window
    window['OUTPUT'].print(f">>{atcmd.decode()}")

# Define a function for reading data from the serial port.


def read_thread():
    global ser
    while True:
        if ser is not None and ser.is_open:
            if ser.in_waiting:
                msg = ser.readline().decode().strip()
                window.write_event_value(
                    ('-READ_THREAD-', 'OUTPUT', msg), None)

                if msg:
                    msg = msg.split(' ')
                    type = msg[0]
                    data = msg[1:]
                    if type == 'MRG-MSG':
                        window.write_event_value(
                            ('-READ_THREAD-', 'ROLE', data[1]), None)

        sleep(0.1)


# Create the PySimpleGUI window.
window = sg.Window('MESH Prov_1', layout, font=('Helvetica', 14))
keep_window_open = True
ble_connected = False
ser = None


# Use a while loop to continuously read events from the PySimpleGUI window.
while keep_window_open:
    event, values = window.read()
    if event in (sg.WIN_CLOSED, 'Close'):
        keep_window_open = False

    elif event == 'CONNECT':
        port = values['PORT']
        if port:
            ser = serial.Serial(port, baudrate=115200,
                                bytesize=8, parity='N', stopbits=1, timeout=1)
            print(f'Connected {port}')
            window['STATUS'].update('Open', background_color='green')
            window['CONNECT'].update(disabled=True)
            ble_connected = True
            t = threading.Thread(target=read_thread, daemon=True)
            t.start()
            # check Role
            write_mesh_AtCmd('MRG')

    elif event[0] == '-READ_THREAD-':
        if event[1] == 'OUTPUT':
            window['OUTPUT'].print(event[2])
        elif event[1] == 'ROLE':
            window['ROLE'].update(event[2])

    if ble_connected:
        if event == 'Test AT CMD':
            write_mesh_AtCmd('?')
        elif event == 'SEND':
            atcmd = values['ATCMD']
            if atcmd:
                write_mesh_AtCmd(atcmd)


if ser is not None and ser.is_open:
    ser.close()
window.close()
