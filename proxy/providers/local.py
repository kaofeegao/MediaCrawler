# -*- coding: utf-8 -*-
# Copyright (c) 2025 gaoyefei@yeah.net
#
# This file is part of MediaCrawler project.
# Repository: https://github.com/NanmiCoder/MediaCrawler/blob/main/proxy/providers/local.py
# GitHub: https://github.com/NanmiCoder
# Licensed under NON-COMMERCIAL LEARNING LICENSE 1.1
#

# 声明：本代码仅供学习和研究目的使用。使用者应遵守以下原则：
# 1. 不得用于任何商业用途。
# 2. 使用时应遵守目标平台的使用条款和robots.txt规则。
# 3. 不得进行大规模爬取或对平台造成运营干扰。
# 4. 应合理控制请求频率，避免给目标平台带来不必要的负担。
# 5. 不得用于任何非法或不当的用途。
#
# 详细许可条款请参阅项目根目录下的LICENSE文件。
# 使用本代码即表示您同意遵守上述原则和LICENSE中的所有条款。

# -*- coding: utf-8 -*-
# @Author  : gaoyefei@yeah.net
# @Time    : 2026/3/5 
# @Desc    : Local IP list provider implementation
import asyncio
import csv
import json
import re
from typing import List, Optional

from proxy.base_proxy import ProxyProvider
from proxy.types import IpInfoModel, ProviderNameEnum


class LocalIpProvider(ProxyProvider):
    """
    Local IP list provider that reads IPs from a local file
    """

    def __init__(self, file_path: str, format_type: str = "ip:port"):
        """
        Initialize local IP provider
        :param file_path: Path to the local IP list file
        :param format_type: Format of the IP list (ip:port, ip:port:user:pass, or json)
        """
        self.file_path = file_path
        self.format_type = format_type

    async def get_proxy(self, num: int) -> List[IpInfoModel]:
        """
        Get proxy IPs from local file
        :param num: Number of IPs to extract
        :return: List of IpInfoModel objects
        """
        ips = await self._read_local_ips()
        return ips[:num]  # Return up to num IPs

    async def _read_local_ips(self) -> List[IpInfoModel]:
        """
        Read IPs from local file
        :return: List of IpInfoModel objects
        """
        try:
            if self.file_path.endswith('.json'):
                return await self._read_json_file()
            elif self.file_path.endswith('.csv'):
                return await self._read_csv_file()
            else:
                return await self._read_text_file()
        except Exception as e:
            raise Exception(f"[LocalIpProvider._read_local_ips] Error reading local IP file: {e}")

    async def _read_text_file(self) -> List[IpInfoModel]:
        """
        Read IPs from text file (one IP per line)
        :return: List of IpInfoModel objects
        """
        ips = []
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    ip_model = self._parse_ip_line(line)
                    if ip_model:
                        ips.append(ip_model)
        except Exception as e:
            raise Exception(f"[LocalIpProvider._read_text_file] Error reading text file: {e}")
        return ips

    async def _read_json_file(self) -> List[IpInfoModel]:
        """
        Read IPs from JSON file
        :return: List of IpInfoModel objects
        """
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return [IpInfoModel(**item) for item in data if self._validate_ip_model(item)]
                else:
                    raise Exception("[LocalIpProvider._read_json_file] JSON data is not a list")
        except Exception as e:
            raise Exception(f"[LocalIpProvider._read_json_file] Error reading JSON file: {e}")

    async def _read_csv_file(self) -> List[IpInfoModel]:
        """
        Read IPs from CSV file
        :return: List of IpInfoModel objects
        """
        ips = []
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if not row or row[0].startswith('#'):
                        continue
                    line = ','.join(row).strip()
                    ip_model = self._parse_ip_line(line)
                    if ip_model:
                        ips.append(ip_model)
        except Exception as e:
            raise Exception(f"[LocalIpProvider._read_csv_file] Error reading CSV file: {e}")
        return ips

    def _parse_ip_line(self, line: str) -> Optional[IpInfoModel]:
        """
        Parse a single line from the IP file
        :param line: Line containing IP information
        :return: IpInfoModel object or None if invalid
        """
        if self.format_type == "ip:port":
            return self._parse_ip_port(line)
        elif self.format_type == "ip:port:user:pass":
            return self._parse_ip_port_user_pass(line)
        else:
            raise Exception(f"[LocalIpProvider._parse_ip_line] Unsupported format type: {self.format_type}")

    def _parse_ip_port(self, line: str) -> Optional[IpInfoModel]:
        """
        Parse IP:PORT format
        :param line: Line in format "ip:port"
        :return: IpInfoModel object or None if invalid
        """
        parts = line.split(':')
        if len(parts) < 2:
            return None
        ip = parts[0]
        try:
            port = int(parts[1])
            user = ""
            password = ""
            if len(parts) > 2:
                user = parts[2] if len(parts) > 2 else ""
                password = parts[3] if len(parts) > 3 else ""
            # Validate IP address format
            if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip):
                return None
            return IpInfoModel(ip=ip, port=port, user=user, password=password)
        except ValueError:
            return None

    def _parse_ip_port_user_pass(self, line: str) -> Optional[IpInfoModel]:
        """
        Parse IP:PORT:USER:PASS format
        :param line: Line in format "ip:port:user:pass"
        :return: IpInfoModel object or None if invalid
        """
        parts = line.split(':')
        if len(parts) < 2:
            return None
        ip = parts[0]
        try:
            port = int(parts[1])
            user = parts[2] if len(parts) > 2 else ""
            password = parts[3] if len(parts) > 3 else ""
            return IpInfoModel(ip=ip, port=port, user=user, password=password)
        except ValueError:
            return None

    def _validate_ip_model(self, data: dict) -> bool:
        """
        Validate IP model data
        :param data: Dictionary containing IP data
        :return: True if valid, False otherwise
        """
        required_fields = ['ip', 'port']
        for field in required_fields:
            if field not in data:
                return False
        try:
            int(data['port'])
            return True
        except (ValueError, TypeError):
            return False

def new_local_ip_provider(file_path: str = "", format_type: str = "ip:port"):
    """
    Create a new local IP provider
    :param file_path: Path to local IP list file
    :param format_type: Format of IP list (ip:port or ip:port:user:pass)
    :return: LocalIpProvider instance
    """
    return LocalIpProvider(file_path, format_type)