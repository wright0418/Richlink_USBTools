import serial.tools.list_ports
import PySimpleGUI as sg
import datetime
import threading
import time

# 找到所有的串口
ports = [port[0] for port in list(serial.tools.list_ports.comports())]


# 定义一个函数，用于读取并处理串口响应
def read_response_thread(ser, response_window):
    while ser.is_open:
        response = ser.readline().decode().strip()
        if response:
            # 更新响应窗口
            response_window.print(
                f'[{datetime.datetime.now().strftime("%H:%M:%S.")}{str(datetime.datetime.now().microsecond//100)}] <<：{response}')
        time.sleep(0.001)


# AT CMD 下拉選單選項
at_commands = [
    'AT', 'AT+ROLE=?', 'AT+ROLE=P', 'AT+ROLE=C', 'AT+VERSION', 'AT+MODE_DATA', 'AT+ADDR=?', 'AT+REBOOT', 'AT+EN_SYSMSG=1', 'AT+TX_POWER=?', 'AT+SCAN', 'AT+CONN='
]
# 創建 PySimpleGUI 窗口
layout = [[sg.Text('請選擇要連接的串口：')],
          [sg.Combo(ports, size=(20, 1), key='PORT')],
          [sg.Button('連線', key='CONNECT'), sg.Button('取消')],
          [sg.Multiline(size=(80, 30), key='RESPONSE',
                        autoscroll=True, reroute_stdout=True)],
          [sg.Checkbox('顯示送出訊息', key='SHOW_SENT_MESSAGE')],
          [sg.Checkbox('加上 \\r\\n', key='ADD_CR_NL')],
          [sg.Text('AT CMD：'),
           sg.Combo(at_commands, size=(30, 1), key='AT_CMD')],
          [sg.Button('送出', key='SEND')]
          ]

window = sg.Window('RL62M01 AT CMD Tools', layout)
keep_window_open = True
ser = None
response_thread = None
while keep_window_open:
    event, values = window.read()
    if event in (sg.WIN_CLOSED, '取消'):
        keep_window_open = False
        break
    elif event == 'CONNECT':
        port = values['PORT']
        # 连接到串口
        try:
            ser = serial.Serial(port, baudrate=115200,
                                bytesize=8, parity='N', stopbits=1, timeout=1)
            print(f'Connected {port}')
            # 清除串口接收缓冲区
            ser.reset_input_buffer()
            # 禁用连接按钮
            window['CONNECT'].update(disabled=True)
            # 发送 AT 命令并读取响应
            ser.write(b'AT\r\n')
            response = ser.readline().decode().strip()
            # 在窗口中显示响应
            window['RESPONSE'].print(
                f'[{datetime.datetime.now().strftime("%H:%M:%S")}{str(datetime.datetime.now().microsecond//100)}] <<：{response}')
            # 启动响应读取线程
            response_thread = threading.Thread(
                target=read_response_thread, args=(ser, window['RESPONSE']))
            response_thread.start()

        except Exception as e:
            print(f'Connect {port} Fail{e}')
            keep_window_open = False
            break
    elif event == 'SEND':
        if ser is not None and ser.is_open:
            at_cmd = values['AT_CMD']
            show_sent_message = values['SHOW_SENT_MESSAGE']
            add_cr_nl = values['ADD_CR_NL']
            if add_cr_nl:
                at_cmd += '\r\n'
            if show_sent_message:
                window['RESPONSE'].print(
                    f'[{datetime.datetime.now().strftime("%H:%M:%S")}{str(datetime.datetime.now().microsecond//100)}] >>：{at_cmd}')
            ser.write(at_cmd.encode())
        else:
            print('Please Connect to COM Port')

# 关闭连接并清理
if ser is not None and ser.is_open:
    ser.close()
if response_thread is not None and response_thread.is_alive():
    response_thread.join()
window.close()
