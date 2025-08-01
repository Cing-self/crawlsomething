#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试爬虫脚本

用于测试GitHub爬虫的基本功能，帮助诊断问题。
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.crawler.github_crawler import GitHubTrendingCrawler
from app.config import get_settings
from loguru import logger


async def test_crawler():
    """测试爬虫功能"""
    settings = get_settings()
    crawler = GitHubTrendingCrawler()
    
    print("🔧 爬虫配置信息:")
    print(f"   GitHub基础URL: {settings.github_base_url}")
    print(f"   Trending URL: {settings.github_trending_url}")
    print(f"   请求超时: {settings.request_timeout}秒")
    print(f"   最大重试: {settings.max_retries}次")
    print(f"   User-Agent: {settings.user_agent[:50]}...")
    print()
    
    # 1. 测试健康检查
    print("1. 测试GitHub连接...")
    try:
        health = await crawler.health_check()
        print(f"   健康状态: {health}")
        if not health.get('github_accessible', False):
            print("   ❌ GitHub不可访问，请检查网络连接")
            return
        else:
            print("   ✅ GitHub连接正常")
    except Exception as e:
        print(f"   ❌ 健康检查失败: {e}")
        return
    
    print()
    
    # 2. 测试获取trending页面
    print("2. 测试获取trending页面...")
    try:
        url = crawler._build_url(None, "daily")
        print(f"   请求URL: {url}")
        
        import aiohttp
        async with aiohttp.ClientSession(**crawler.session_config) as session:
            html_content = await crawler._fetch_page(session, url)
            print(f"   页面内容长度: {len(html_content)}")
            
            # 检查页面内容
            if "trending" in html_content.lower():
                print("   ✅ 页面包含trending内容")
            else:
                print("   ❌ 页面不包含trending内容")
                
            # 检查是否有仓库列表
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            repo_articles = soup.find_all('article', class_='Box-row')
            print(f"   找到仓库数量: {len(repo_articles)}")
            
            if len(repo_articles) == 0:
                print("   ❌ 未找到仓库列表，可能页面结构已变化")
                # 保存页面内容用于调试
                with open('debug_page.html', 'w', encoding='utf-8') as f:
                    f.write(html_content)
                print("   💾 页面内容已保存到 debug_page.html")
            else:
                print("   ✅ 找到仓库列表")
                
    except Exception as e:
        print(f"   ❌ 获取页面失败: {e}")
        return
    
    print()
    
    # 3. 测试完整爬取流程
    print("3. 测试完整爬取流程...")
    try:
        repositories = await crawler.fetch_trending(limit=5)
        print(f"   成功爬取 {len(repositories)} 个仓库")
        
        if repositories:
            print("   前3个仓库:")
            for i, repo in enumerate(repositories[:3]):
                print(f"     {i+1}. {repo.name} - {repo.stars} stars")
            print("   ✅ 爬取成功")
        else:
            print("   ❌ 未爬取到任何仓库")
            
    except Exception as e:
        print(f"   ❌ 爬取失败: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("🎉 调试完成！")


if __name__ == "__main__":
    asyncio.run(test_crawler())