from utime import sleep_ms, ticks_ms, ticks_diff
import ubinascii as binascii


class MeshDevice:

    def __init__(self, uart):

        self.ble = uart
        self.publish_info = {'from': None, 'data': None}
        self.mesh_data = None
        self.uid = None
        self.prov_state = None
        self.ble.write('\r\n\r\n')
        self.ble.read(self.ble.any())
        self.check_prov()
        self.mac_addr = self.MyMac_Addr()

    def __del__(self):
        self.ble.deinit()

    def WriteCMD_withResp(self, atcmd_):
        _ = self.ble .read(self.ble .any())
        _ = self.ble.write(atcmd_+'\r\n')
        # print('Send_AT',atcmd_)
        type, msg = self.uart_recv(timeout=3000)
        return type, msg

    def check_msg(self, type, data):
        if 'SYS-MSG' in type and len(data) >= 2:
            if data[0] == 'DEVICE':
                if len(data) >= 3:
                    self.uid = data[2]
                self.prov_state = data[1]
        if 'PROV-MSG' in type and len(data) == 2:
            if data[0] == 'SUCCESS':
                self.prov_state = 'PROV-ED'
                self.uid = data[1]
            else:
                self.prov_state = 'UNPROV'

        if 'MDTGP-MSG' in type and len(data) == 3:
            self.publish_info['from'] = data[0]
            self.publish_info['data'] = binascii.unhexlify(data[2])

        if 'MDTS-MSG' in type and len(data) == 3:
            self.mesh_data = binascii.unhexlify(data[2])
        return

    def uart_recv(self, timeout=50):
        pre_ticks = ticks_ms()
        while True:
            try:
                if self.ble.any():
                    msg = str(self.ble.readline(), 'utf-8').strip().split(' ')
                    type = msg[0]
                    other = msg[1:]
                    #print (type,msg)
                    if type in ('REBOOT-MSG',):
                        continue
                    self.check_msg(type, other)
                    return type, other
                elif ticks_diff(ticks_ms(), pre_ticks) > timeout:
                    return None, None
            except:
                return None, None

            sleep_ms(10)

    def NodeReset(self):
        self.WriteCMD_withResp('AT+NR')

    def check_prov(self):
        self.WriteCMD_withResp('AT+REBOOT')

    def MyMac_Addr(self):
        _, msg = self.WriteCMD_withResp('AT+ADDR')
        return msg[0]

    def read_mdts_data(self):
        data = self.mesh_data
        self.mesh_data = None
        return data

    def read_publish_data(self):
        source = self.publish_info['from']
        data = self.publish_info['data']
        self.publish_info['from'] = None
        self.publish_info['data'] = None
        return source, data

    def Send_mesh_data(self, data):
        if not isinstance(data, bytes):
            return
        if len(data) > 20:
            data = data[:20]
        self.mesh_data = data
        msg = self.WriteCMD_withResp(
            'AT+MDTS 0 0x{}'.format(str(binascii.hexlify(data), 'utf-8')))


if __name__ == '__main__':
    ''' MESH device RAW Data (bytes) read/write'''
    from machine import UART, LED
    from utime import sleep
    import gc
    try:
        uart = UART(1, 115200, timeout=20)
    except:
        uart.deinit()
        uart = UART(1, 115200, timeout=20)
    y = LED('ledy')
    MD = MeshDevice(uart)
    # MD.NodeReset()
    while True:
        type1, data1 = MD.uart_recv()
        if MD.prov_state != 'PROV-ED':
            y.toggle()
            sleep(0.5)
        else:
            y.on()
            dat = MD.read_mdts_data()
            if dat:
                print(dat)
