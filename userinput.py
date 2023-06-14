# Ref. https://proxyway.com/guides/how-to-scrape-instagram
# video: https://www.youtube.com/watch?v=SNyQu_FXkqs
# proxy provider: https://proxy2.webshare.io/proxy/list

from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from pprint import pprint
import json
from selenium_stealth import stealth
import csv

proxy = "http://username:password@proxy_server:port"
proxy = "server:port"
output = {}

def prepare_browser():
    chrome_options = webdriver.ChromeOptions()
    proxy = "server:port"
    chrome_options.add_argument(f'--proxy-server={proxy}')
    chrome_options.add_argument("start-maximized")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    driver = webdriver.Chrome('YOUR PATH OF CHROMEDRIVER/chromedriver.exe')
    driver.get("https://www.instagram.com/")
    stealth(driver,
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.53 Safari/537.36',
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=False,
            run_on_insecure_origins=False,
            )
    return driver

def parse_data(username, user_data):
    captions = []
    likes_count = 0
    comments_count = 0
    post_created_date = None
    post_created_time = None
    views_count = 0
    type_of_post = []
    latest_post_url = None
    likes_disabled = False
    views_disabled = False

    if len(user_data['edge_owner_to_timeline_media']['edges']) > 0:
        for i, node in enumerate(user_data['edge_owner_to_timeline_media']['edges']):
            if i == 0:  # This is the latest post
                latest_post_url = "https://instagram.com/p/" + node['node']['shortcode']

            if len(node['node']['edge_media_to_caption']['edges']) > 0:
                if node['node']['edge_media_to_caption']['edges'][0]['node']['text']:
                    captions.append(
                        node['node']['edge_media_to_caption']['edges'][0]['node']['text']
                    )
            likes_count += node['node']['edge_liked_by']['count']
            comments_count += node['node']['edge_media_to_comment']['count']

            # Extract post created date and time
            created_timestamp = node['node']['taken_at_timestamp']
            created_datetime = datetime.fromtimestamp(created_timestamp)
            post_created_date = created_datetime.date()
            post_created_time = created_datetime.time()

            # Extract views count (if available)
            views_count = node['node'].get('video_view_count', 0)

            # Check type of post
            if node['node']['is_video']:
                type_of_post = 'video'
            elif node['node'].get('display_url'):
                type_of_post = 'image'
            else:
                type_of_post = 'text'

            # Check if likes/views are disabled
            likes_disabled = 'edge_media_preview_like' not in node['node']
            views_disabled = 'edge_media_to_comment' not in node['node']

    user_output = {
        'UserName': username,
        'Name': user_data['full_name'],
        'Category': user_data['category_name'],
        'Followers': user_data['edge_followed_by']['count'],
        'Post Created Date': post_created_date,
        'Post Created Time': post_created_time,
        'Following': user_data['edge_follow']['count'],
        'Likes': likes_count,
        'Total Interactions': likes_count + comments_count,
        'Views': views_count,
        'Comments': comments_count,
        'Number of Post': user_data['edge_owner_to_timeline_media']['count'],
        'Posts': captions,
        'Type of Post': type_of_post,
        'Likes Disabled': likes_disabled,
        'Views Disabled': views_disabled,
        'Latest Post URL': latest_post_url,
        'Link': f"https://instagram.com/{username}",
    }

    return user_output

def scrape(username):
    url = f'https://instagram.com/{username}/?__a=1&__d=dis'
    chrome = prepare_browser()
    chrome.get(url)
    print(f"Attempting: {chrome.current_url}")
    if "login" in chrome.current_url:
        print("Failed/ redir to login")
        chrome.quit()
        return None
    else:
        print("Success")
        resp_body = chrome.find_element(By.TAG_NAME, "body").text
        data_json = json.loads(resp_body)
        user_data = data_json['graphql']['user']
        num_posts = user_data['edge_owner_to_timeline_media']['count']
        parsed_data = parse_data(username, user_data)
        chrome.quit()
        return parsed_data

def main():
    username = input('Please enter the username: ')
    # Open a CSV file in write mode
    with open(username + '.csv', 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['UserName', 'Name', 'Category', 'Followers', 'Post Created Date', 'Post Created Time', 'Following', 'Likes', 'Total Interactions', 'Views', 'Comments', 'Number of Post', 'Posts', 'Type of Post', 'Likes Disabled', 'Views Disabled', 'Latest Post URL', 'Link']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # Write the header row
        writer.writeheader()

        #for user_data in username:
        user_data = scrape(username)
        if user_data:
            writer.writerow(user_data)
            output[username] = user_data

if __name__ == '__main__':
    main()
    pprint(output)
