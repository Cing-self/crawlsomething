#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API测试脚本

用于测试GitHub Trending API的基本功能
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

async def test_api():
    """测试API功能"""
    async with aiohttp.ClientSession() as session:
        print("🧪 开始测试 GitHub Trending API")
        print("=" * 50)
        
        # 测试健康检查
        print("\n1. 测试健康检查...")
        try:
            async with session.get(f"{BASE_URL}/health") as response:
                data = await response.json()
                print(f"✅ 健康检查: {response.status} - {data['status']}")
        except Exception as e:
            print(f"❌ 健康检查失败: {e}")
            return
        
        # 测试根路径
        print("\n2. 测试根路径...")
        try:
            async with session.get(f"{BASE_URL}/") as response:
                data = await response.json()
                print(f"✅ 根路径: {response.status} - {data['name']} v{data['version']}")
        except Exception as e:
            print(f"❌ 根路径测试失败: {e}")
        
        # 测试获取支持的语言列表
        print("\n3. 测试获取支持的语言列表...")
        try:
            async with session.get(f"{BASE_URL}/api/trending/languages/supported") as response:
                data = await response.json()
                if response.status == 200:
                    languages = data if isinstance(data, list) else data.get('data', [])
                    print(f"✅ 支持的语言数量: {len(languages)}")
                    print(f"   前5个语言: {languages[:5]}")
                else:
                    print(f"❌ 获取语言列表失败: {response.status}")
        except Exception as e:
            print(f"❌ 获取语言列表失败: {e}")
        
        # 测试获取trending仓库（默认参数）
        print("\n4. 测试获取trending仓库（默认参数）...")
        try:
            async with session.get(f"{BASE_URL}/api/trending") as response:
                data = await response.json()
                if response.status == 200:
                    repos = data.get('repositories', data.get('data', []))
                    print(f"✅ 获取到 {len(repos)} 个trending仓库")
                    if repos:
                        first_repo = repos[0]
                        print(f"   第一个仓库: {first_repo.get('name', 'N/A')}")
                        print(f"   描述: {first_repo.get('description', 'N/A')[:50]}...")
                        print(f"   星标数: {first_repo.get('stars', 'N/A')}")
                else:
                    print(f"❌ 获取trending仓库失败: {response.status}")
                    print(f"   错误信息: {data.get('message', 'Unknown error')}")
        except Exception as e:
            print(f"❌ 获取trending仓库失败: {e}")
        
        # 测试获取Python语言的trending仓库
        print("\n5. 测试获取Python语言的trending仓库...")
        try:
            async with session.get(f"{BASE_URL}/api/trending/python") as response:
                data = await response.json()
                if response.status == 200:
                    repos = data.get('repositories', data.get('data', []))
                    print(f"✅ 获取到 {len(repos)} 个Python trending仓库")
                    if repos:
                        first_repo = repos[0]
                        print(f"   第一个仓库: {first_repo.get('name', 'N/A')}")
                        print(f"   语言: {first_repo.get('language', 'N/A')}")
                else:
                    print(f"❌ 获取Python trending仓库失败: {response.status}")
        except Exception as e:
            print(f"❌ 获取Python trending仓库失败: {e}")
        
        # 测试带参数的请求
        print("\n6. 测试带参数的请求（weekly, JavaScript）...")
        try:
            params = {
                'since': 'weekly',
                'language': 'javascript'
            }
            async with session.get(f"{BASE_URL}/api/trending", params=params) as response:
                data = await response.json()
                if response.status == 200:
                    repos = data.get('repositories', data.get('data', []))
                    print(f"✅ 获取到 {len(repos)} 个JavaScript weekly trending仓库")
                else:
                    print(f"❌ 获取带参数的trending仓库失败: {response.status}")
        except Exception as e:
            print(f"❌ 获取带参数的trending仓库失败: {e}")
        
        print("\n" + "=" * 50)
        print("🎉 API测试完成！")

def main():
    """主函数"""
    print("请确保服务已启动: python run.py")
    print("按Enter键开始测试...")
    input()
    
    try:
        asyncio.run(test_api())
    except KeyboardInterrupt:
        print("\n\n⏹️  测试被用户中断")
    except Exception as e:
        print(f"\n\n❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    main()