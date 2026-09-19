"""
해외 스포츠 언론사(AS.com, Marca 등) 동적 댓글 및 해외 반응 수집기
기술 스택: CustomTkinter (모던 다크 테마 GUI) + Selenium & undetected-chromedriver (Cloudflare/봇 차단 우회)
"""

import os
import re
import sys
import time
import urllib.parse
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
    pass  # 실행 시 모듈 누락 안내 메시지 처리


class SportsCommentCrawlerGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        # 1. 윈도우 기본 설정 (다크 모드 및 기본 테마)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("해외 스포츠 미디어 댓글 크롤러 (Marca & AS.com 반응 분석기)")
        self.geometry("960, 780")
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
            text="⚽ 해외 스포츠 언론사 동적 댓글 수집기",
            font=ctk.CTkFont(family="Arial", size=20, weight="bold"),
            text_color="#ffffff"
        )
        title_label.pack(anchor="w", padx=16, pady=(12, 2))

        desc_label = ctk.CTkLabel(
            header_frame,
            text="undetected-chromedriver로 Cloudflare 우회 | iframe 댓글(Coral, Livefyre, OpenWeb) 정밀 파싱",
            font=ctk.CTkFont(size=12),
            text_color="#9ca3af"
        )
        desc_label.pack(anchor="w", padx=16, pady=(0, 12))

        # 탭 뷰 (1: 단일 기사 URL 수집 / 2: 키워드 검색 자동 수집)
        self.tabview = ctk.CTkTabview(self, corner_radius=10)
        self.tabview.pack(fill="x", padx=16, pady=6)

        tab_direct = self.tabview.add("단일 기사 URL 직접 수집")
        tab_keyword = self.tabview.add("키워드 검색 자동 기사 탐색")

        # -------------------------------------------------------------
        # 탭 1: 단일 기사 URL 직접 수집
        # -------------------------------------------------------------
        url_label = ctk.CTkLabel(tab_direct, text="기사 URL (AS.com, Marca 등):", font=ctk.CTkFont(weight="bold"))
        url_label.grid(row=0, column=0, sticky="w", padx=10, pady=(6, 2))

        self.entry_url = ctk.CTkEntry(
            tab_direct,
            placeholder_text="https://as.com/futbol/primera/... 또는 https://www.marca.com/...",
            width=680
        )
        self.entry_url.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 8))

        # 프리셋 선택 버튼 (AS, Marca 등 기본 셀렉터 자동완성)
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
        iframe_label = ctk.CTkLabel(tab_direct, text="iframe 선택자 (선택 사항, 없으면 비워둠):")
        iframe_label.grid(row=3, column=0, sticky="w", padx=10, pady=(4, 2))

        self.entry_iframe = ctk.CTkEntry(
            tab_direct,
            placeholder_text="예: iframe[id*='comment'], iframe[id*='coral'], iframe[title*='comment']",
            width=680
        )
        self.entry_iframe.grid(row=4, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 8))

        # 댓글 CSS 선택자
        css_label = ctk.CTkLabel(tab_direct, text="댓글 본문 CSS 선택자:")
        css_label.grid(row=5, column=0, sticky="w", padx=10, pady=(4, 2))

        self.entry_comment_css = ctk.CTkEntry(
            tab_direct,
            placeholder_text="예: .ue-c-article__comment-content, div[data-testid='comment-body'], .comment-text",
            width=680
        )
        self.entry_comment_css.grid(row=6, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 8))

        # 기본값으로 Marca / AS 겸용 권장 셀렉터 사전 입력
        self._set_preset_marca()

        # -------------------------------------------------------------
        # 탭 2: 키워드 검색 자동 수집
        # -------------------------------------------------------------
        kw_title_label = ctk.CTkLabel(
            tab_keyword,
            text="해외 미디어 검색 키워드 (선수명, 매치업):",
            font=ctk.CTkFont(weight="bold")
        )
        kw_title_label.grid(row=0, column=0, sticky="w", padx=10, pady=(6, 2))

        self.entry_keyword = ctk.CTkEntry(
            tab_keyword,
            placeholder_text="예: Lee Kang-in Atletico Osasuna 또는 이강인 아틀레티코마드리드 오사수나",
            width=680
        )
        self.entry_keyword.insert(0, "Lee Kang-in Atletico Osasuna")
        self.entry_keyword.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 8))

        kw_target_label = ctk.CTkLabel(tab_keyword, text="검색 대상 언론사:")
        kw_target_label.grid(row=2, column=0, sticky="w", padx=10, pady=(4, 2))

        self.media_choice = ctk.CTkSegmentedButton(
            tab_keyword,
            values=["Marca (스페인)", "AS.com (스페인)", "전체 스포츠지 (Google News)"]
        )
        self.media_choice.set("Marca (스페인)")
        self.media_choice.grid(row=3, column=0, sticky="w", padx=10, pady=(0, 10))

        kw_info_label = ctk.CTkLabel(
            tab_keyword,
            text="* 키워드로 관련 기사를 검색 후 상위 기사의 댓글 섹션으로 자동 진입하여 해외 팬들의 반응을 추출합니다.",
            text_color="#94a3b8",
            font=ctk.CTkFont(size=11)
        )
        kw_info_label.grid(row=4, column=0, columnspan=2, sticky="w", padx=10, pady=(0, 6))

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

        # 시작 안내 메시지
        self._log_output("[안내] 해외 스포츠 언론사 댓글 수집기 프로그램이 준비되었습니다.\n"
                         "1. 기사 URL을 입력하거나 키워드 검색 모드를 선택하세요.\n"
                         "2. '크롤링 시작'을 클릭하면 브라우저가 백그라운드 스레드에서 안전하게 실행됩니다.\n"
                         "--------------------------------------------------------------------------------\n")

    # =================================================================
    # 프리셋 설정 헬퍼 함수
    # =================================================================
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

    # =================================================================
    # 로그 및 상태 업데이트 (스레드 안전)
    # =================================================================
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

    # =================================================================
    # 크롤링 스레드 제어
    # =================================================================
    def start_crawling_thread(self):
        """UI가 멈추지 않도록 백그라운드 Worker Thread 생성 및 실행"""
        if self.is_crawling:
            return

        current_tab = self.tabview.get()
        target_url = self.entry_url.get().strip()
        keyword = self.entry_keyword.get().strip()

        # 유효성 검사
        if current_tab == "단일 기사 URL 직접 수집":
            if not target_url or not (target_url.startswith("http://") or target_url.startswith("https://")):
                messagebox.showwarning("입력 오류", "올바른 기사 URL 형식(http:// 또는 https://)을 입력해 주세요.")
                return
        else:
            if not keyword:
                messagebox.showwarning("입력 오류", "검색할 키워드를 입력해 주세요.")
                return

        # UI 버튼 상태 갱신
        self.is_crawling = True
        self.btn_start.configure(state="disabled", fg_color="#6b7280")
        self.btn_stop.configure(state="normal")
        self.collected_comments = []
        self._set_count(0)

        # 백그라운드 스레드 시작
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

    # =================================================================
    # 핵심 크롤링 Worker 로직
    # =================================================================
    def _run_crawler_worker(self):
        """백그라운드에서 동작하는 실제 크롤러 본체"""
        current_tab = self.tabview.get()

        try:
            self._set_status("브라우저 초기화 중 (undetected-chromedriver 가동)...")
            self._log_output("\n[시작] 봇 탐지 우회 브라우저를 구동합니다...\n")

            # undetected_chromedriver 옵션 설정
            options = uc.ChromeOptions()
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-popup-blocking")
            # 필요 시 헤드리스 모드: options.add_argument("--headless=new")
            
            # 드라이버 인스턴스 생성
            self.driver = uc.Chrome(options=options)
            self.driver.set_page_load_timeout(35)

            if not self.is_crawling:
                return

            # 타겟 URL 결정
            if current_tab == "단일 기사 URL 직접 수집":
                target_url = self.entry_url.get().strip()
                self._crawl_single_article(target_url)
            else:
                keyword = self.entry_keyword.get().strip()
                selected_media = self.media_choice.get()
                self._search_and_crawl_articles(keyword, selected_media)

        except Exception as e:
            self._set_status(f"에러 발생: {str(e)[:40]}", color="#ef4444")
            self._log_output(f"\n[오류 발생] {str(e)}\n")
        finally:
            # 안전하게 드라이버 정리
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
            self._log_output("\n[완료] 크롤링 작업이 종료되었습니다.\n")

    def _crawl_single_article(self, url):
        """지정된 단일 기사 URL에 접속하여 댓글 수집"""
        iframe_sel = self.entry_iframe.get().strip()
        comment_sel = self.entry_comment_css.get().strip()

        self._set_status(f"기사 페이지 접속 중 ({url[:30]}...)")
        self._log_output(f">> 기사 접속: {url}\n")
        self.driver.get(url)

        # 페이지 로딩 및 쿠키 동의 팝업 처리 대기
        time.sleep(3)
        self._handle_cookie_consent()

        # 댓글이 로딩되도록 부드럽게 스크롤 내리기
        self._smooth_scroll_to_bottom(steps=6, delay=0.8)

        # iframe 처리 로직
        if iframe_sel:
            self._set_status("댓글 iframe 탐색 및 진입 중...")
            self._log_output(f">> iframe 탐색 시도: {iframe_sel}\n")
            self._switch_to_comment_iframe(iframe_sel)

        # 댓글 본문 요소 수집
        self._extract_comments(comment_sel)

    def _search_and_crawl_articles(self, keyword, media):
        """키워드로 관련 기사를 검색한 후 상위 기사의 댓글을 수집"""
        self._set_status(f"'{keyword}' 관련 기사 검색 중...")
        
        # 언론사별 도메인 타겟팅 쿼리 생성
        if "Marca" in media:
            search_query = f"site:marca.com {keyword}"
        elif "AS.com" in media:
            search_query = f"site:as.com {keyword}"
        else:
            search_query = f"site:marca.com OR site:as.com {keyword}"

        encoded_query = urllib.parse.quote_plus(search_query)
        search_url = f"https://www.google.com/search?q={encoded_query}&hl=es"

        self._log_output(f">> 구글 뉴스/기사 검색 진입: {search_query}\n")
        self.driver.get(search_url)
        time.sleep(3)
        self._handle_cookie_consent()

        # 검색 결과 링크 추출 (상위 3개 기사)
        found_links = []
        try:
            link_elements = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='marca.com'], a[href*='as.com']")
            for elem in link_elements:
                href = elem.get_attribute("href")
                if href and ("marca.com" in href or "as.com" in href):
                    # 기사 링크 패턴 필터링
                    if ("/futbol/" in href or "/primera/" in href or "/actualidad/" in href) and href not in found_links:
                        found_links.append(href)
                if len(found_links) >= 3:
                    break
        except Exception as e:
            self._log_output(f">> 기사 링크 추출 중 경고: {e}\n")

        if not found_links:
            self._log_output(">> 직접 일치하는 기사 링크를 찾지 못하여 검색 결과의 첫 번째 유효 링크로 진입합니다.\n")
            # 대체 셀렉터
            for a in self.driver.find_elements(By.CSS_SELECTOR, "div.g a"):
                h = a.get_attribute("href")
                if h and h.startswith("http") and "google" not in h:
                    found_links.append(h)
                    break

        if not found_links:
            self._log_output(">> 검색된 기사가 없습니다. 키워드를 영문(예: Lee Kang-in Atletico)으로 변경해 보세요.\n")
            return

        self._log_output(f">> 총 {len(found_links)}건의 관련 기사를 발견했습니다.\n")

        # 각 기사를 순차적으로 크롤링
        for idx, article_url in enumerate(found_links, 1):
            if not self.is_crawling:
                break
            self._log_output(f"\n==================================================\n")
            self._log_output(f"[{idx}/{len(found_links)}] 기사 분석 시작: {article_url}\n")
            self.driver.get(article_url)
            time.sleep(3)
            self._handle_cookie_consent()

            # 부드러운 스크롤 유도
            self._smooth_scroll_to_bottom(steps=5, delay=0.7)

            # 언론사별 기본 셀렉터 분기
            if "as.com" in article_url:
                iframe_candidates = "iframe[id*='c-comments'], iframe[id*='coral'], iframe[title*='comentarios']"
                comment_candidates = ".c-comments__body, .coral-comment-content, div[class*='comment-body'], [data-testid='comment-content']"
            else:
                iframe_candidates = "iframe[id*='ue-comments-iframe'], iframe[src*='coral'], iframe[title*='comentarios']"
                comment_candidates = ".ue-c-article__comment-content, .coral-comment-content, [data-testid='comment-content']"

            self._switch_to_comment_iframe(iframe_candidates)
            self._extract_comments(comment_candidates, article_url=article_url)
            time.sleep(2)

    # =================================================================
    # 세부 크롤링 지원 로직 (스크롤, 쿠키, iframe, 필터링)
    # =================================================================
    def _handle_cookie_consent(self):
        """유럽 언론사 특유의 GDPR/쿠키 동의 배너 자동 수락 시도"""
        cookie_selectors = [
            "button#didomi-notice-agree-button",
            "button[id*='accept']",
            "button[class*='accept']",
            "#onetrust-accept-btn-handler",
            "button[aria-label='Aceptar']"
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
            self._log_output(f">> 스크롤 중 알림: {e}\n")

    def _switch_to_comment_iframe(self, iframe_selector_str):
        """콤마로 구분된 후보 iframe 셀렉터 중 존재하는 iframe으로 switch_to"""
        # 먼저 부모 기본 프레임으로 복귀
        try:
            self.driver.switch_to.default_content()
        except Exception:
            pass

        selectors = [s.strip() for s in iframe_selector_str.split(",") if s.strip()]
        for sel in selectors:
            try:
                # WebDriverWait로 5초간 iframe 출현 대기
                wait = WebDriverWait(self.driver, 5)
                iframe_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, sel)))
                self.driver.switch_to.frame(iframe_element)
                self._log_output(f">> [성공] 댓글 iframe 진입 완료: {sel}\n")
                time.sleep(2)
                return True
            except Exception:
                continue

        # 모든 iframe 진입 실패 시에도 본문에 댓글이 직접 렌더링되었을 수 있으므로 기본 컨텐츠 유지
        self._log_output(">> 지정된 iframe을 찾지 못했거나 메인 DOM에 댓글이 존재합니다 (메인 프레임 탐색).\n")
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
                    self._log_output(f">> 셀렉터 매칭 성공 ({sel}): {len(elems)}개 감지\n")
                    break
            except Exception:
                continue

        # 만약 명시적 셀렉터로 못 찾은 경우, 일반적인 댓글 컨테이너 탐색
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
            self._log_output(">> 등록된 댓글이 없거나 아직 로딩되지 않았습니다.\n")
            return

        # 필터링 및 출력
        banned_phrases = ["cargar más", "responder", "reportar", "compartir", "iniciar sesión", "ver más comentarios"]
        count = 0

        for elem in found_elements:
            if not self.is_crawling:
                break
            try:
                raw_text = elem.text.strip()
                # 1. 5자 미만 필터링
                if len(raw_text) < 5:
                    continue

                # 2. 메뉴/광고성 UI 텍스트 필터링
                lower_text = raw_text.lower()
                if any(bp in lower_text for bp in banned_phrases):
                    continue

                # 3. 중복 수집 방지
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
                    f"[{item_data['index']}] 해외 팬 반응\n"
                    f"{raw_text}\n"
                    f"--------------------------------------------------------------------------------\n"
                )
                self._log_output(display_block)

            except Exception:
                continue

        self._log_output(f">> 이번 기사에서 유효 댓글 {count}건 추출 완료.\n")

    # =================================================================
    # 결과 저장 (TXT / CSV)
    # =================================================================
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
    # 라이브러리 설치 안내
    try:
        import customtkinter
        import undetected_chromedriver
        import selenium
    except ImportError as e:
        print("[경고] 필수 라이브러리가 설치되지 않았습니다.")
        print("터미널 또는 명령 프롬프트(CMD)에서 아래 명령어를 실행하세요:")
        print("pip install customtkinter undetected-chromedriver selenium")
        sys.exit(1)

    # GUI 앱 인스턴스 실행
    app = SportsCommentCrawlerGUI()
    app.mainloop()
