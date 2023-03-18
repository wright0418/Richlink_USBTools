'''
must to install
pip install pyserial
pip install pysimplegui

1. 建立 Serial COM 連線
2. Serial COM Port 送  MESH AT COMMAND "?" ，回應command 列表
    開啟一個 thread  read UART 回應 訊息，持續接收 UART 資料
3. 按鍵 Send AT+MRG\r\n , 詢問 MESH Module 是哪一種 "DEVICE /PROVISIONER"
4. 建立 處理 綁定 流程 thread  
5. 綁定 裝置管理 , 是否在線 顯示

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
ports = [port.device for port in serial.tools.list_ports.comports()]

# Define a list of AT CMD options.
at_cmd_options = ['VER', 'MRG', 'REBOOT', 'NL',
                  'DIS 1', 'DIS 0', 'PBADVCON', 'PROV 1']

# Create PySimpleGUI windows
layout = [
    [sg.Text('Please Select COM Port')],
    [sg.Combo(ports, size=(20, 1), key='PORT'),
     sg.Text('Close', key='STATUS', background_color='grey')],
    [sg.Button('Connect', key='CONNECT', disabled=False), sg.Button('Close')],
    [sg.Button('Unbind All'), sg.Text('', key='ROLE', text_color='red')],
    [sg.Button('Bind Device to DataTrans Model(0x04005D)', key='BIND')],
    [sg.T(text='Serial Msg', pad=((100, 0), (0, 0))), sg.T(
        text='un-bind Mac address', pad=((530, 0), (0, 0)))],
    [sg.Multiline(size=(60, 20), key='OUTPUT', font=(
        'Helvetica', 10), autoscroll=True),
     sg.Listbox(values=[], size=(30, 20), key='DEVICE', font=(
         'Helvetica', 10), enable_events=True)],
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
    with lock:
        window['OUTPUT'].print(f">>{atcmd.decode()}")

# Define a function for reading data from the serial port.


unbind_dict = {}
prov_uid = None
prov_state = None

# 創建一個threading.Lock()
lock = threading.Lock()

# Note .....
# Thread 中的 event  會透過 window.write_event_value() 將 訊息傳回 main GUI Thread
# 主 GUI 在   window.read() 就會收到此 Event 與  value
# window.write_event_value( ('-READ_THREAD-', 'OUTPUT', msg), None)
#        Event = ('-READ_THREAD-', 'OUTPUT', msg) , Value = None


def read_thread():
    global ser, prov_uid, prov_state
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
                    print('t-d', type, data)
                    if type == 'MRG-MSG':
                        window.write_event_value(
                            ('-READ_THREAD-', 'ROLE', data[1]), None)
                    elif type == "DIS-MSG" and len(data) == 3 and '123E4567E89B12D3A456' in data[2]:
                        if data[0] not in unbind_dict:
                            unbind_dict[data[0]] = data[2]
                            window.write_event_value(
                                ('-READ_THREAD-', 'DEVICE', None), None)

                    elif type in ('PBADVCON-MSG', 'AKA-MSG', 'MAKB-MSG'):
                        print('msg', type, data)
                        prov_state = data[0]

                    elif type == 'PROV-MSG':
                        if data[0] == 'SUCCESS':
                            prov_state = data[0]
                            prov_uid = data[1]
                        else:
                            prov_state = data[0]
                        print('Prov', data)
        sleep(0.1)


def bind_device(mac_address):
    global prov_state, prov_uid

    print('start bind')
    write_mesh_AtCmd('PBADVCON {}'.format(mac_address))
    sleep(1)
    if prov_state != 'SUCCESS':
        window.write_event_value(('-BIND_THREAD-', 'ERROR'), None)
        return
    write_mesh_AtCmd('PROV')
    sleep(5)

    write_mesh_AtCmd(f'AKA {prov_uid} 0 0')
    sleep(1)
    if prov_state != 'SUCCESS':
        window.write_event_value(('-BIND_THREAD-', 'ERROR'), None)

        return
    write_mesh_AtCmd(f'MAKB {prov_uid} 0 x4005D 0')
    sleep(1)
    if prov_state != 'SUCCESS':
        window.write_event_value(('-BIND_THREAD-', 'ERROR'), None)

        return
    window.write_event_value(('-BIND_THREAD-', 'SUCCESS'), None)


# Create the PySimpleGUI window.
window = sg.Window('MESH Prov_Bind', layout, font=('Helvetica', 12))
keep_window_open = True
ble_connected = False
ser = None


# Use a while loop to continuously read events from the PySimpleGUI window.
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
            window['STATUS'].update('Open', background_color='green')
            window['CONNECT'].update(disabled=True)
            ble_connected = True

            # 連線上後，建立一個讀取  UART  thread ，並啟動 thread
            t = threading.Thread(target=read_thread, daemon=True)
            t.start()
            # check Role
            write_mesh_AtCmd('MRG')
# check event from read thread
    elif event[0] == '-READ_THREAD-':
        name = event[1]
        value = event[2]
        if name == 'OUTPUT':
            window['OUTPUT'].print(value)
        elif name == 'ROLE':
            window['ROLE'].update(value)
        elif name == 'DEVICE':
            window['DEVICE'].update(values=unbind_dict)

# check event from bind  thread
    elif event[0] == '-BIND_THREAD-':
        if event[1] == 'SUCCESS':
            sg.popup_no_buttons('Binding success!', auto_close_duration=4)
            unbind_dict = {}
            window['DEVICE'].update(values=unbind_dict)
        else:
            sg.popup_no_buttons('Binding failed!', auto_close_duration=4)
            unbind_dict = {}
            window['DEVICE'].update(values=unbind_dict)

    if ble_connected:
        if event == 'Unbind All':
            write_mesh_AtCmd('NR')
        elif event == 'BIND':
            unbind_dict = {}
            window['DEVICE'].update(values=unbind_dict)
            # enable 搜尋
            write_mesh_AtCmd('DIS 1')
        elif event == 'DEVICE':
            # disable 搜尋
            write_mesh_AtCmd('DIS 0')
            selected_item = values['DEVICE'][0]
            confirm = sg.popup('Are you sure to bind the mac address "{}" to model 0x0405D?'.format(
                selected_item), title='Confirmation', button_type=sg.POPUP_BUTTONS_YES_NO)

            if confirm == 'Yes':
                sg.popup_no_buttons('Binding............',
                                    non_blocking=True, auto_close_duration=7)
                t = threading.Thread(target=bind_device, args=(
                    unbind_dict[selected_item],))
                t.start()

if ser is not None and ser.is_open:
    ser.close()
window.close()
