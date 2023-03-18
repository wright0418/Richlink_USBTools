import serial.tools.list_ports
import PySimpleGUI as sg
import datetime
from time import sleep

# 找到所有的串口
ports = [port[0] for port in list(serial.tools.list_ports.comports())]

# 創建 PySimpleGUI 窗口
layout = [
    [sg.Text('請選擇要連接的串口：')],
    [sg.Combo(ports, size=(20, 1), key='PORT')],
    [sg.Radio('主機模式', "RADIO1", key='HOST_MODE'),
     sg.Radio('從機模式', "RADIO1", default=True, key='SLAVE_MODE')],
    [sg.Button('連線', key='CONNECT'), sg.Button('取消')],
]


def Change_CMD_Mode():
    global ser
    ser.write(b'!CCMD@')
    sleep(0.5)
    ser.write(b'AT\r\n')
    sleep(0.1)
    ret = ser_read()


def ser_read():
    global ser
    if ser.in_waiting:
        ret = ser.read(ser.in_waiting)
        return ret


def Host_Mode_ATCMD():
    global ser
    Change_CMD_Mode()
    ser.write(b'AT+ROLE=C\r\n')
    sleep(0.5)
    ret = ser_read()


def Slave_Mode_ATCMD():
    global ser
    Change_CMD_Mode()
    ser.write(b'AT+ROLE=P\r\n')
    sleep(0.5)
    ret = ser_read()
    ser.write(b'AT+MODE_DATA\r\n')
    sleep(0.5)
    ret = ser_read()


def Slave_Mode_Send_ABC(cmd):
    global ser
    cmd += '\r\n'
    ser.write(cmd.encode())
    window['RESPONSE'].print(f'>>>{cmd}')


def Slave_Mode_Send_Text(text):
    global ser
    ser.write(text.encode() + b'\r\n')
    window['RESPONSE'].print(f'>>>{text}')


def Recv_Data_Mode():
    global ser
    if ser.in_waiting:
        ret = ser.readline().decode().strip()
        window['RESPONSE'].print(f'<<<{ret}')
        return ret


window = sg.Window('RL62M USB Demo', layout)
keep_window_open = True
ble_connected = False
ser = None
while keep_window_open:
    event, values = window.read()
    if event in (sg.WIN_CLOSED, '取消'):
        keep_window_open = False
        break
    elif event == 'CONNECT':
        port = values['PORT']
        if port:
            mode = 'host' if values['HOST_MODE'] else 'slave'
            ser = serial.Serial(port, baudrate=115200,
                                bytesize=8, parity='N', stopbits=1, timeout=1)
            print(f'已连接到串口 {port}')
            # 清除串口接收缓冲区
            ser.reset_input_buffer()
            window.close()
            break
        else:
            print('need select a com port')

if keep_window_open and port is not None and mode is not None:
    if mode == 'host':
        layout = [
            [sg.Button('掃描裝置', key='SCAN_DEVICE'), sg.Listbox(
                values=[], size=(50, 5), key='DEVICE_LIST'), sg.Button('連線', key='BLE_CON'), sg.Button('斷線', key='BLE_DISCON', disabled=True)],
            [sg.Multiline(size=(80, 10), key='RESPONSE',
                          autoscroll=True)],
            [sg.Button('Send A', key='SEND_A'), sg.Button(
                'Send B', key='SEND_B'), sg.Button('Send C', key='SEND_C')],
            [sg.InputText(key='TEXT_INPUT'), sg.Button(
                '傳送', key='SEND_TEXT')],
            [sg.Button('退出')],
        ]
        Host_Mode_ATCMD()
    elif mode == 'slave':
        layout = [[sg.Multiline(size=(80, 10), key='RESPONSE', autoscroll=True)],
                  [sg.Button('Send A', key='SEND_A'), sg.Button(
                      'Send B', key='SEND_B'), sg.Button('Send C', key='SEND_C')],
                  [sg.InputText(key='TEXT_INPUT'), sg.Button(
                      '傳送', key='SEND_TEXT')],
                  [sg.Button('退出')],
                  ]
        Slave_Mode_ATCMD()

    window = sg.Window('RL62M01_DEMO', layout)
    while True:
        event, values = window.read(timeout=100)
        if event in (sg.WIN_CLOSED, '退出'):
            break

        if event == 'SCAN_DEVICE':
            wait_layoyt = [[sg.Text('搜尋中...')]]
            device = []
            _ = ser_read()
            ser.write(b'AT+SCAN\r\n')
            line = ser.readline()
            sleep(0.5)
            window['DEVICE_LIST'].update(values=device)
            wait_ = sg.Window('等待窗口', wait_layoyt, modal=True,
                              no_titlebar=True, auto_close=True, auto_close_duration=5)
            event, values = wait_.read()
            wait_.close()
            while True:
                line = ser.readline().decode('utf-8')
                if line:
                    if 'SCAN_END_DEV_NUM' not in line and line.split(' ')[0].isdigit():
                        device.append(line)
                        line = line.strip()
                        window['DEVICE_LIST'].update(values=device)
                    else:
                        break
        if event == 'BLE_CON':
            if values['DEVICE_LIST']:
                no = values['DEVICE_LIST'][0].split(' ')[0]
                cmd = f'AT+CONN={no}\r\n'
                ser.write(cmd.encode())
                sleep(0.2)
                ser.write(b'AT+MODE_DATA\r\n')
                sleep(0.2)
                ret = ser_read()
                ble_connected = True
                window['BLE_CON'].update(disabled=True)
                window['SCAN_DEVICE'].update(disabled=True)
                window['BLE_DISCON'].update(disabled=False)

        if event == 'BLE_DISCON':
            Change_CMD_Mode()
            sleep(0.1)
            ret = ser_read()
            ser.write(b'AT+DISC\r\n')
            sleep(0.1)
            ret = ser_read()
            ble_connected = True
            window['BLE_CON'].update(disabled=False)
            window['SCAN_DEVICE'].update(disabled=False)
            window['BLE_DISCON'].update(disabled=True)
            device = []
            window['DEVICE_LIST'].update(values=device)

        elif event == 'SEND_A':
            Slave_Mode_Send_ABC('A')
        elif event == 'SEND_B':
            Slave_Mode_Send_ABC('B')
        elif event == 'SEND_C':
            Slave_Mode_Send_ABC('C')
        elif event == 'SEND_TEXT':
            text = values['TEXT_INPUT']
            if text:
                Slave_Mode_Send_Text(text)
        Recv_Data_Mode()
    if ser is not None and ser.is_open:
        ser.close()
    window.close()
