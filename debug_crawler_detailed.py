#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细的爬虫调试脚本

用于测试GitHub trending爬虫的具体错误信息。
"""

import asyncio
import aiohttp
from app.crawler.github_crawler import GitHubTrendingCrawler
from app.config import get_settings

async def test_crawler_detailed():
    """详细测试爬虫功能"""
    settings = get_settings()
    crawler = GitHubTrendingCrawler()
    
    print(f"🔧 配置信息:")
    print(f"   - GitHub URL: {settings.github_trending_url}")
    print(f"   - User-Agent: {settings.user_agent}")
    print(f"   - 超时时间: {settings.request_timeout}秒")
    print(f"   - 最大重试: {settings.max_retries}次")
    print()
    
    # 测试直接HTTP请求
    print("🌐 测试直接HTTP请求...")
    try:
        async with aiohttp.ClientSession(**crawler.session_config) as session:
            url = "https://github.com/trending"
            print(f"   请求URL: {url}")
            
            async with session.get(url) as response:
                print(f"   状态码: {response.status}")
                print(f"   响应头: {dict(response.headers)}")
                
                if response.status == 200:
                    content = await response.text()
                    print(f"   内容长度: {len(content)}")
                    print(f"   内容预览: {content[:200]}...")
                else:
                    error_text = await response.text()
                    print(f"   错误内容: {error_text}")
                    
    except Exception as e:
        print(f"   ❌ HTTP请求失败: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # 测试爬虫方法
    print("🕷️ 测试爬虫方法...")
    try:
        repositories = await crawler.fetch_trending(limit=5)
        print(f"   ✅ 成功获取 {len(repositories)} 个仓库")
        
        for i, repo in enumerate(repositories[:3], 1):
            print(f"   {i}. {repo.name} - ⭐{repo.stars}")
            
    except Exception as e:
        print(f"   ❌ 爬虫方法失败: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_crawler_detailed())