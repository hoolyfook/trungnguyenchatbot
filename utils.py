# utils.py
from bs4 import BeautifulSoup
import requests
import re

def get_href_from_main(url):
    if url and (url[-1] == '.' or url[-1] == ')'):
        url = url[:-1]
        
    # Gửi yêu cầu GET đến URL
    response = requests.get(url)
    
    # Tạo đối tượng BeautifulSoup để phân tích HTML
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Tìm thẻ <main>
    main_tag = soup.find('main')
    if not main_tag:
        return None
    
    # Tìm thẻ <a> trong thẻ <main>
    a_tag = main_tag.find('a', href=True)
    if a_tag and a_tag['href'].startswith('https://trungnguyenlegendcafe.net/wp-content'):
        return a_tag['href']
    else:
        return None


def extract_urls(text):
    # Biểu thức chính quy để tìm URL
    url_pattern = re.compile(r'https?://\S+')
    # Tìm tất cả các URL trong văn bản
    urls = url_pattern.findall(text)
    # Trả về URL đầu tiên nếu có, hoặc None nếu không tìm thấy
    return urls if urls else []