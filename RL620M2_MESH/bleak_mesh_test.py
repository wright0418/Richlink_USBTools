import asyncio
import bleak
from bleak import discover
from bleak import BleakClient

PROVISIONING_SERVICE_UUID = "524CACC0-3C17-D293-8E48-14FE2E4DA212"
PROVISIONING_DATA_OUT_UUID = "0000D001-0000-1000-8000-00805F9B34FB"
PROVISIONING_DATA_IN_UUID = "0000D002-0000-1000-8000-00805F9B34FB"


async def scan_mesh_devices():

    # 设置要扫描的Service UUID，这里以SIG Mesh的UUID为例
    devices = await discover(services=[PROVISIONING_SERVICE_UUID])

    # 输出扫描到的设备信息
    for device in devices:
        print(device)

# asyncio.run(scan_mesh_devices())

MESH_DEVICE_MAC = "65:57:00:00:20:1F"
PROVISIONING_DATA = b"\x00\x01\x02\x03"


async def connect_to_mesh_device(mac_address, provisioning_data):
    # 连接Mesh设备
    async with BleakClient(mac_address) as client:
        # 连接成功后，获取provisioning service

        services = await client.get_services()
        provisioning_service = None
        for service in services:
            print('service', service.uuid)
            if service.uuid == PROVISIONING_SERVICE_UUID.lower():
                provisioning_service = service
                break
        if provisioning_service is None:
            print("Provisioning service not found")
            return
        # provisioning_service = await client.get_service_by_uuid(PROVISIONING_SERVICE_UUID)

        # 获取characteristic
        provisioning_data_in_characteristic = provisioning_service.get_characteristic(
            PROVISIONING_DATA_IN_UUID.lower())

        # 发送provisioning data
        await client.write_gatt_char(provisioning_data_in_characteristic.handle, provisioning_data)

        # 等待设备发送provisioning data并计算出session key和device key
        while True:
            # 获取characteristic
            provisioning_data_out_characteristic = provisioning_service.get_characteristic(
                PROVISIONING_DATA_IN_UUID.lower())
            print('prov_char', provisioning_data_out_characteristic)
            # 读取设备发送的provisioning data
            provisioning_data_out = await client.read_gatt_char(provisioning_data_out_characteristic.handle)

            print('prov', provisioning_data_out)

            if provisioning_data_out:
                # 计算session key和device key
                session_key = b"session_key"
                device_key = b"device_key"

                # 将session key和device key写入到设备中
                session_key_characteristic = await provisioning_service.get_characteristic("00002add-0000-1000-8000-00805f9b34fb")
                device_key_characteristic = await provisioning_service.get_characteristic("00002ade-0000-1000-8000-00805f9b34fb")

                await session_key_characteristic.write_value(session_key)
                await device_key_characteristic.write_value(device_key)

                # 将设备添加到Mesh网络中
                # ...

                # 完成provisioning
                break

asyncio.run(connect_to_mesh_device(MESH_DEVICE_MAC, PROVISIONING_DATA))
