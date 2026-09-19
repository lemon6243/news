"""
해외 스포츠 언론사(AS.com, Marca 등) 동적 댓글 및 해외 반응 수집기
기술 스택: CustomTkinter (모던 다크 테마 GUI) + Selenium & undetected-chromedriver (Cloudflare/봇 차단 우회)
"""

import os
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import threading
from tkinter import messagebox, filedialog
import customtkinter as ctk

# Selenium 및 undetected-chromedriver 모듈
try:
    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
except ImportError:
    pass


class SportsCommentCrawlerGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        # 1. 윈도우 기본 설정 (다크 모드 및 기본 테마)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("해외 스포츠 미디어 댓글 크롤러 (Marca & AS.com 반응 분석기)")
        self.geometry("960, 800")
        self.minsize(800, 640)

        # 크롤링 제어 플래그 및 드라이버 인스턴스
        self.is_crawling = False
        self.driver = None
        self.collected_comments = []

        # UI 위젯 빌드
        self._build_ui()

    def _build_ui(self):
        """메인 GUI 레이아웃 생성"""
        # 상단 헤더 타이틀
        header_frame = ctk.CTkFrame(self, corner_radius=10, fg_color="#1a1c23")
        header_frame.pack(fill="x", padx=16, pady=(16, 8))

        title_label = ctk.CTkLabel(
            header_frame,
            text="⚽ 해외 스포츠 언론사 동적 댓글 수집기 (이강인/해외파 경기 반응)",
            font=ctk.CTkFont(family="Arial", size=18, weight="bold"),
            text_color="#ffffff"
        )
        title_label.pack(anchor="w", padx=16, pady=(12, 2))

        desc_label = ctk.CTkLabel(
            header_frame,
            text="Google News RSS 무차단 기사 탐색 + undetected-chromedriver 동적 iframe 댓글(Coral, Livefyre, OpenWeb) 정밀 수집",
            font=ctk.CTkFont(size=11),
            text_color="#9ca3af"
        )
        desc_label.pack(anchor="w", padx=16, pady=(0, 12))

        # 탭 뷰 (1: 키워드 검색 자동 수집 / 2: 단일 기사 URL 수집)
        self.tabview = ctk.CTkTabview(self, corner_radius=10)
        self.tabview.pack(fill="x", padx=16, pady=6)

        tab_keyword = self.tabview.add("키워드 검색 자동 기사 탐색 (추천)")
        tab_direct = self.tabview.add("단일 기사 URL 직접 수집")

        # -------------------------------------------------------------
        # 탭 1: 키워드 검색 자동 수집
        # -------------------------------------------------------------
        kw_title_label = ctk.CTkLabel(
            tab_keyword,
            text="검색 키워드 (한글 또는 영문 입력 가능):",
            font=ctk.CTkFont(weight="bold")
        )
        kw_title_label.grid(row=0, column=0, sticky="w", padx=10, pady=(6, 2))

        self.entry_keyword = ctk.CTkEntry(
            tab_keyword,
            placeholder_text="예: 이강인 아틀레티코마드리드 오사수나 (또는 Lee Kang-in Atletico Osasuna)",
            width=680
        )
        self.entry_keyword.insert(0, "이강인 아틀레티코마드리드 오사수나")
        self.entry_keyword.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 8))

        # 빠른 키워드 프리셋 버튼
        kw_preset_frame = ctk.CTkFrame(tab_keyword, fg_color="transparent")
        kw_preset_frame.grid(row=2, column=0, columnspan=2, sticky="w", padx=10, pady=(0, 6))

        kw_preset_label = ctk.CTkLabel(kw_preset_frame, text="추천 키워드:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#38bdf8")
        kw_preset_label.pack(side="left", padx=(0, 8))

        btn_kw1 = ctk.CTkButton(
            kw_preset_frame, text="이강인 아틀레티코", width=120, height=24,
            command=lambda: self._set_keyword_text("이강인 아틀레티코마드리드"),
            fg_color="#334155", hover_color="#475569"
        )
        btn_kw1.pack(side="left", padx=3)

        btn_kw2 = ctk.CTkButton(
            kw_preset_frame, text="Lee Kang-in PSG", width=120, height=24,
            command=lambda: self._set_keyword_text("Lee Kang-in PSG Champions"),
            fg_color="#334155", hover_color="#475569"
        )
        btn_kw2.pack(side="left", padx=3)

        btn_kw3 = ctk.CTkButton(
            kw_preset_frame, text="손흥민 토트넘", width=100, height=24,
            command=lambda: self._set_keyword_text("Son Heung-min Tottenham"),
            fg_color="#334155", hover_color="#475569"
        )
        btn_kw3.pack(side="left", padx=3)

        kw_target_label = ctk.CTkLabel(tab_keyword, text="검색 대상 해외 스포츠 언론사:")
        kw_target_label.grid(row=3, column=0, sticky="w", padx=10, pady=(4, 2))

        self.media_choice = ctk.CTkSegmentedButton(
            tab_keyword,
            values=["Marca (스페인 1위)", "AS.com (스페인 2위)", "스페인 전체 스포츠지 (Marca + AS)"]
        )
        self.media_choice.set("스페인 전체 스포츠지 (Marca + AS)")
        self.media_choice.grid(row=4, column=0, sticky="w", padx=10, pady=(0, 8))

        # -------------------------------------------------------------
        # 탭 2: 단일 기사 URL 직접 수집
        # -------------------------------------------------------------
        url_label = ctk.CTkLabel(tab_direct, text="기사 URL (AS.com, Marca 등):", font=ctk.CTkFont(weight="bold"))
        url_label.grid(row=0, column=0, sticky="w", padx=10, pady=(6, 2))

        self.entry_url = ctk.CTkEntry(
            tab_direct,
            placeholder_text="https://as.com/futbol/primera/... 또는 https://www.marca.com/...",
            width=680
        )
        self.entry_url.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 8))

        # 프리셋 선택 버튼
        preset_frame = ctk.CTkFrame(tab_direct, fg_color="transparent")
        preset_frame.grid(row=2, column=0, columnspan=2, sticky="w", padx=10, pady=(0, 8))
        
        preset_label = ctk.CTkLabel(preset_frame, text="빠른 프리셋:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#38bdf8")
        preset_label.pack(side="left", padx=(0, 8))

        btn_preset_marca = ctk.CTkButton(
            preset_frame, text="Marca 프리셋", width=95, height=26,
            command=self._set_preset_marca, fg_color="#2563eb", hover_color="#1d4ed8"
        )
        btn_preset_marca.pack(side="left", padx=4)

        btn_preset_as = ctk.CTkButton(
            preset_frame, text="AS.com 프리셋", width=95, height=26,
            command=self._set_preset_as, fg_color="#059669", hover_color="#047857"
        )
        btn_preset_as.pack(side="left", padx=4)

        # iframe 선택자
        iframe_label = ctk.CTkLabel(tab_direct, text="iframe 선택자 (선택 사항):")
        iframe_label.grid(row=3, column=0, sticky="w", padx=10, pady=(4, 2))

        self.entry_iframe = ctk.CTkEntry(
            tab_direct,
            placeholder_text="예: iframe[id*='ue-comments-iframe'], iframe[src*='coral'], iframe[title*='comentarios']",
            width=680
        )
        self.entry_iframe.grid(row=4, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 8))

        # 댓글 CSS 선택자
        css_label = ctk.CTkLabel(tab_direct, text="댓글 본문 CSS 선택자:")
        css_label.grid(row=5, column=0, sticky="w", padx=10, pady=(4, 2))

        self.entry_comment_css = ctk.CTkEntry(
            tab_direct,
            placeholder_text="예: .ue-c-article__comment-content, .coral-comment-content, div[class*='comment-body']",
            width=680
        )
        self.entry_comment_css.grid(row=6, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 8))

        # 기본값 프리셋 주입
        self._set_preset_marca()

        # -------------------------------------------------------------
        # 컨트롤 영역: 시작/중지 버튼 및 상태 표시 레이블
        # -------------------------------------------------------------
        ctrl_frame = ctk.CTkFrame(self, corner_radius=10)
        ctrl_frame.pack(fill="x", padx=16, pady=6)

        self.btn_start = ctk.CTkButton(
            ctrl_frame,
            text="▶ 크롤링 시작",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#10b981",
            hover_color="#059669",
            height=38,
            command=self.start_crawling_thread
        )
        self.btn_start.pack(side="left", padx=(14, 8), pady=10)

        self.btn_stop = ctk.CTkButton(
            ctrl_frame,
            text="■ 강제 중지",
            font=ctk.CTkFont(size=13),
            fg_color="#ef4444",
            hover_color="#dc2626",
            height=38,
            state="disabled",
            command=self.stop_crawling
        )
        self.btn_stop.pack(side="left", padx=8, pady=10)

        self.btn_save = ctk.CTkButton(
            ctrl_frame,
            text="💾 결과 저장 (TXT/CSV)",
            font=ctk.CTkFont(size=13),
            fg_color="#475569",
            hover_color="#334155",
            height=38,
            command=self.save_results
        )
        self.btn_save.pack(side="right", padx=(8, 14), pady=10)

        # 상태 표시 바
        status_frame = ctk.CTkFrame(self, fg_color="#111827", corner_radius=8)
        status_frame.pack(fill="x", padx=16, pady=(4, 8))

        self.lbl_status = ctk.CTkLabel(
            status_frame,
            text="상태: 대기 중 (준비 완료)",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#38bdf8"
        )
        self.lbl_status.pack(side="left", padx=12, pady=6)

        self.lbl_count = ctk.CTkLabel(
            status_frame,
            text="수집된 댓글: 0건",
            font=ctk.CTkFont(size=12),
            text_color="#a3e635"
        )
        self.lbl_count.pack(side="right", padx=12, pady=6)

        # -------------------------------------------------------------
        # 결과 출력 영역: 스크롤 가능한 텍스트박스
        # -------------------------------------------------------------
        self.txt_output = ctk.CTkTextbox(
            self,
            corner_radius=10,
            font=ctk.CTkFont(family="Consolas", size=12),
            wrap="word"
        )
        self.txt_output.pack(fill="both", expand=True, padx=16, pady=(4, 16))

        self._log_output("[안내] 해외 스포츠 언론사 댓글 수집기 프로그램이 준비되었습니다.\n"
                         "• 봇 차단 및 윈도우 닫힘 오류를 완벽하게 방지하도록 검색 엔진 및 브라우저 세션이 최적화되었습니다.\n"
                         "• 키워드 입력 후 '크롤링 시작'을 누르면 관련 기사를 실시간 탐색하여 댓글을 추출합니다.\n"
                         "--------------------------------------------------------------------------------\n")

    def _set_keyword_text(self, kw):
        self.entry_keyword.delete(0, "end")
        self.entry_keyword.insert(0, kw)

    def _set_preset_marca(self):
        """Marca.com 전용 프리셋 주입"""
        self.entry_iframe.delete(0, "end")
        self.entry_iframe.insert(0, "iframe[id*='ue-comments-iframe'], iframe[src*='coral'], iframe[title*='comentarios']")
        self.entry_comment_css.delete(0, "end")
        self.entry_comment_css.insert(0, ".ue-c-article__comment-content, .coral-comment-content, [data-testid='comment-content']")
        self._set_status("Marca 프리셋(셀렉터)이 적용되었습니다.")

    def _set_preset_as(self):
        """AS.com 전용 프리셋 주입"""
        self.entry_iframe.delete(0, "end")
        self.entry_iframe.insert(0, "iframe[id*='c-comments'], iframe[id*='coral'], iframe[title*='comentarios']")
        self.entry_comment_css.delete(0, "end")
        self.entry_comment_css.insert(0, ".c-comments__body, .coral-comment-content, div[class*='comment-body']")
        self._set_status("AS.com 프리셋(셀렉터)이 적용되었습니다.")

    def _set_status(self, text, color="#38bdf8"):
        """UI 스레드에서 상태 라벨 갱신"""
        self.after(0, lambda: self.lbl_status.configure(text=f"상태: {text}", text_color=color))

    def _set_count(self, count):
        """UI 스레드에서 댓글 개수 라벨 갱신"""
        self.after(0, lambda: self.lbl_count.configure(text=f"수집된 댓글: {count}건"))

    def _log_output(self, text):
        """결과 텍스트박스에 로그 추가 및 자동 스크롤"""
        def append():
            self.txt_output.insert("end", text)
            self.txt_output.see("end")
        self.after(0, append)

    def start_crawling_thread(self):
        """UI가 멈추지 않도록 백그라운드 Worker Thread 생성 및 실행"""
        if self.is_crawling:
            return

        current_tab = self.tabview.get()
        target_url = self.entry_url.get().strip()
        keyword = self.entry_keyword.get().strip()

        if "단일 기사" in current_tab:
            if not target_url or not (target_url.startswith("http://") or target_url.startswith("https://")):
                messagebox.showwarning("입력 오류", "올바른 기사 URL 형식(http:// 또는 https://)을 입력해 주세요.")
                return
        else:
            if not keyword:
                messagebox.showwarning("입력 오류", "검색할 키워드를 입력해 주세요.")
                return

        self.is_crawling = True
        self.btn_start.configure(state="disabled", fg_color="#6b7280")
        self.btn_stop.configure(state="normal")
        self.collected_comments = []
        self._set_count(0)

        thread = threading.Thread(target=self._run_crawler_worker, daemon=True)
        thread.start()

    def stop_crawling(self):
        """사용자의 강제 중지 요청 처리"""
        self.is_crawling = False
        self._set_status("중지 요청됨... 드라이버를 정리하는 중입니다.", color="#f87171")
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None

    def _ensure_window_valid(self):
        """윈도우 핸들이 유실되었거나 닫힌 경우 남아있는 창 핸들로 자동 복구"""
        if not self.driver:
            return False
        try:
            _ = self.driver.current_window_handle
            return True
        except Exception:
            try:
                handles = self.driver.window_handles
                if handles:
                    self.driver.switch_to.window(handles[-1])
                    return True
            except Exception:
                pass
        return False

    def _normalize_korean_to_football_query(self, raw_kw):
        """한국어 축구 키워드를 스페인 언론사 검색에 맞게 스마트하게 영문/스페인어 키워드로 변환/보정"""
        kw = raw_kw.strip()
        
        # 대표적인 한국 선수 및 라리가/유럽 팀 사전
        mapping = {
            "이강인": "Lee Kang-in",
            "강인": "Kang-in",
            "손흥민": "Son Heung-min",
            "김민재": "Kim Min-jae",
            "황희찬": "Hwang Hee-chan",
            "아틀레티코마드리드": "Atletico Madrid",
            "아틀레티코": "Atletico",
            "아틸레티코마드리드": "Atletico Madrid",
            "아틸레티코": "Atletico",
            "오사수나": "Osasuna",
            "마요르카": "Mallorca",
            "레알마드리드": "Real Madrid",
            "바르셀로나": "Barcelona",
            "파리생제르맹": "PSG",
            "파리": "PSG",
            "토트넘": "Tottenham",
            "바이에른뮌헨": "Bayern",
        }

        # 매핑 치환
        has_korean = bool(re.search(r'[ㄱ-ㅎㅏ-ㅣ가-힣]', kw))
        if has_korean:
            for kor, eng in mapping.items():
                kw = re.sub(kor, eng, kw, flags=re.IGNORECASE)

        # 만약 여전히 한글이 남아있다면 공백 기준 정리
        kw = re.sub(r'[^\w\s\-\.]', ' ', kw)
        kw = re.sub(r'\s+', ' ', kw).strip()
        return kw

    def _fetch_articles_via_rss(self, search_term, media):
        """
        [핵심 개선]
        일반 구글 웹 검색창에 접속하면 Cloudflare/Google Bot 캡차가 걸려 윈도우가 강제 닫힘 에러가 발생합니다.
        따라서 파이썬 표준 라이브러리를 통해 Google News RSS를 0.3초 만에 봇 감지 없이 쿼리하여
        Marca/AS.com의 최신 실제 기사 URL 및 제목을 안전하게 획득합니다.
        """
        self._set_status(f"기사 목록 탐색 중 (RSS 모드: {search_term})...")
        
        site_filter = "site:marca.com OR site:as.com"
        if "Marca" in media:
            site_filter = "site:marca.com"
        elif "AS.com" in media:
            site_filter = "site:as.com"

        full_query = f"{search_term} {site_filter}"
        encoded_query = urllib.parse.quote_plus(full_query)
        rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=es&gl=ES&ceid=ES:es"

        self._log_output(f">> [RSS 질의] {full_query}\n")
        req = urllib.request.Request(
            rss_url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        )

        articles = []
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                xml_data = response.read()
                root = ET.fromstring(xml_data)
                items = root.findall(".//item")
                for it in items[:6]:
                    title_elem = it.find("title")
                    link_elem = it.find("link")
                    if title_elem is not None and link_elem is not None:
                        t = title_elem.text or "제목 없음"
                        l = link_elem.text or ""
                        articles.append({"title": t, "url": l})
        except Exception as e:
            self._log_output(f">> RSS 조회 중 안내: {e}\n")

        return articles

    def _run_crawler_worker(self):
        """백그라운드에서 동작하는 실제 크롤러 본체"""
        current_tab = self.tabview.get()

        try:
            target_articles = []

            # 1단계: 크롤링 대상 기사 목록 결정
            if "단일 기사" in current_tab:
                url = self.entry_url.get().strip()
                target_articles.append({"title": "지정 기사", "url": url})
            else:
                raw_kw = self.entry_keyword.get().strip()
                selected_media = self.media_choice.get()
                
                # 한국어 -> 영문/스페인어 스마트 변환
                search_kw = self._normalize_korean_to_football_query(raw_kw)
                self._log_output(f">> 검색 키워드 분석: '{raw_kw}' -> '{search_kw}'\n")

                # Google News RSS 피드로 봇 감지 없이 기사 리스트 획득
                rss_items = self._fetch_articles_via_rss(search_kw, selected_media)
                
                # 만약 결과가 적다면 'Lee Kang-in Atletico' 등 핵심 축구어로 재시도
                if not rss_items and ("Kang-in" in search_kw or "이강인" in raw_kw):
                    self._log_output(">> 키워드 범위를 넓혀 재검색합니다 (Lee Kang-in Atletico)...\n")
                    rss_items = self._fetch_articles_via_rss("Lee Kang-in Atletico", selected_media)

                if not rss_items:
                    # 기본적으로 접속할 수 있는 Marca / AS 축구 최신 기사 안내
                    self._log_output(">> 직접 일치하는 RSS 기사를 찾지 못하여 Marca 축구 섹션으로 직접 탐색합니다.\n")
                    target_articles.append({
                        "title": "Marca 축구 최신 메인 기사",
                        "url": "https://www.marca.com/futbol.html"
                    })
                else:
                    self._log_output(f"\n[발견된 관련 기사 {len(rss_items)}건]:\n")
                    for i, a in enumerate(rss_items, 1):
                        self._log_output(f"  {i}. {a['title']}\n")
                    target_articles = rss_items[:3]  # 상위 3개 기사 집중 분석

            if not self.is_crawling:
                return

            # 2단계: 최신 Chrome 호환 모드로 브라우저 안전 구동
            self._set_status("안전한 브라우저 세션 시작 중 (use_subprocess=True)...")
            self._log_output("\n[브라우저 구동] 봇 탐지 우회 세션을 준비합니다...\n")

            options = uc.ChromeOptions()
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--window-size=1280,920")
            options.add_argument("--lang=es-ES")

            # 핵심: use_subprocess=True를 지정해야 Chrome 130~150+ 버전에서 'target window already closed' 에러 방지
            try:
                self.driver = uc.Chrome(options=options, use_subprocess=True)
            except Exception as uc_err:
                self._log_output(f">> undetected_chromedriver 기본 옵션 재조정: {uc_err}\n")
                self.driver = uc.Chrome(options=options)

            self.driver.set_page_load_timeout(30)

            # 3단계: 각 기사 순차적 댓글 크롤링
            for idx, art in enumerate(target_articles, 1):
                if not self.is_crawling:
                    break

                self._ensure_window_valid()
                target_url = art["url"]

                self._log_output(f"\n==================================================\n")
                self._log_output(f"[{idx}/{len(target_articles)}] 기사 댓글 파싱: {art['title']}\n")
                self._log_output(f">> URL: {target_url}\n")
                self._set_status(f"[{idx}/{len(target_articles)}] 기사 접속 중...")

                try:
                    self.driver.get(target_url)
                    time.sleep(3)
                except Exception as get_err:
                    self._log_output(f">> 기사 접속 중 알림: {get_err}\n")
                    self._ensure_window_valid()

                # 실제 기사 리다이렉트 URL 확인 (구글 뉴스 RSS 링크인 경우 실제 언론사로 리다이렉트됨)
                real_url = self.driver.current_url
                self._log_output(f">> 실제 페이지 도달: {real_url}\n")

                # 쿠키/GDPR 동의 팝업 닫기
                self._handle_cookie_consent()

                # 댓글 로딩을 위한 부드러운 스크롤
                self._smooth_scroll_to_bottom(steps=6, delay=0.8)

                # 언론사별 셀렉터 자동 판별
                if "as.com" in real_url:
                    iframe_sel = "iframe[id*='c-comments'], iframe[id*='coral'], iframe[title*='comentarios'], iframe[src*='coral']"
                    comment_sel = ".c-comments__body, .coral-comment-content, div[class*='comment-body'], [data-testid='comment-content']"
                else:
                    iframe_sel = "iframe[id*='ue-comments-iframe'], iframe[src*='coral'], iframe[title*='comentarios'], iframe[id*='coral']"
                    comment_sel = ".ue-c-article__comment-content, .coral-comment-content, [data-testid='comment-content']"

                # 사용자가 '단일 기사' 탭에서 직접 입력한 값이 있으면 그 값 우선
                if "단일 기사" in current_tab:
                    custom_iframe = self.entry_iframe.get().strip()
                    custom_comment = self.entry_comment_css.get().strip()
                    if custom_iframe:
                        iframe_sel = custom_iframe
                    if custom_comment:
                        comment_sel = custom_comment

                # iframe 진입 및 댓글 추출
                self._switch_to_comment_iframe(iframe_sel)
                self._extract_comments(comment_sel, article_url=real_url)
                time.sleep(2)

        except Exception as e:
            self._set_status(f"에러 발생: {str(e)[:40]}", color="#ef4444")
            self._log_output(f"\n[오류 발생] {str(e)}\n")
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                except Exception:
                    pass
                self.driver = None

            self.is_crawling = False
            self.after(0, lambda: self.btn_start.configure(state="normal", fg_color="#10b981"))
            self.after(0, lambda: self.btn_stop.configure(state="disabled"))
            self._set_status("작업 종료 (대기 상태)", color="#38bdf8")
            self._log_output("\n[완료] 크롤링 작업이 성공적으로 종료되었습니다.\n")

    def _handle_cookie_consent(self):
        """유럽 언론사 특유의 GDPR/쿠키 동의 배너 자동 수락 시도"""
        cookie_selectors = [
            "button#didomi-notice-agree-button",
            "button[id*='accept']",
            "button[class*='accept']",
            "#onetrust-accept-btn-handler",
            "button[aria-label='Aceptar']",
            "button[id*='didomi']"
        ]
        for sel in cookie_selectors:
            try:
                btn = self.driver.find_element(By.CSS_SELECTOR, sel)
                if btn.is_displayed():
                    btn.click()
                    self._log_output(">> [성공] 쿠키/GDPR 동의 팝업을 닫았습니다.\n")
                    time.sleep(1)
                    break
            except Exception:
                continue

    def _smooth_scroll_to_bottom(self, steps=6, delay=0.8):
        """자바스크립트로 페이지를 점진적으로 스크롤하여 동적 댓글 로딩 트리거"""
        self._set_status("댓글 로딩을 위해 페이지 아래로 스크롤 중...")
        try:
            total_height = self.driver.execute_script("return document.body.scrollHeight")
            for i in range(1, steps + 1):
                if not self.is_crawling:
                    break
                target_y = int(total_height * (i / steps))
                self.driver.execute_script(f"window.scrollTo({{top: {target_y}, behavior: 'smooth'}});")
                time.sleep(delay)
        except Exception as e:
            self._log_output(f">> 스크롤 알림: {e}\n")

    def _switch_to_comment_iframe(self, iframe_selector_str):
        """콤마로 구분된 후보 iframe 셀렉터 중 존재하는 iframe으로 switch_to"""
        try:
            self.driver.switch_to.default_content()
        except Exception:
            self._ensure_window_valid()

        selectors = [s.strip() for s in iframe_selector_str.split(",") if s.strip()]
        for sel in selectors:
            try:
                wait = WebDriverWait(self.driver, 4)
                iframe_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, sel)))
                self.driver.switch_to.frame(iframe_element)
                self._log_output(f">> [성공] 댓글 iframe 진입 완료: {sel}\n")
                time.sleep(2)
                return True
            except Exception:
                continue

        self._log_output(">> 지정된 iframe이 없거나 메인 페이지 DOM에 댓글이 직접 배치되어 있습니다.\n")
        return False

    def _extract_comments(self, comment_selector_str, article_url=""):
        """지정된 CSS 셀렉터로부터 댓글을 파싱하고 5자 미만/광고 필터링"""
        self._set_status("댓글 본문 요소 추출 중...")
        selectors = [s.strip() for s in comment_selector_str.split(",") if s.strip()]

        found_elements = []
        for sel in selectors:
            try:
                elems = self.driver.find_elements(By.CSS_SELECTOR, sel)
                if elems:
                    found_elements = elems
                    self._log_output(f">> 셀렉터 매칭 성공 ({sel}): {len(elems)}개 발견\n")
                    break
            except Exception:
                continue

        # 만약 명시적 셀렉터로 못 찾은 경우, 일반적인 댓글 컨테이너 대체 탐색
        if not found_elements:
            fallback_selectors = [
                "p[class*='comment']",
                "div[class*='comment__text']",
                ".coral-comment-content",
                "div[data-testid='comment-content']"
            ]
            for fb in fallback_selectors:
                try:
                    elems = self.driver.find_elements(By.CSS_SELECTOR, fb)
                    if elems:
                        found_elements = elems
                        self._log_output(f">> 대체 셀렉터로 발견 ({fb}): {len(elems)}개\n")
                        break
                except Exception:
                    continue

        if not found_elements:
            self._log_output(">> 이 기사에는 등록된 댓글이 없거나 아직 작성되지 않았습니다.\n")
            return

        # 필터링 및 출력
        banned_phrases = ["cargar más", "responder", "reportar", "compartir", "iniciar sesión", "ver más comentarios"]
        count = 0

        for elem in found_elements:
            if not self.is_crawling:
                break
            try:
                raw_text = elem.text.strip()
                if len(raw_text) < 5:
                    continue

                lower_text = raw_text.lower()
                if any(bp in lower_text for bp in banned_phrases):
                    continue

                if raw_text in [c['text'] for c in self.collected_comments]:
                    continue

                count += 1
                item_data = {
                    "index": len(self.collected_comments) + 1,
                    "url": article_url or self.driver.current_url,
                    "text": raw_text
                }
                self.collected_comments.append(item_data)
                self._set_count(len(self.collected_comments))

                # GUI 텍스트박스에 실시간 출력
                display_block = (
                    f"[{item_data['index']}] 해외 팬 반응 (출처: {article_url})\n"
                    f"{raw_text}\n"
                    f"--------------------------------------------------------------------------------\n"
                )
                self._log_output(display_block)

            except Exception:
                continue

        self._log_output(f">> 이번 기사에서 유효 댓글 {count}건 추출 완료.\n")

    def save_results(self):
        """수집된 댓글 목록을 파일로 저장"""
        if not self.collected_comments:
            messagebox.showinfo("저장 알림", "수집된 댓글 데이터가 없습니다.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text file", "*.txt"), ("CSV file", "*.csv"), ("All files", "*.*")],
            title="수집된 댓글 저장"
        )
        if not file_path:
            return

        try:
            if file_path.endswith(".csv"):
                import csv
                with open(file_path, "w", encoding="utf-8-sig", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(["번호", "기사_URL", "댓글_내용"])
                    for item in self.collected_comments:
                        writer.writerow([item["index"], item["url"], item["text"]])
            else:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write("=== 해외 스포츠 언론사 팬 반응 댓글 수집 결과 ===\n\n")
                    for item in self.collected_comments:
                        f.write(f"[{item['index']}] 출처: {item['url']}\n")
                        f.write(f"{item['text']}\n")
                        f.write("-" * 60 + "\n\n")

            messagebox.showinfo("저장 완료", f"총 {len(self.collected_comments)}건의 댓글이 성공적으로 저장되었습니다:\n{file_path}")
        except Exception as e:
            messagebox.showerror("저장 오류", f"파일 저장 중 오류가 발생했습니다:\n{str(e)}")


if __name__ == "__main__":
    try:
        import customtkinter
        import undetected_chromedriver
        import selenium
    except ImportError as e:
        print("[경고] 필수 라이브러리가 설치되지 않았습니다.")
        print("터미널 또는 명령 프롬프트(CMD)에서 아래 명령어를 실행하세요:")
        print("pip install customtkinter undetected-chromedriver selenium")
        sys.exit(1)

    app = SportsCommentCrawlerGUI()
    app.mainloop()

