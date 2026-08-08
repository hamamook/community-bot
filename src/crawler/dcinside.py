import re
from playwright.sync_api import sync_playwright

def scrape_dcinside_post(url: str):
    # 💡 핵심 1: 복잡한 모바일 주소를 정규식(Regex)을 이용해 정확한 PC 주소로 분해 후 조립합니다.
    match = re.search(r'm\.dcinside\.com/([^/]+)/([^/]+)/(\d+)', url)
    if match:
        board_type = match.group(1) # 'board', 'mini', 'mgallery'
        gall_id = match.group(2)
        no = match.group(3)
        
        if board_type == 'mini':
            pc_url = f"https://gall.dcinside.com/mini/board/view/?id={gall_id}&no={no}"
        elif board_type == 'mgallery':
            pc_url = f"https://gall.dcinside.com/mgallery/board/view/?id={gall_id}&no={no}"
        else:
            pc_url = f"https://gall.dcinside.com/board/view/?id={gall_id}&no={no}"
    else:
        # 혹시 모를 예외 상황을 위한 기본 변환
        pc_url = url.replace("m.dcinside.com", "gall.dcinside.com")

    with sync_playwright() as p:
        # PC 버전이므로 화면을 띄워서(headless=False) 안정적으로 긁어옵니다.
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        try:
            page.goto(pc_url, timeout=30000)
            page.wait_for_timeout(2000)
            
            title = page.title()
            
            # 💡 핵심 2: PC 버전은 지연 로딩이나 숨김 처리가 없어 클래스 이름만으로 100% 긁어올 수 있습니다.
            try:
                content = page.locator(".write_div").inner_text(timeout=5000)
            except:
                content = "본문을 가져올 수 없거나 없는 글입니다."
                
            # PC 버전의 텍스트와 댓글은 `.usertxt` 안에 모두 담겨있습니다.
            comments = []
            comment_elements = page.locator(".usertxt")
            for i in range(comment_elements.count()):
                text = comment_elements.nth(i).inner_text().strip()
                # 빈 줄 방지
                if text:
                    comments.append(text)
                    
            result = {
                "title": title,
                "url": pc_url,
                "content": content.strip(),
                "comments": comments
            }
            
        except Exception as e:
            print(f"[{pc_url}] 크롤링 중 에러 발생: {e}")
            result = None
            
        finally:
            browser.close()
            
        return result