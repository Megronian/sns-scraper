#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
import time
import os

class SNSScraper:
    def __init__(self):
        # ブラウザのふりをするためのヘッダー
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.data = []
        
        # dataフォルダが存在しない場合は作成
        os.makedirs('data', exist_ok=True)
    
    def safe_request(self, url, max_retries=3):
        """安全にHTTPリクエストを送信"""
        for attempt in range(max_retries):
            try:
                print(f"🌐 アクセス中: {url}")
                time.sleep(2)  # 2秒待機（サーバーに優しく）
                response = requests.get(url, headers=self.headers, timeout=15)
                if response.status_code == 200:
                    return response
                else:
                    print(f"❌ HTTP {response.status_code}: {url}")
            except Exception as e:
                print(f"⚠️ エラー (試行 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(5)  # 失敗時は5秒待機
        return None
    
    def scrape_instagram_basic(self, username):
        """Instagram投稿の基本情報を取得"""
        try:
            url = f"https://www.instagram.com/{username}/"
            response = self.safe_request(url)
            
            if response:
                # 投稿のリンクパターンを検索
                post_pattern = r'/p/([A-Za-z0-9_-]+)/'
                matches = re.findall(post_pattern, response.text)
                
                # 重複を除去して最新5件取得
                unique_posts = list(dict.fromkeys(matches))[:5]
                print(f"📸 Instagram @{username}: {len(unique_posts)}件の投稿を発見")
                
                for post_code in unique_posts:
                    post_data = {
                        'company': 'Rocket now' if 'rocketnow' in username.lower() else 'Wolt',
                        'platform': 'Instagram',
                        'username': username,
                        'post_url': f"https://www.instagram.com/p/{post_code}/",
                        'post_id': post_code,
                        'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    self.data.append(post_data)
                    
        except Exception as e:
            print(f"❌ Instagram {username} エラー: {e}")
    
    def scrape_twitter_nitter(self, username):
        """Nitter経由でTwitter投稿を取得"""
        try:
            # Nitterのミラーサイトを試す
            nitter_instances = [
                f"https://nitter.net/{username}",
                f"https://nitter.it/{username}",
                f"https://nitter.privacydev.net/{username}"
            ]
            
            for nitter_url in nitter_instances:
                response = self.safe_request(nitter_url)
                
                if response:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    tweets = soup.find_all('div', class_='timeline-item')
                    
                    if tweets:
                        print(f"🐦 Twitter @{username}: {len(tweets[:5])}件のツイートを発見")
                        
                        for tweet in tweets[:5]:  # 最新5件
                            tweet_link = tweet.find('a', class_='tweet-link')
                            tweet_content = tweet.find('div', class_='tweet-content')
                            
                            if tweet_link and tweet_content:
                                # Nitterのリンクを本家Twitterのリンクに変換
                                nitter_link = tweet_link.get('href', '')
                                twitter_link = f"https://twitter.com{nitter_link}"
                                
                                post_data = {
                                    'company': 'Rocket now' if 'rocketnow' in username.lower() else 'Wolt',
                                    'platform': 'Twitter',
                                    'username': username,
                                    'post_url': twitter_link,
                                    'content_preview': tweet_content.get_text(strip=True)[:100] + '...',
                                    'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                }
                                self.data.append(post_data)
                        break  # 成功したらループを抜ける
                    
        except Exception as e:
            print(f"❌ Twitter {username} エラー: {e}")
    
    def load_existing_data(self):
        """既存のデータを読み込み（重複防止用）"""
        try:
            with open('data/posts.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return []
    
    def save_data(self):
        """データを保存（重複チェック付き）"""
        # 既存データを読み込み
        existing_data = self.load_existing_data()
        existing_urls = {item.get('post_url') for item in existing_data}
        
        # 新しいデータのみを抽出
        new_data = [item for item in self.data 
                   if item.get('post_url') not in existing_urls]
        
        # 全データをマージ
        all_data = existing_data + new_data
        
        # 日付でソート（新しい順）
        all_data.sort(key=lambda x: x.get('scraped_at', ''), reverse=True)
        
        # 保存
        with open('data/posts.json', 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n📊 結果:")
        print(f"   新規投稿: {len(new_data)}件")
        print(f"   総投稿数: {len(all_data)}件")
        
        return len(new_data)

def main():
    print("🚀 SNS投稿自動取得システム開始")
    print("=" * 50)
    
    scraper = SNSScraper()
    
    # 取得対象のアカウント
    accounts = [
        # Rocket now
        {'platform': 'instagram', 'username': 'rocketnow_official'},
        {'platform': 'twitter', 'username': 'Rocketnow_jp'},
        
        # Wolt
        {'platform': 'instagram', 'username': 'woltjapan'},
        {'platform': 'twitter', 'username': 'WoltJapan'}
    ]
    
    # 各アカウントから投稿を取得
    for account in accounts:
        print(f"\n📱 {account['platform'].title()} @{account['username']} を処理中...")
        
        if account['platform'] == 'instagram':
            scraper.scrape_instagram_basic(account['username'])
        elif account['platform'] == 'twitter':
            scraper.scrape_twitter_nitter(account['username'])
    
    # データ保存
    new_posts_count = scraper.save_data()
    
    print("\n" + "=" * 50)
    print("✅ 処理完了！")
    
    if new_posts_count > 0:
        print(f"🎉 {new_posts_count}件の新しい投稿を発見しました")
    else:
        print("📭 新しい投稿は見つかりませんでした")

if __name__ == "__main__":
    main()
