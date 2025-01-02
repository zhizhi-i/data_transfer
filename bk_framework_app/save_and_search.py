# -*- coding: utf-8 -*-

import json
import os
from datetime import datetime
# import schedule
from .librenms import GetLibrenmsInfo
from blueapps.utils.logger import logger
from blueapps.account.decorators import login_exempt
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.http.response import JsonResponse
from django.views.decorators.http import require_http_methods


# 获取当天日期的文件名
def get_filename():
    today_str = datetime.now().strftime("%Y-%m-%d")
    base_path = "/var/cache/"  # 固定文件路径
    logger.error(f"文件存放目录:{base_path}")
    return os.path.join(base_path, f"librenms_{today_str}.json")

# 模拟获取设备信息的函数
def update_device_info():
    librenms_info = GetLibrenmsInfo()
    librenms_devices_info = librenms_info.assembly_data()
    return librenms_devices_info

# 更新文件，每天生成以当天日期命名的文件

@login_exempt
def update_local_file(request):
    filename = get_filename()
    logger.info(f"文件存放路径:{filename}")
    try:
        # 更新文件内容
        devices_info = update_device_info()
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(devices_info, f, indent=4, ensure_ascii=False)
        # print(f"端口信息已成功更新并保存到文件：{filename}")
        return JsonResponse({
            "result": True,
            "message": "已缓存最新的librenms数据"
            })
    except Exception as e:
        # print(f"更新文件时出错：{e}")
        return JsonResponse({
            "result": False,
            "message": f"更新文件时出错：{e}"
            })


# 读取文件并返回内容
def read_file_content():
    filename = get_filename()
    try:
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                loaded_data = json.load(f)
                return loaded_data
        else:
            return {"error": "文件不存在"}
    except Exception as e:
        return {"error": f"读取文件时出错：{e}"}

# 根据 IP 查找信息
@login_exempt
@csrf_exempt
@require_http_methods(["GET"])
def get_info_by_ip(request):
    ip = request.GET.get("ip")
    if not ip:
        return JsonResponse({"error": "缺少参数: ip"}, status=400)

    data = read_file_content()
    if not data:
        return JsonResponse({"error": "文件不存在或读取失败"}, status=500)

    result = next((item for item in data if item["ip"] == ip), None)
    if result:
        result.pop("ip", None)
        return JsonResponse(result, safe=False)
    else:
        return JsonResponse({"error": "未找到指定 IP 的信息"}, status=404)


