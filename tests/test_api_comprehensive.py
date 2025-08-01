#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全面的API单元测试

测试GitHub Trending API的所有功能和边界情况
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any, List

BASE_URL = "http://localhost:8000"

class TestGitHubTrendingAPI:
    """GitHub Trending API测试类"""
    
    async def test_health_check(self, session):
        """测试健康检查接口"""
        async with session.get(f"{BASE_URL}/health") as response:
            assert response.status == 200
            data = await response.json()
            assert data["status"] == "healthy"
            assert "timestamp" in data
    
    async def test_root_endpoint(self, session):
        """测试根路径接口"""
        async with session.get(f"{BASE_URL}/") as response:
            assert response.status == 200
            data = await response.json()
            assert data["name"] == "GitHub Trending Crawler"
            assert data["version"] == "1.0.0"
            assert "status" in data
    
    async def test_supported_languages(self, session):
        """测试获取支持的编程语言列表"""
        async with session.get(f"{BASE_URL}/api/trending/languages/supported") as response:
            assert response.status == 200
            data = await response.json()
            assert isinstance(data, list)
            assert len(data) > 0
            # 检查常见语言是否存在
            common_languages = ["python", "javascript", "java", "typescript"]
            for lang in common_languages:
                assert lang in data
    
    async def test_trending_default(self, session):
        """测试获取trending仓库（默认参数）"""
        async with session.get(f"{BASE_URL}/api/trending/") as response:
            assert response.status == 200
            data = await response.json()
            assert data["success"] is True
            assert "repositories" in data
            assert isinstance(data["repositories"], list)
            
            # 如果有仓库数据，验证结构
            if data["repositories"]:
                repo = data["repositories"][0]
                required_fields = ["name", "url", "description", "stars", "forks", 
                                 "language", "stars_today", "owner", "repo_name"]
                for field in required_fields:
                    assert field in repo
    
    async def test_trending_with_language(self, session):
        """测试获取指定语言的trending仓库"""
        language = "python"
        async with session.get(f"{BASE_URL}/api/trending/{language}") as response:
            assert response.status == 200
            data = await response.json()
            assert data["success"] is True
            assert "repositories" in data
            
            # 验证返回的仓库都是指定语言（如果有数据）
            if data["repositories"]:
                for repo in data["repositories"]:
                    if repo.get("language"):
                        assert repo["language"].lower() == language.lower()
    
    async def test_trending_with_parameters(self, session):
        """测试带参数的trending请求"""
        params = {
            "since": "weekly",
            "limit": 5
        }
        async with session.get(f"{BASE_URL}/api/trending/", params=params) as response:
            assert response.status == 200
            data = await response.json()
            assert data["success"] is True
            assert "repositories" in data
            
            # 验证返回数量不超过限制
            if data["repositories"]:
                assert len(data["repositories"]) <= 5
    
    async def test_trending_invalid_language(self, session):
        """测试无效语言参数"""
        invalid_language = "invalidlanguage123"
        async with session.get(f"{BASE_URL}/api/trending/{invalid_language}") as response:
            # 应该返回200但可能没有数据，或者返回错误
            assert response.status in [200, 400, 404]
    
    async def test_trending_invalid_since_parameter(self, session):
        """测试无效的since参数"""
        params = {"since": "invalid_period"}
        async with session.get(f"{BASE_URL}/api/trending/", params=params) as response:
            # 应该返回422验证错误、400错误或使用默认值
            assert response.status in [200, 400, 422]
    
    async def test_trending_health_check(self, session):
        """测试trending服务健康检查"""
        async with session.get(f"{BASE_URL}/api/trending/health") as response:
            # 健康检查可能返回200或500，都是正常的
            assert response.status in [200, 500]
            data = await response.json()
            assert "status" in data
            assert "timestamp" in data
            assert "version" in data
    
    async def test_trending_refresh(self, session):
        """测试手动刷新trending数据"""
        payload = {
            "language": "python",
            "since": "daily",
            "limit": 5
        }
        async with session.post(f"{BASE_URL}/api/trending/refresh", json=payload) as response:
            assert response.status == 200
            data = await response.json()
            assert data["success"] is True
            assert "repositories" in data
    
    async def test_response_headers(self, session):
        """测试响应头"""
        async with session.get(f"{BASE_URL}/api/trending/") as response:
            assert response.status == 200
            # 检查自定义响应头
            assert "x-process-time" in response.headers
            assert "x-request-id" in response.headers
    
    async def test_concurrent_requests(self, session):
        """测试并发请求"""
        # 创建多个并发请求
        tasks = []
        for _ in range(5):
            task = session.get(f"{BASE_URL}/api/trending/")
            tasks.append(task)
        
        # 等待所有请求完成
        responses = await asyncio.gather(*tasks)
        
        # 验证所有响应
        for response in responses:
            assert response.status == 200
            data = await response.json()
            assert data["success"] is True
            response.close()


async def run_comprehensive_tests():
    """运行全面测试"""
    print("🧪 开始运行全面的API测试")
    print("=" * 60)
    
    test_instance = TestGitHubTrendingAPI()
    
    async with aiohttp.ClientSession() as session:
        tests = [
            ("健康检查", test_instance.test_health_check),
            ("根路径", test_instance.test_root_endpoint),
            ("支持的语言列表", test_instance.test_supported_languages),
            ("默认trending", test_instance.test_trending_default),
            ("指定语言trending", test_instance.test_trending_with_language),
            ("带参数trending", test_instance.test_trending_with_parameters),
            ("无效语言参数", test_instance.test_trending_invalid_language),
            ("无效since参数", test_instance.test_trending_invalid_since_parameter),
            ("trending健康检查", test_instance.test_trending_health_check),
            ("手动刷新", test_instance.test_trending_refresh),
            ("响应头检查", test_instance.test_response_headers),
            ("并发请求", test_instance.test_concurrent_requests),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            try:
                print(f"\n🔍 测试: {test_name}")
                await test_func(session)
                print(f"✅ {test_name} - 通过")
                passed += 1
            except Exception as e:
                print(f"❌ {test_name} - 失败: {e}")
                failed += 1
    
    print("\n" + "=" * 60)
    print(f"🎯 测试结果: {passed} 通过, {failed} 失败")
    print(f"📊 成功率: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        print("🎉 所有测试都通过了！")
    else:
        print(f"⚠️  有 {failed} 个测试失败，请检查相关功能")


if __name__ == "__main__":
    print("请确保服务已启动: python run.py")
    input("按Enter键开始全面测试...")
    asyncio.run(run_comprehensive_tests())