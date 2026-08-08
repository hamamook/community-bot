def filter_dcinside_links(links: list) -> list:
    """주어진 링크 리스트에서 dcinside.com이 포함된 링크만 반환합니다."""
    dc_links = []
    
    for link in links:
        if "dcinside.com" in link:
            dc_links.append(link)
            
    return dc_links
def filter_dcinside_links(links: list) -> list:
    """주어진 링크 리스트에서 dcinside.com이 포함된 링크만 반환합니다."""
    dc_links = []
    for link in links:
        if "dcinside.com" in link:
            dc_links.append(link)
    return dc_links

def filter_arca_links(links: list) -> list:
    """주어진 링크 리스트에서 아카라이브 게시글 링크만 반환합니다."""
    arca_links = []
    for link in links:
        # 아카라이브 게시글 주소 형식(arca.live/b/...) 필터링
        if "arca.live/b/" in link:
            arca_links.append(link)
    return arca_links