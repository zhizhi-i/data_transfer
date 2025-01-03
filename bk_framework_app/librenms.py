# -*- coding: utf-8 -*-


import requests
from blueapps.utils.logger import logger
import concurrent.futures
from collections import defaultdict
import re


# 定义API的URL和认证信息
base_url = "http://librenms.polar.com/api/v0"
api_token = '67ae076b7de19d7dedc09498d647f05b'

# 设置请求头
headers = {
    'X-Auth-Token': api_token,
    'Accept': 'application/json'
}


class GetLibrenmsInfo(object):
    base_url = "http://librenms.polar.com/api/v0"
    api_token = '67ae076b7de19d7dedc09498d647f05b'
    headers = {
        'X-Auth-Token': api_token,
        'Accept': 'application/json'
    }
    
    # 定义匹配规则
    mapping_rules = {
        "psu": "power supply",
        "fan": "fan"
    }

    def __init__(self):
        pass

    # 通用接口请求函数
    def _request(self, url, method='GET', data=None, params=None,headers=headers):
        try:
            response = requests.request(method, url, json=data, params=params, headers=headers ,verify=False)
            response.raise_for_status()  
            return response.json() 
        except requests.RequestException as e:
            logger.error(f"request error:{str(e)}")
            return {'result':False, 'error':'请求错误','message': str(e)}
        except Exception as e:
            logger.error(f"request error:{str(e)}")
            return {'result':False, 'error':'未知错误','message': str(e)}

    # 格式化输出名称和编号
    def _normalize_name(self,name: str) -> str:
        name = name.lower().strip()
        match = re.search(r'(\d+)$', name)
        for key, value in self.mapping_rules.items():
            name = re.sub(rf'\b{key}\b', value, name)  # 替换关键字
        return name,match.group(1) if match else ""
        
    # 根据主设备和组件名称查询组件id
    def _get_sensor_id(self,device_id,device_name):
        url = f"{self.base_url}/devices/{device_id}/health/device_state/"
        response = self._request(url=url,method="get")
        graphs = response.get("graphs",[])
        for graph in graphs:
            # 将两个值格式化之后的数据进行对比
            if self._normalize_name(graph["desc"]) == self._normalize_name(device_name):
                return graph["sensor_id"]

        return 0
            
    # 根据设备名称和组件id查询组件状态
    def _get_device_status(self,device_id,sensor_id):
        url = f"{self.base_url}/devices/{device_id}/health/device_state/{sensor_id}"
        response = self._request(url=url,method="get")
        graphs = response.get("graphs",[])
        for graph in graphs:
            if graph["sensor_id"] == sensor_id:
                sensor_current = graph.get("sensor_current")
                if sensor_current is not None and sensor_current == 1:
                    return "normal"
                else:
                    return "absent"

    # 获取设备风扇和电源信息
    def get_entphysical_info(self,device_id,entphysicalclass):
        fan_info = []
        psu_info = []
        url = f"{self.base_url}/inventory/{device_id}/all"
        response = self._request(url=url,method="get")
        inventorys = response.get('inventory',[]) # 获取指定设备的硬件列表
        if inventorys != []:
            for inventory in inventorys:
                if inventory["entPhysicalClass"] == "fan" and entphysicalclass == "fan":
                    sensor_descr = inventory.get("entPhysicalName","")
                    fan_info.append({
                        "fanSN": inventory.get("entPhysicalSerialNum",""),
                        "fanNum": self._normalize_name(inventory.get("entPhysicalName",""))[1],
                        "fanGroove": inventory.get("entPhysicalName",""),
                        "fanStatus": self._get_device_status(device_id,self._get_sensor_id(device_id,sensor_descr)),
                    })
                
                elif inventory["entPhysicalClass"] == "powerSupply" and entphysicalclass == "powerSupply":
                    sensor_descr = inventory.get("entPhysicalName","")
                    psu_info.append({
                        "powerSN": inventory.get("entPhysicalSerialNum",""),
                        "powerNum": self._normalize_name(inventory.get("entPhysicalName",""))[1],
                        "powderGroove": inventory.get("entPhysicalName",""),
                        "powerStatus": self._get_device_status(device_id,self._get_sensor_id(device_id,sensor_descr)),
                    })

        
        return fan_info,psu_info
    
    # 获取所有端口信息
    def _get_all_ports(self):
        url = f"{self.base_url}/ports"  
        response = self._request(url=url,method="get")
        ports_info = response.get("ports",[])
        # 获取所有端口的id
        ports_id_list = [port_info["port_id"] for port_info in ports_info]
        logger.info(f"get_ports_list:{ports_id_list}")
        return ports_id_list

    # 返回所有端口信息，并根据设备id分组
    def get_ports_info(self,ports_id_list):
        all_ports_info = defaultdict(list)

        def get_port_info(port_id):
            port_url = f"{base_url}/ports/{port_id}"
            response = self._request(url=port_url, method="get")
            ports_info = response.get("port", [])
            
            result = []
            for port_info in ports_info:
                device_id = port_info.get("device_id", "unknown")

                if "Gig" not in port_info["ifName"]:
                    continue
                
                # 获取光模块信息
                trans_url = f"{base_url}/ports/{port_id}/transceiver"
                trans_response = self._request(url=trans_url, method="get")
                trans_info = trans_response.get("transceivers", [])
                
                # 整合光模块信息
                trans_info_list = [
                    {
                        "opticalModuleSn": tran_info.get("serial", ""),
                        "opticalModuleType": tran_info.get("type", ""),
                        "opticalModuleModel": tran_info.get("model", ""),
                        "opticalModuleManufactur": tran_info.get("vendor", "")
                    }
                    for tran_info in trans_info
                ]
                
                if not trans_info_list:
                    trans_info_list.append({
                        "opticalModuleSn": "",
                        "opticalModuleType": "",
                        "opticalModuleModel": "",
                        "opticalModuleManufactur": ""
                    })
                
                result.append({
                    "portNum": port_info.get("ifName", ""),
                    "portInfo": {
                        "MTU": "" if port_info.get("ifMtu", 0) is None or port_info.get("ifMtu", 0) >= 10000 else port_info.get("ifMtu", 0),
                        "portSpeed": f'{(port_info.get("ifSpeed") or 0) / 1000000000:.2f} Gbps',
                        "portStatus": port_info.get("ifOperStatus", "")
                    },
                    "opticalModuleInfo": trans_info_list
                })
            return device_id,result

        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            future_to_port = {executor.submit(get_port_info, port_id): port_id for port_id in ports_id_list}
            for future in concurrent.futures.as_completed(future_to_port):
                try:
                    device_id, port_data_list = future.result()
                    all_ports_info[device_id].extend(port_data_list)
                except Exception as e:
                    print(f"Error fetching port data: {e}")

        return all_ports_info
    
    # 获取非ping类型设备的设备id
    def _get_devices_id(self):
        url = f"{self.base_url}/devices"  
        response = self._request(url=url,method="get")
        devices_info = response.get("devices",[])
        devices_id_list = [device_info["device_id"] for device_info in devices_info if device_info["os"] != "ping"]
        return devices_id_list

    # 根据设备id获取设备基础信息
    def get_base_info(self,device_id):
        url = f"{self.base_url}/devices/{device_id}"
        response = self._request(url=url,method="get")
        device_info =response.get("devices",[])[0]
        return {
            "SN": device_info.get("serial",""),
            "type": device_info.get("hardware",""),
            "model": ""
        },device_info.get("ip","")
    
    # 引擎板暂无获取逻辑
    def get_engine_info(self):
        return {
            "engineSN": "",
            "engineNum": "",
            "engineGroove": "",
            "engineStatus": ""           
        }
    
    # 业务板暂无获取逻辑
    def get_business_info(self):
        return {
            "businessSN": "",
            "businessNum": "",
            "businessGroove": "",
            "businessStatus": ""        
        }
    
    # 交换板暂无获取逻辑
    def get_exchange_info(self):
        return {
            "exchangeSN": "",
            "exchangeNum": "",
            "exchangeGroove": "",
            "exchangeStatus": ""     
        }
    
    # IB信息,librenms无IB设备信息
    def get_ib_info(self):
        return {
            "SN": "",
            "LID": "",
            "GUID": ""  
        }
    
    # 数据组装
    def assembly_data(self):
        devices_info = []
        devices_id_list = self._get_devices_id()
        ports_id_list = self._get_all_ports()
        ports_info = self.get_ports_info(ports_id_list)
        for device_id in devices_id_list:
            devices_info.append({
                "ip": self.get_base_info(device_id)[1],
                "IBInfo": self.get_ib_info(),
                "chassisInfo":{
                    "fanInfo": self.get_entphysical_info(device_id,"fan")[0],
                    "powerInfo": self.get_entphysical_info(device_id,"powerSupply")[1],
                    "baseInfo": self.get_base_info(device_id)[0],
                    "engineInfo": self.get_engine_info(),
                    "businessInfo": self.get_business_info(),
                    "exchangeInfo": self.get_exchange_info()
                },
                "portAndModelInfo": ports_info.get(device_id,[]),
                "topologyInfo": {},
                "consoleInfo": {
                    "console": "",
                    "consolePick": ""
                }
            })
        
        return devices_info