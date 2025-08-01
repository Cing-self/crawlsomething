# -*- coding: utf-8 -*-
"""
GitHub Trending爬虫模块

实现GitHub trending页面的数据爬取功能。
使用aiohttp进行异步HTTP请求，BeautifulSoup解析HTML内容。
支持按时间范围和编程语言筛选trending仓库。
"""

import re
import asyncio
import random
from typing import List, Optional, Dict, Any
from datetime import datetime
from urllib.parse import urljoin, urlparse

import aiohttp
from bs4 import BeautifulSoup
from loguru import logger

from app.config import get_settings
from app.schemas.trending import TrendingRepository

settings = get_settings()


class GitHubTrendingCrawler:
    """GitHub Trending爬虫类
    
    负责爬取GitHub trending页面数据，解析仓库信息。
    支持异步操作和错误重试机制。
    """
    
    def __init__(self):
        """初始化爬虫"""
        self.base_url = settings.github_base_url
        self.trending_url = settings.github_trending_url
        self.timeout = settings.request_timeout
        self.max_retries = settings.max_retries
        self.delay = settings.request_delay
        self.min_delay = settings.min_delay
        self.max_delay = settings.max_delay
        
        # 多个User-Agent轮换
        self.user_agents = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        
        # HTTP会话配置
        self.session_config = {
            'timeout': aiohttp.ClientTimeout(total=self.timeout),
            'headers': {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0'
            }
        }
    
    async def fetch_trending(
        self, 
        language: Optional[str] = None, 
        since: str = "daily",
        limit: int = 25
    ) -> List[TrendingRepository]:
        """获取trending仓库列表
        
        Args:
            language: 编程语言筛选，如 'python', 'javascript'
            since: 时间范围，'daily', 'weekly', 'monthly'
            limit: 返回数量限制
            
        Returns:
            List[TrendingRepository]: trending仓库列表
            
        Raises:
            Exception: 爬取失败时抛出异常
        """
        url = self._build_url(language, since)
        logger.info(f"开始爬取GitHub trending: {url}")
        
        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession(**self.session_config) as session:
                    html_content = await self._fetch_page(session, url)
                    repositories = self._parse_repositories(html_content)
                    
                    # 应用数量限制
                    if limit and len(repositories) > limit:
                        repositories = repositories[:limit]
                    
                    logger.info(f"成功爬取 {len(repositories)} 个仓库")
                    return repositories
                    
            except Exception as e:
                logger.warning(f"爬取失败 (尝试 {attempt + 1}/{self.max_retries}): {str(e)}")
                if attempt < self.max_retries - 1:
                    # 指数退避 + 随机抖动
                    base_delay = self.delay * (2 ** attempt)
                    jitter = random.uniform(0.5, 1.5)
                    retry_delay = base_delay * jitter
                    logger.info(f"等待 {retry_delay:.2f} 秒后重试")
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error(f"爬取最终失败: {str(e)}")
                    raise
        
        return []
    
    def _build_url(self, language: Optional[str], since: str) -> str:
        """构建trending页面URL
        
        Args:
            language: 编程语言
            since: 时间范围
            
        Returns:
            str: 完整的URL
        """
        url = self.trending_url
        
        # 添加语言参数
        if language:
            url = f"{url}/{language.lower()}"
        
        # 添加时间范围参数
        url = f"{url}?since={since}"
        
        return url
    
    async def _fetch_page(self, session: aiohttp.ClientSession, url: str) -> str:
        """获取页面HTML内容
        
        Args:
            session: aiohttp会话
            url: 目标URL
            
        Returns:
            str: HTML内容
            
        Raises:
            Exception: 请求失败时抛出异常
        """
        # 随机选择User-Agent
        user_agent = random.choice(self.user_agents)
        headers = {'User-Agent': user_agent}
        
        # 添加随机延迟
        delay = random.uniform(self.min_delay, self.max_delay)
        logger.debug(f"等待 {delay:.2f} 秒后发起请求")
        await asyncio.sleep(delay)
        
        async with session.get(url, headers=headers) as response:
            if response.status != 200:
                raise Exception(f"HTTP {response.status}: {await response.text()}")
            
            content = await response.text()
            logger.debug(f"获取页面内容成功，长度: {len(content)}")
            return content
    
    def _parse_repositories(self, html_content: str) -> List[TrendingRepository]:
        """解析HTML内容，提取仓库信息
        
        Args:
            html_content: HTML页面内容
            
        Returns:
            List[TrendingRepository]: 解析出的仓库列表
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        repositories = []
        
        # 查找仓库列表容器
        repo_articles = soup.find_all('article', class_='Box-row')
        
        if not repo_articles:
            logger.warning("未找到仓库列表，页面结构可能已变化")
            return repositories
        
        for article in repo_articles:
            try:
                repo_data = self._parse_single_repository(article)
                if repo_data:
                    repositories.append(repo_data)
            except Exception as e:
                logger.warning(f"解析单个仓库失败: {str(e)}")
                continue
        
        logger.info(f"成功解析 {len(repositories)} 个仓库")
        return repositories
    
    def _parse_single_repository(self, article) -> Optional[TrendingRepository]:
        """解析单个仓库信息
        
        Args:
            article: BeautifulSoup元素
            
        Returns:
            Optional[TrendingRepository]: 仓库信息或None
        """
        try:
            # 获取仓库名称和URL
            title_element = article.find('h2', class_='h3 lh-condensed')
            if not title_element:
                return None
            
            link_element = title_element.find('a')
            if not link_element:
                return None
            
            repo_path = link_element.get('href', '').strip()
            if not repo_path:
                return None
            
            repo_url = urljoin(self.base_url, repo_path)
            repo_name = repo_path.strip('/')
            
            # 分离owner和repo_name
            parts = repo_name.split('/')
            if len(parts) != 2:
                return None
            
            owner, repo_short_name = parts
            
            # 获取描述
            description = None
            desc_element = article.find('p', class_='col-9')
            if desc_element:
                description = desc_element.get_text(strip=True)
            
            # 获取编程语言
            language = None
            language_color = None
            lang_element = article.find('span', itemprop='programmingLanguage')
            if lang_element:
                language = lang_element.get_text(strip=True)
                # 获取语言颜色
                color_element = lang_element.find_previous('span', class_='repo-language-color')
                if color_element:
                    style = color_element.get('style', '')
                    color_match = re.search(r'background-color:\s*([^;]+)', style)
                    if color_match:
                        language_color = color_match.group(1).strip()
            
            # 获取星标数和fork数
            stars, forks = self._parse_stats(article)
            
            # 获取今日星标数
            stars_today = self._parse_stars_today(article)
            
            # 获取头像URL
            avatar_url = self._parse_avatar_url(article)
            
            return TrendingRepository(
                name=repo_name,
                url=repo_url,
                description=description,
                stars=stars,
                forks=forks,
                language=language,
                language_color=language_color,
                stars_today=stars_today,
                period_stars=stars_today,  # 对于trending，period_stars等于stars_today
                owner=owner,
                repo_name=repo_short_name,
                avatar_url=avatar_url,
                crawled_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"解析仓库详情失败: {str(e)}")
            return None
    
    def _parse_stats(self, article) -> tuple[int, int]:
        """解析星标数和fork数
        
        Args:
            article: BeautifulSoup元素
            
        Returns:
            tuple[int, int]: (stars, forks)
        """
        stars = 0
        forks = 0
        
        # 查找统计信息
        stat_links = article.find_all('a', class_='Link--muted')
        
        for link in stat_links:
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            if '/stargazers' in href:
                stars = self._parse_number(text)
            elif '/forks' in href:
                forks = self._parse_number(text)
        
        return stars, forks
    
    def _parse_stars_today(self, article) -> int:
        """解析今日新增星标数
        
        Args:
            article: BeautifulSoup元素
            
        Returns:
            int: 今日新增星标数
        """
        # 查找今日星标信息
        star_element = article.find('span', class_='d-inline-block float-sm-right')
        if star_element:
            text = star_element.get_text(strip=True)
            # 提取数字，格式通常是 "123 stars today"
            match = re.search(r'(\d+(?:,\d+)*)\s+stars?\s+today', text)
            if match:
                return self._parse_number(match.group(1))
        
        return 0
    
    def _parse_avatar_url(self, article) -> Optional[str]:
        """解析头像URL
        
        Args:
            article: BeautifulSoup元素
            
        Returns:
            Optional[str]: 头像URL
        """
        img_element = article.find('img', class_='avatar')
        if img_element:
            src = img_element.get('src')
            if src:
                return urljoin(self.base_url, src)
        
        return None
    
    def _parse_number(self, text: str) -> int:
        """解析数字字符串
        
        Args:
            text: 包含数字的字符串，如 "1,234" 或 "1.2k"
            
        Returns:
            int: 解析出的数字
        """
        if not text:
            return 0
        
        # 移除逗号
        text = text.replace(',', '')
        
        # 处理k, m等单位
        text = text.lower()
        multiplier = 1
        
        if text.endswith('k'):
            multiplier = 1000
            text = text[:-1]
        elif text.endswith('m'):
            multiplier = 1000000
            text = text[:-1]
        
        try:
            number = float(text) * multiplier
            return int(number)
        except (ValueError, TypeError):
            return 0
    
    async def get_supported_languages(self) -> List[str]:
        """获取支持的编程语言列表
        
        Returns:
            List[str]: 支持的编程语言列表
        """
        # 常见的GitHub trending支持的编程语言
        return [
            'python', 'javascript', 'java', 'typescript', 'c++', 'c', 'c#',
            'go', 'rust', 'php', 'ruby', 'swift', 'kotlin', 'dart', 'scala',
            'r', 'matlab', 'shell', 'powershell', 'html', 'css', 'vue',
            'react', 'angular', 'node.js', 'express', 'django', 'flask',
            'spring', 'laravel', 'rails', 'asp.net'
        ]
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查
        
        Returns:
            Dict[str, Any]: 健康状态信息
        """
        try:
            async with aiohttp.ClientSession(**self.session_config) as session:
                async with session.get(self.base_url) as response:
                    if response.status == 200:
                        return {
                            'status': 'healthy',
                            'github_accessible': True,
                            'response_time': response.headers.get('X-Response-Time')
                        }
                    else:
                        return {
                            'status': 'unhealthy',
                            'github_accessible': False,
                            'error': f'HTTP {response.status}'
                        }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'github_accessible': False,
                'error': str(e)
            }