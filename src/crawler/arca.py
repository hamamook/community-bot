from playwright.sync_api import sync_playwright

def scrape_arca_post(url: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        try:
            page.goto(url, timeout=30000)
            page.wait_for_timeout(2000)
            
            title = page.title()
            
            # 아카라이브 본문은 보통 .fr-view 라는 에디터 클래스 안에 담겨있습니다.
            try:
                content = page.locator(".fr-view").inner_text(timeout=5000)
            except:
                content = "본문을 가져올 수 없거나 없는 글입니다."
                
            # 아카라이브 댓글 텍스트는 .comment-item .text 형태로 묶여있습니다.
            comments = []
            comment_elements = page.locator(".comment-item .text")
            for i in range(comment_elements.count()):
                text = comment_elements.nth(i).inner_text().strip()
                if text:
                    comments.append(text)
                    
            result = {
                "title": title,
                "url": url,
                "content": content.strip(),
                "comments": comments
            }
            
        except Exception as e:
            print(f"[{url}] 아카라이브 크롤링 중 에러 발생: {e}")
            result = None
            
        finally:
            browser.close()
            
        return result