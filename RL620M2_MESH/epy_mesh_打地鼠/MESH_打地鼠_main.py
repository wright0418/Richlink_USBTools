from machine import UART, LED, Switch
from utime import sleep, ticks_ms, ticks_diff
import gc
import ubinascii as binascii
import ustruct as struct

from MESHDevice import MeshDevice as Mesh_D


try:
    uart = UART(1, 115200, timeout=20)
except:
    uart.deinit()
    uart = UART(1, 115200, timeout=20)
uart.read(uart.any())


def chek_node_reset_key():
    pre_ticks_ms = ticks_ms()
    while key.value():
        if ticks_diff(ticks_ms(), pre_ticks_ms) > 1000:
            MD.NodeReset()
            # print('reset_node')
            while True:
                type1, data1 = MD.uart_recv()
                if type1 == 'SYS-MSG' and ('DEVICE' in data1):
                    break
            break


def check_key_and_send_score():
    global my_uid, act_uid, score
    if key.value() and my_uid == act_uid:
        clear_mouse()
        score = score+1
        MD.Send_mesh_data(bytes(struct.pack(">B", score)))
        act_uid = "90"


def check_mesh_cmd_show_action(type, data):
    global act_uid, game_start, my_uid, score
    if type == "MDTS-MSG":
        try:
            act_uid = data1[2][:2]
            game_start = data1[2][2:]
            my_uid = MD.uid[4:]
            if game_start == "01":
                if act_uid == 'FF':
                    score = 0
                    MD.Send_mesh_data(bytes(struct.pack(">B", score)))
                if my_uid == act_uid:
                    show_mouse()
                else:
                    clear_mouse()
        except:
            pass


def show_mouse():
    Mouse.on()
    rgb.rgb_write(R64)


def clear_mouse():
    Mouse.off()
    rgb.off()


prov_index = LED('ledr')
Mouse = LED('ledy')
rgb = LED(LED.RGB)

key = Switch('keya')
prov_index.on()
Mouse.on()
sleep(1)
prov_index.off()
Mouse.off()

uart.write('AT+VER\r\n')
sleep(0.1)
_ = uart.read(uart.any())

R64 = [[255, 0, 0]]*64

score = 0
act_uid = None
game_start = 0
my_uid = None

MD = Mesh_D(uart)
while True:
    type1, data1 = MD.uart_recv()
    gc.collect()
    sleep(0.05)
    if MD.prov_state != 'PROV-ED':
        prov_index.toggle()
        sleep(0.5)
    else:
        # chek_node_reset_key()
        check_mesh_cmd_show_action(type1, data1)
        check_key_and_send_score()
    gc.collect()
    sleep(0.05)
