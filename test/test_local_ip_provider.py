# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Repository: https://github.com/NanmiCoder/MediaCrawler/blob/main/test/test_local_ip_provider.py
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
# @Author  : relakkes@gmail.com
# @Time    : 2025/3/4 19:37
# @Desc    : Test for local IP provider
import asyncio
import os
import tempfile
from typing import List

import pytest
import pytest_asyncio
from proxy.providers import LocalIpProvider
from proxy.types import IpInfoModel


@pytest_asyncio.fixture
async def temp_ip_file():
    """Create a temporary IP list file for testing"""
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
    temp_file.write("""# Test IP list
192.168.1.1:8080
10.0.0.1:3128
172.16.0.1:8080:user:password
""")
    temp_file.close()
    yield temp_file.name
    os.unlink(temp_file.name)


@pytest_asyncio.fixture
async def temp_json_file():
    """Create a temporary JSON IP list file for testing"""
    json_content = """[
        {"ip": "192.168.1.1", "port": 8080, "user": "", "password": ""},
        {"ip": "10.0.0.1", "port": 3128, "user": "", "password": ""}
    ]"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        f.write(json_content)
        json_file = f.name
    yield json_file
    os.unlink(json_file)


@pytest_asyncio.fixture
async def temp_invalid_file():
    """Create a temporary invalid IP list file for testing"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("invalid_ip:8080\n")
        invalid_file = f.name
    yield invalid_file
    os.unlink(invalid_file)


@pytest_asyncio.fixture
async def temp_empty_file():
    """Create a temporary empty IP list file for testing"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        empty_file = f.name
    yield empty_file
    os.unlink(empty_file)


@pytest_asyncio.fixture
async def temp_comment_file():
    """Create a temporary IP list file with comments for testing"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("""# Comment line
192.168.1.1:8080
# Another comment
10.0.0.1:3128
""")
        comment_file = f.name
    yield comment_file
    os.unlink(comment_file)


@pytest_asyncio.fixture
async def local_ip_provider():
    """Create a local IP provider fixture"""
    return LocalIpProvider


async def test_local_ip_provider_basic(local_ip_provider, temp_ip_file):
    """Test basic functionality of local IP provider"""
    provider = local_ip_provider(temp_ip_file, format_type="ip:port")
    ips = await provider.get_proxy(10)
    assert len(ips) == 3
    assert all(isinstance(ip, IpInfoModel) for ip in ips)
    assert ips[0].ip == "192.168.1.1"
    assert ips[0].port == 8080
    assert ips[0].user == ""
    assert ips[0].password == ""


async def test_local_ip_provider_with_auth(local_ip_provider, temp_ip_file):
    """Test local IP provider with authentication format"""
    provider = local_ip_provider(temp_ip_file, format_type="ip:port:user:pass")
    ips = await provider.get_proxy(10)
    assert len(ips) == 3
    assert ips[2].ip == "172.16.0.1"
    assert ips[2].port == 8080
    assert ips[2].user == "user"
    assert ips[2].password == "password"


async def test_local_ip_provider_json(local_ip_provider, temp_json_file):
    """Test local IP provider with JSON format"""
    provider = local_ip_provider(temp_json_file, format_type="ip:port")
    ips = await provider.get_proxy(10)
    assert len(ips) == 2
    assert ips[0].ip == "192.168.1.1"
    assert ips[0].port == 8080


async def test_local_ip_provider_invalid_format(local_ip_provider, temp_invalid_file):
    """Test local IP provider with invalid format"""
    provider = local_ip_provider(temp_invalid_file, format_type="ip:port")
    ips = await provider.get_proxy(10)
    assert len(ips) == 0  # Should return empty list for invalid IPs


async def test_local_ip_provider_empty_file(local_ip_provider, temp_empty_file):
    """Test local IP provider with empty file"""
    provider = local_ip_provider(temp_empty_file, format_type="ip:port")
    ips = await provider.get_proxy(10)
    assert len(ips) == 0


async def test_local_ip_provider_comments(local_ip_provider, temp_comment_file):
    """Test local IP provider with comments in file"""
    provider = local_ip_provider(temp_comment_file, format_type="ip:port")
    ips = await provider.get_proxy(10)
    assert len(ips) == 2