"""
해외 스포츠 언론사(AS.com, Marca 등) 동적 댓글 및 해외 반응 수집기
기술 스택: CustomTkinter (모던 다크 테마 GUI) + Selenium & undetected-chromedriver (Cloudflare/봇 차단 우회)
"""

import os
import re
import sys
import time
import json
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import threading
try:
    from tkinter import messagebox, filedialog
    import customtkinter as ctk
except ImportError:
    ctk = None
    messagebox = None
    filedialog = None

# Selenium 및 undetected-chromedriver 모듈
try:
    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
except ImportError:
    pass


_BaseClass = ctk.CTk if ctk is not None else object


class SportsCommentCrawlerGUI(_BaseClass):
    def __init__(self):
        if ctk is not None:
            super().__init__()
            # 1. 윈도우 기본 설정 (다크 모드 및 기본 테마)
            ctk.set_appearance_mode("dark")
            ctk.set_default_color_theme("blue")

            self.title("해외 스포츠 미디어 댓글 크롤러 (Marca & AS.com 반응 분석기)")
            self.geometry("960, 820")
            self.minsize(800, 640)

        # 크롤링 제어 플래그 및 드라이버 인스턴스
        self.is_crawling = False
        self.driver = None
        self.collected_comments = []

        # UI 위젯 빌드
        if ctk is not None:
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
            text="Google News RSS 무차단 기사 탐색 + Marca(Coral) & AS.com(Disqus) 동적 댓글 정밀 수집",
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
            kw_preset_frame, text="이강인 (PSG)", width=105, height=24,
            command=lambda: self._set_keyword_text("이강인 PSG Champions"),
            fg_color="#334155", hover_color="#475569"
        )
        btn_kw1.pack(side="left", padx=3)

        btn_kw2 = ctk.CTkButton(
            kw_preset_frame, text="손흥민 (토트넘)", width=105, height=24,
            command=lambda: self._set_keyword_text("Son Heung-min Tottenham"),
            fg_color="#334155", hover_color="#475569"
        )
        btn_kw2.pack(side="left", padx=3)

        btn_kw3 = ctk.CTkButton(
            kw_preset_frame, text="김민재 (뮌헨)", width=105, height=24,
            command=lambda: self._set_keyword_text("Kim Min-jae Bayern"),
            fg_color="#334155", hover_color="#475569"
        )
        btn_kw3.pack(side="left", padx=3)

        btn_kw4 = ctk.CTkButton(
            kw_preset_frame, text="황희찬 (울버햄튼)", width=110, height=24,
            command=lambda: self._set_keyword_text("Hwang Hee-chan Wolves"),
            fg_color="#334155", hover_color="#475569"
        )
        btn_kw4.pack(side="left", padx=3)

        btn_kw5 = ctk.CTkButton(
            kw_preset_frame, text="쿠보 다케후사", width=95, height=24,
            command=lambda: self._set_keyword_text("久保建英 ソシエダ"),
            fg_color="#334155", hover_color="#475569"
        )
        btn_kw5.pack(side="left", padx=3)

        kw_target_label = ctk.CTkLabel(tab_keyword, text="검색 대상 국가 / 메이저 스포츠 언론사:")
        kw_target_label.grid(row=3, column=0, sticky="w", padx=10, pady=(4, 2))

        self.media_choice = ctk.CTkComboBox(
            tab_keyword,
            values=[
                "글로벌 메이저 스포츠지 전체 (스페인/영국/독일/프랑스/이탈리아/일본/중국)",
                "🇪🇸 스페인 (Marca + AS.com)",
                "🇪🇸 Marca (스페인 1위)",
                "🇪🇸 AS.com (스페인 2위)",
                "🇬🇧 영국 (Daily Mail + The Sun + Guardian)",
                "🇩🇪 독일 (Sport1 + Sport.de + Kicker)",
                "🇫🇷 프랑스 (Foot Mercato + L'Equipe + MaxiFoot)",
                "🇮🇹 이탈리아 (Gazzetta dello Sport + Corriere + Tuttosport)",
                "🇯🇵 일본 (Yahoo Japan Sports + FootballChannel + SoccerDigest)",
                "🇨🇳 중국 (Hupu 虎扑 + Sina Sports + Dongqiudi)"
            ],
            width=520,
            state="readonly"
        )
        self.media_choice.set("글로벌 메이저 스포츠지 전체 (스페인/영국/독일/프랑스/이탈리아/일본/중국)")
        self.media_choice.grid(row=4, column=0, sticky="w", padx=10, pady=(0, 8))

        # 매칭 기준 및 수집 기사 수 설정
        kw_opts_frame = ctk.CTkFrame(tab_keyword, fg_color="transparent")
        kw_opts_frame.grid(row=5, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 4))

        kw_mode_lbl = ctk.CTkLabel(kw_opts_frame, text="기사 매칭 기준:", font=ctk.CTkFont(size=12, weight="bold"))
        kw_mode_lbl.pack(side="left", padx=(0, 6))

        self.match_mode = ctk.CTkSegmentedButton(
            kw_opts_frame,
            values=["부분 일치 (제목/본문에 단어 포함 시 수집)", "전체 일치"],
            width=300
        )
        self.match_mode.set("부분 일치 (제목/본문에 단어 포함 시 수집)")
        self.match_mode.pack(side="left", padx=(0, 16))

        kw_limit_lbl = ctk.CTkLabel(kw_opts_frame, text="수집 기사 수:", font=ctk.CTkFont(size=12, weight="bold"))
        kw_limit_lbl.pack(side="left", padx=(0, 6))

        self.article_limit = ctk.CTkSegmentedButton(
            kw_opts_frame,
            values=["2개", "3개", "5개"],
            width=130
        )
        self.article_limit.set("3개")
        self.article_limit.pack(side="left")

        # 댓글 수집 범위 (전체 댓글 수집 여부)
        kw_depth_frame = ctk.CTkFrame(tab_keyword, fg_color="transparent")
        kw_depth_frame.grid(row=6, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 4))

        kw_depth_lbl = ctk.CTkLabel(kw_depth_frame, text="기사당 댓글 수집 목표:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#38bdf8")
        kw_depth_lbl.pack(side="left", padx=(0, 8))

        self.comment_depth = ctk.CTkSegmentedButton(
            kw_depth_frame,
            values=["전체 댓글 모두 (끝까지)", "최대 300개 (권장)", "최대 100개", "최대 50개"],
            width=480
        )
        self.comment_depth.set("전체 댓글 모두 (끝까지)")
        self.comment_depth.pack(side="left")

        kw_info_label = ctk.CTkLabel(
            tab_keyword,
            text="* [전체 댓글 수집 지원] 첫 페이지만 긁는 것이 아니라 '더보기(Load More)' 클릭 및 API 페이징으로 기사에 등록된 수백 개의 전체 댓글을 끝까지 수집합니다.",
            text_color="#38bdf8",
            font=ctk.CTkFont(size=11)
        )
        kw_info_label.grid(row=7, column=0, columnspan=2, sticky="w", padx=10, pady=(0, 4))

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
        
        preset_label = ctk.CTkLabel(preset_frame, text="국가별 프리셋:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#38bdf8")
        preset_label.pack(side="left", padx=(0, 8))

        btn_preset_marca = ctk.CTkButton(
            preset_frame, text="🇪🇸 Marca", width=80, height=26,
            command=self._set_preset_marca, fg_color="#2563eb", hover_color="#1d4ed8"
        )
        btn_preset_marca.pack(side="left", padx=2)

        btn_preset_as = ctk.CTkButton(
            preset_frame, text="🇪🇸 AS.com", width=80, height=26,
            command=self._set_preset_as, fg_color="#059669", hover_color="#047857"
        )
        btn_preset_as.pack(side="left", padx=2)

        btn_preset_fm = ctk.CTkButton(
            preset_frame, text="🇫🇷 Foot Mercato", width=105, height=26,
            command=self._set_preset_footmercato, fg_color="#7c3aed", hover_color="#6d28d9"
        )
        btn_preset_fm.pack(side="left", padx=2)

        btn_preset_uk = ctk.CTkButton(
            preset_frame, text="🇬🇧 Daily Mail/The Sun", width=130, height=26,
            command=self._set_preset_uk, fg_color="#b91c1c", hover_color="#991b1b"
        )
        btn_preset_uk.pack(side="left", padx=2)

        btn_preset_de_it = ctk.CTkButton(
            preset_frame, text="🇩🇪 🇮🇹 독/이탈리아", width=105, height=26,
            command=self._set_preset_germany_italy, fg_color="#d97706", hover_color="#b45309"
        )
        btn_preset_de_it.pack(side="left", padx=2)

        btn_preset_jp = ctk.CTkButton(
            preset_frame, text="🇯🇵 야후재팬/Qoly", width=105, height=26,
            command=self._set_preset_japan, fg_color="#0891b2", hover_color="#0e7490"
        )
        btn_preset_jp.pack(side="left", padx=2)

        btn_preset_cn = ctk.CTkButton(
            preset_frame, text="🇨🇳 Hupu/동치우디", width=110, height=26,
            command=self._set_preset_china, fg_color="#be185d", hover_color="#9d174d"
        )
        btn_preset_cn.pack(side="left", padx=2)

        # iframe 선택자
        iframe_label = ctk.CTkLabel(tab_direct, text="iframe 선택자 (선택 사항):")
        iframe_label.grid(row=3, column=0, sticky="w", padx=10, pady=(4, 2))

        self.entry_iframe = ctk.CTkEntry(
            tab_direct,
            placeholder_text="예: iframe[id*='ue-comments-iframe'], iframe[src*='coral'], iframe[title*='comentarios']",
            width=680
        )
        self.entry_iframe.grid(row=4, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 6))

        # 댓글 CSS 선택자
        css_label = ctk.CTkLabel(tab_direct, text="댓글 본문 CSS 선택자:")
        css_label.grid(row=5, column=0, sticky="w", padx=10, pady=(4, 2))

        self.entry_comment_css = ctk.CTkEntry(
            tab_direct,
            placeholder_text="예: .ue-c-article__comment-content, .coral-comment-content, div[class*='comment-body']",
            width=680
        )
        self.entry_comment_css.grid(row=6, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 6))

        # 단일 기사 댓글 수집 목표
        direct_depth_frame = ctk.CTkFrame(tab_direct, fg_color="transparent")
        direct_depth_frame.grid(row=7, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 6))

        direct_depth_lbl = ctk.CTkLabel(direct_depth_frame, text="댓글 수집 목표 범위:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#38bdf8")
        direct_depth_lbl.pack(side="left", padx=(0, 8))

        self.direct_comment_depth = ctk.CTkSegmentedButton(
            direct_depth_frame,
            values=["전체 댓글 모두 (끝까지)", "최대 300개 (권장)", "최대 100개", "최대 50개"],
            width=480
        )
        self.direct_comment_depth.set("전체 댓글 모두 (끝까지)")
        self.direct_comment_depth.pack(side="left")

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
        """AS.com 전용 프리셋 주입 (Disqus 기반)"""
        self.entry_iframe.delete(0, "end")
        self.entry_iframe.insert(0, "iframe[src*='disqus.com/embed/comments'], iframe[id*='dsq-app'], iframe[title*='Disqus'], iframe[id*='c-comments'], iframe[src*='coral']")
        self.entry_comment_css.delete(0, "end")
        self.entry_comment_css.insert(0, ".post-message, .post-message p, [data-role='post-content'], .c-comments__body, div[class*='comment-body']")
        self._set_status("AS.com 프리셋(Disqus 최적화)이 적용되었습니다.")

    def _set_preset_footmercato(self):
        """Foot Mercato (프랑스) 전용 프리셋 주입"""
        self.entry_iframe.delete(0, "end")
        self.entry_iframe.insert(0, "iframe[src*='disqus.com/embed/comments'], iframe[id*='dsq-app'], iframe[title*='Disqus']")
        self.entry_comment_css.delete(0, "end")
        self.entry_comment_css.insert(0, ".post-message, .post-message p, [data-role='post-content'], .comment__text")
        self._set_status("Foot Mercato (프랑스 Disqus) 프리셋이 적용되었습니다.")

    def _set_preset_uk(self):
        """영국 (Daily Mail / The Sun / Guardian) 전용 프리셋 주입"""
        self.entry_iframe.delete(0, "end")
        self.entry_iframe.insert(0, "iframe[src*='spot.im'], iframe[src*='openweb'], iframe[id*='sp_message_iframe'], iframe[src*='coral']")
        self.entry_comment_css.delete(0, "end")
        self.entry_comment_css.insert(0, ".comment__text, .messageContent, .item-comment, [data-testid='comment-content'], .dsq-comment-body, div[class*='content-message']")
        self._set_status("영국 언론사 (Daily Mail / The Sun / OpenWeb) 프리셋이 적용되었습니다.")

    def _set_preset_germany_italy(self):
        """독일 / 이탈리아 (Sport1, Sport.de, Gazzetta, Corriere) 전용 프리셋 주입"""
        self.entry_iframe.delete(0, "end")
        self.entry_iframe.insert(0, "iframe[src*='spot.im'], iframe[src*='openweb'], iframe[src*='disqus'], iframe[id*='comment']")
        self.entry_comment_css.delete(0, "end")
        self.entry_comment_css.insert(0, ".sp_message, .comment-content, div[class*='comment-body'], [data-role='post-content'], .post-message")
        self._set_status("독일/이탈리아 언론사 프리셋이 적용되었습니다.")

    def _set_preset_japan(self):
        """일본 (Yahoo Japan Sports, Qoly, FootballChannel) 전용 프리셋 주입"""
        self.entry_iframe.delete(0, "end")
        self.entry_iframe.insert(0, "iframe[id*='comment'], iframe[src*='disqus'], iframe[src*='comment']")
        self.entry_comment_css.delete(0, "end")
        self.entry_comment_css.insert(0, "p[class*='CommentItem__comment'], p[class*='comment'], [data-testid='comment-content'], .post-message, div[class*='comment-text']")
        self._set_status("일본 야후재팬 / 축구 언론사 프리셋이 적용되었습니다.")

    def _set_preset_china(self):
        """중국 (Hupu 虎扑, Dongqiudi 懂球帝, Sina Sports) 전용 프리셋 주입"""
        self.entry_iframe.delete(0, "end")
        self.entry_iframe.insert(0, "iframe[id*='comment'], iframe[src*='comment']")
        self.entry_comment_css.delete(0, "end")
        self.entry_comment_css.insert(0, ".thread-content-detail, .post-reply-list-content, [class*='comment-content'], .comment-item-content, div[class*='reply_content']")
        self._set_status("중국 호푸(Hupu) / 동치우디 프리셋이 적용되었습니다.")

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

    def _analyze_query_and_build_tokens(self, raw_input):
        """
        사용자 입력어로부터:
        1. Google News RSS 다각도 검색 쿼리 리스트 생성
        2. 기사 제목 및 본문(원문)에 포함되었는지 검사할 부분 일치 토큰 세트 생성
        """
        entity_map = [
            # 한국 및 글로벌 주요 선수
            ("이강인", "player", "Kang-in", ["kang-in", "kang in", "lee kang-in", "lee kang in", "kangin", "イ・ガンイン", "李刚仁"]),
            ("강인", "player", "Kang-in", ["kang-in", "kang in"]),
            ("손흥민", "player", "Son Heung-min", ["son", "heung-min", "sonny", "ソン・フンミン", "孙兴慜"]),
            ("김민재", "player", "Kim Min-jae", ["kim min-jae", "min-jae", "minjae", "キム・ミンジェ", "金玟哉"]),
            ("황희찬", "player", "Hwang Hee-chan", ["hwang", "hee-chan", "황희찬", "黄喜灿"]),
            ("쿠보", "player", "Kubo", ["kubo", "takefusa kubo", "久保建英"]),
            ("미토마", "player", "Mitoma", ["mitoma", "kaoru mitoma", "三笘薫"]),
            ("음바페", "player", "Mbappe", ["mbappe", "mbappé"]),
            ("홀란드", "player", "Haaland", ["haaland"]),
            ("메시", "player", "Messi", ["messi"]),
            ("호날두", "player", "Ronaldo", ["ronaldo", "cr7"]),
            # 주요 클럽 팀
            ("아틀레티코마드리드", "team", "Atletico Madrid", ["atletico", "atlético", "atleti", "colchoneros", "colchonero"]),
            ("아틸레티코마드리드", "team", "Atletico Madrid", ["atletico", "atlético", "atleti"]),
            ("아틀레티코", "team", "Atletico", ["atletico", "atlético", "atleti"]),
            ("아틸레티코", "team", "Atletico", ["atletico", "atlético", "atleti"]),
            ("오사수나", "team", "Osasuna", ["osasuna", "rojillos", "rojillo"]),
            ("레알마드리드", "team", "Real Madrid", ["real madrid", "madrid", "merengue"]),
            ("바르셀로나", "team", "Barcelona", ["barcelona", "barca", "barça", "culer"]),
            ("파리생제르맹", "team", "PSG", ["psg", "paris", "paris sg"]),
            ("파리", "team", "PSG", ["psg", "paris"]),
            ("마요르카", "team", "Mallorca", ["mallorca", "bermellon"]),
            ("발렌시아", "team", "Valencia", ["valencia", "che"]),
            ("토트넘", "team", "Tottenham", ["tottenham", "spurs"]),
            ("바이에른뮌헨", "team", "Bayern", ["bayern", "munich", "münchen"]),
            ("뮌헨", "team", "Bayern", ["bayern", "munich", "münchen"]),
            ("울버햄튼", "team", "Wolves", ["wolves", "wolverhampton"]),
            ("맨시티", "team", "Man City", ["man city", "manchester city"]),
            ("아스날", "team", "Arsenal", ["arsenal", "gunners"]),
            ("리버풀", "team", "Liverpool", ["liverpool"]),
            ("소시에다드", "team", "Real Sociedad", ["sociedad", "real sociedad", "ソシエダ"]),
            ("유벤투스", "team", "Juventus", ["juventus", "juve"]),
            ("밀란", "team", "Milan", ["ac milan", "milan", "rossoneri"]),
            ("인테르", "team", "Inter", ["inter", "nerazzurri"]),
        ]

        match_tokens = set()
        for w in re.findall(r'[\w\-]+', raw_input.lower()):
            if len(w) >= 2:
                match_tokens.add(w)

        found_players = []
        found_teams = []
        temp_text = raw_input

        for kor, cat, eng, syns in entity_map:
            if kor in temp_text:
                match_tokens.add(kor.lower())
                match_tokens.add(eng.lower())
                for s in syns:
                    match_tokens.add(s.lower())
                if cat == "player" and eng not in found_players:
                    found_players.append(eng)
                elif cat == "team" and eng not in found_teams:
                    found_teams.append(eng)
                temp_text = temp_text.replace(kor, " ")

        queries = []
        if found_players and found_teams:
            queries.append(f"{found_players[0]} {' '.join(found_teams)}")
            for t in found_teams:
                queries.append(f"{found_players[0]} {t}")
            if len(found_teams) >= 2:
                queries.append(f"{found_teams[0]} {found_teams[1]}")
            queries.append(f"{found_players[0]}")
        elif found_players:
            queries.append(f"{found_players[0]}")
        elif found_teams:
            queries.append(" ".join(found_teams))
        else:
            queries.append(raw_input)

        return queries, match_tokens

    def _fetch_candidate_articles(self, search_queries, media, pool_limit=10):
        """다양한 검색 쿼리 조합 및 선택된 국가/언론사에 맞춰 Google News RSS에서 중복 없이 후보 기사 추출"""
        # 선택된 국가에 따른 언어/국가 파라미터 및 site_filter 결정
        hl_gl_map = {
            "스페인": ("hl=es&gl=ES&ceid=ES:es", "site:marca.com OR site:as.com"),
            "Marca": ("hl=es&gl=ES&ceid=ES:es", "site:marca.com"),
            "AS.com": ("hl=es&gl=ES&ceid=ES:es", "site:as.com"),
            "영국": ("hl=en-GB&gl=GB&ceid=GB:en", "site:dailymail.co.uk OR site:thesun.co.uk OR site:theguardian.com"),
            "독일": ("hl=de&gl=DE&ceid=DE:de", "site:sport1.de OR site:sport.de OR site:kicker.de"),
            "프랑스": ("hl=fr&gl=FR&ceid=FR:fr", "site:footmercato.net OR site:lequipe.fr OR site:maxifoot.fr"),
            "이탈리아": ("hl=it&gl=IT&ceid=IT:it", "site:gazzetta.it OR site:corrieredellosport.it OR site:tuttosport.com"),
            "일본": ("hl=ja&gl=JP&ceid=JP:ja", "site:news.yahoo.co.jp OR site:football-zone.net OR site:soccerdigestweb.com OR site:qoly.jp"),
            "중국": ("hl=zh-CN&gl=CN&ceid=CN:zh-Hans", "site:hupu.com OR site:dongqiudi.com OR site:sports.sina.com.cn")
        }

        # 기본값 (글로벌 전체 선택 시)
        region_params = [
            ("hl=es&gl=ES&ceid=ES:es", "site:marca.com OR site:as.com"),
            ("hl=en-GB&gl=GB&ceid=GB:en", "site:dailymail.co.uk OR site:thesun.co.uk"),
            ("hl=fr&gl=FR&ceid=FR:fr", "site:footmercato.net OR site:maxifoot.fr"),
            ("hl=de&gl=DE&ceid=DE:de", "site:sport1.de OR site:sport.de"),
            ("hl=it&gl=IT&ceid=IT:it", "site:gazzetta.it OR site:corrieredellosport.it"),
            ("hl=ja&gl=JP&ceid=JP:ja", "site:news.yahoo.co.jp OR site:qoly.jp"),
            ("hl=zh-CN&gl=CN&ceid=CN:zh-Hans", "site:hupu.com OR site:dongqiudi.com")
        ]

        # 사용자 지정 언론사 선택 확인
        for key, val in hl_gl_map.items():
            if key in media:
                region_params = [val]
                break

        candidates = []
        seen_urls = set()

        for lang_param, site_filter in region_params:
            if not self.is_crawling or len(candidates) >= pool_limit:
                break
            for q in search_queries:
                if not self.is_crawling or len(candidates) >= pool_limit:
                    break
                full_query = f"{q} {site_filter}"
                encoded_query = urllib.parse.quote_plus(full_query)
                rss_url = f"https://news.google.com/rss/search?q={encoded_query}&{lang_param}"

                self._log_output(f">> [RSS 탐색] {full_query}\n")
                req = urllib.request.Request(
                    rss_url,
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                )
                try:
                    with urllib.request.urlopen(req, timeout=8) as response:
                        xml_data = response.read()
                        root = ET.fromstring(xml_data)
                        items = root.findall(".//item")
                        for it in items[:6]:
                            title_elem = it.find("title")
                            link_elem = it.find("link")
                            if title_elem is not None and link_elem is not None:
                                t = (title_elem.text or "제목 없음").strip()
                                l = (link_elem.text or "").strip()
                                if l and l not in seen_urls:
                                    seen_urls.add(l)
                                    candidates.append({"title": t, "url": l})
                except Exception as e:
                    self._log_output(f">> RSS 응답 안내 ({q}): {e}\n")

        return candidates[:pool_limit]

    def _decode_google_news_url(self, gnews_url):
        """
        Google News RSS 리디렉션 URL(https://news.google.com/rss/articles/...)을
        Google batchexecute Fbv4je RPC를 통해 실제 언론사 기사 원문 URL로 고속 디코딩합니다.
        스페인, 영국, 독일, 프랑스, 이탈리아, 일본, 중국 등 글로벌 언론사를 모두 지원합니다.
        """
        if "news.google.com" not in gnews_url:
            return gnews_url

        try:
            m = re.search(r'/articles/([a-zA-Z0-9_\-]+)', gnews_url)
            if not m:
                return gnews_url
            article_id = m.group(1)

            req_url = f"https://news.google.com/rss/articles/{article_id}"
            req = urllib.request.Request(req_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                html = resp.read().decode("utf-8", errors="ignore")

            sig_m = re.search(r'data-n-a-sg=\"([^\"]+)\"', html)
            ts_m = re.search(r'data-n-a-ts=\"([^\"]+)\"', html)
            if not sig_m or not ts_m:
                return gnews_url

            sig = sig_m.group(1)
            ts = ts_m.group(1)

            req_obj = [
                "Fbv4je",
                f'[\"garturlreq\",[[\"X\",\"X\",[\"X\",\"X\"],null,null,null,1,\"US:en\",null,1,null,null,null,null,null,0,1],\"en-US\",\"US\",1,[2],null,null,null,null,null,0,1],\"{article_id}\",{ts},\"{sig}\"]'
            ]
            payload = urllib.parse.urlencode({"f.req": json.dumps([[req_obj]])})
            rpc_req = urllib.request.Request(
                "https://news.google.com/_/DotsSplashUi/data/batchexecute",
                data=payload.encode("utf-8"),
                headers={
                    "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                }
            )
            with urllib.request.urlopen(rpc_req, timeout=8) as resp:
                res = resp.read().decode("utf-8", errors="ignore")
                found = re.findall(r'https?://[^\s\"\'\\\]]+', res)
                target_domains = [
                    "marca.com", "as.com", "dailymail.co.uk", "thesun.co.uk",
                    "theguardian.com", "sport1.de", "sport.de", "kicker.de",
                    "footmercato.net", "lequipe.fr", "maxifoot.fr",
                    "gazzetta.it", "corrieredellosport.it", "tuttosport.com",
                    "yahoo.co.jp", "football-zone.net", "soccerdigestweb.com", "qoly.jp",
                    "hupu.com", "dongqiudi.com", "sina.com.cn"
                ]
                for u in found:
                    for td in target_domains:
                        if td in u:
                            return u
                # 만약 위 도메인이 아니더라도 첫 번째 유효 http URL 반환
                for u in found:
                    if "google.com" not in u and len(u) > 15:
                        return u
        except Exception as e:
            self._log_output(f">> Google News URL 디코딩 알림: {e}\n")

        return gnews_url

    def _extract_marca_comments_api(self, real_url, max_comments=5000):
        """
        Marca 전용: 기사 HTML 내 data-commentId를 파싱하여
        공식 댓글 서비스 API(listar.html)에서 순차 페이징(pagina)을 통해 기사에 등록된 전체 댓글을 누락 없이 즉시 수집합니다.
        브라우저 렌더러 지연 및 iframe 비동기 미로드를 100% 우회합니다.
        """
        try:
            # 1. 브라우저 페이지 소스 또는 direct fetch로 commentId 추출
            page_src = ""
            if self.driver:
                try:
                    page_src = self.driver.page_source or ""
                except Exception:
                    page_src = ""

            if not page_src or "data-commentId" not in page_src:
                req = urllib.request.Request(real_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
                with urllib.request.urlopen(req, timeout=6) as resp:
                    page_src = resp.read().decode("utf-8", errors="ignore")

            cids = re.findall(r'data-commentId=[\"\'](\d+)[\"\']', page_src)
            if not cids:
                return []

            cid = cids[0]
            base_url = f"https://www.marca.com/servicios/noticias/comentarios/comunidad/listar.html?noticia={cid}&version=v2"
            
            # 첫 페이지(최신 댓글) 요청
            api_req = urllib.request.Request(
                base_url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "application/json, text/plain, */*",
                    "Referer": "https://www.marca.com/"
                }
            )
            with urllib.request.urlopen(api_req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="ignore"))

            total_comments = data.get("total", 0)
            items = data.get("items", [])
            comments_map = {}

            def add_items(raw_items):
                for it in raw_items:
                    cid_item = it.get("id")
                    if not cid_item or cid_item in comments_map:
                        continue
                    body = it.get("body") or it.get("cuerpo") or ""
                    user = it.get("user") or it.get("alias") or "스페인 팬"
                    date_str = it.get("date") or ""
                    order_num = it.get("order", 0)
                    if len(body.strip()) >= 5:
                        comments_map[cid_item] = {
                            "order": order_num,
                            "user": user,
                            "date": date_str,
                            "text": body.strip()
                        }

            add_items(items)
            self._log_output(f">> [Marca API] 기사 내 총 {total_comments}개 등록 댓글 확인 (1차 수집: {len(comments_map)}건)\n")

            # 페이징 루프: min(order)를 기준으로 이전 10개씩 끝까지 또는 max_comments까지 연속 호출
            if items and total_comments > len(comments_map):
                current_min_order = min([it.get("order", 999999) for it in items if "order" in it])
                page_round = 1
                while current_min_order > 1 and len(comments_map) < max_comments and self.is_crawling:
                    page_round += 1
                    page_url = f"{base_url}&pagina={current_min_order}"
                    try:
                        p_req = urllib.request.Request(
                            page_url,
                            headers={
                                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                                "Referer": "https://www.marca.com/"
                            }
                        )
                        with urllib.request.urlopen(p_req, timeout=6) as p_resp:
                            p_data = json.loads(p_resp.read().decode("utf-8", errors="ignore"))
                            p_items = p_data.get("items", [])
                            if not p_items:
                                break
                            add_items(p_items)
                            new_min = min([it.get("order", 999999) for it in p_items if "order" in it])
                            if new_min >= current_min_order:
                                break
                            current_min_order = new_min

                            if page_round % 4 == 0 or len(comments_map) >= max_comments or current_min_order <= 1:
                                self._log_output(f">> [Marca 전체 댓글 수집 중] 총 {total_comments}개 중 {len(comments_map)}건 수집 완료...\n")
                            time.sleep(0.08)
                    except Exception:
                        break

            # 순서대로 정렬하여 반환
            sorted_comments = sorted(comments_map.values(), key=lambda x: x.get("order", 0), reverse=True)
            return sorted_comments
        except Exception as e:
            self._log_output(f">> [Marca API 탐색 알림] {e}\n")
            return []

    def _extract_as_comments_api(self, real_url):
        """
        AS.com 전용: 기사 HTML 내 externalDataCommentDisqus 식별자를 읽어
        Disqus 공식 임베드 스레드 엔드포인트에서 JSON 댓글 데이터를 직접 고속 수집합니다.
        """
        try:
            page_src = ""
            if self.driver:
                try:
                    page_src = self.driver.page_source or ""
                except Exception:
                    page_src = ""

            if not page_src or "externalDataCommentDisqus" not in page_src:
                req = urllib.request.Request(
                    real_url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                        "Accept-Language": "es-ES,es;q=0.9"
                    }
                )
                with urllib.request.urlopen(req, timeout=6) as resp:
                    page_src = resp.read().decode("utf-8", errors="ignore")

            m = re.search(r'<script id=\"externalDataCommentDisqus\"[^>]*>(.*?)</script>', page_src, re.DOTALL)
            if not m:
                return []

            d_info = json.loads(m.group(1)).get("data", {})
            page_id = d_info.get("pageIdentifier")
            page_url = d_info.get("pageUrl") or real_url
            if not page_id:
                return []

            t_u = urllib.parse.quote(page_url, safe="")
            dsq_url = f"https://disqus.com/embed/comments/?base=default&f=diarioas&t_i={page_id}&t_u={t_u}&s_o=default"

            dsq_req = urllib.request.Request(
                dsq_url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Referer": real_url
                }
            )
            with urllib.request.urlopen(dsq_req, timeout=8) as resp:
                d_html = resp.read().decode("utf-8", errors="ignore")
                for scr in re.findall(r'<script[^>]*>(.*?)</script>', d_html, re.DOTALL):
                    if '"posts":[' in scr:
                        posts = json.loads(scr).get("response", {}).get("posts", [])
                        comments = []
                        for p in posts:
                            msg = p.get("message", "")
                            clean_text = re.sub(r'<[^>]+>', ' ', msg).strip()
                            clean_text = clean_text.replace("&quot;", '"').replace("&amp;", '&').replace("&#39;", "'")
                            user = p.get("author", {}).get("name") or "익명"
                            date_str = p.get("createdAt") or ""
                            if len(clean_text) >= 5:
                                comments.append({
                                    "user": user,
                                    "date": date_str,
                                    "text": clean_text
                                })
                        return comments
        except Exception as e:
            self._log_output(f">> [AS Disqus 탐색 알림] {e}\n")
            return []

    def _extract_footmercato_comments(self, real_url):
        """
        프랑스 Foot Mercato 전용: Disqus 댓글 스레드 식별자를 추출하여
        공식 Disqus API 엔드포인트에서 댓글을 직접 고속 수집합니다.
        """
        try:
            page_src = ""
            if self.driver:
                try:
                    page_src = self.driver.page_source or ""
                except Exception:
                    page_src = ""

            if not page_src or "disqus_shortname" not in page_src and "disqus" not in page_src:
                req = urllib.request.Request(
                    real_url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8"
                    }
                )
                with urllib.request.urlopen(req, timeout=6) as resp:
                    page_src = resp.read().decode("utf-8", errors="ignore")

            m_id = re.search(r'disqus_identifier\s*=\s*[\'\"]([^\'\"]+)[\'\"]', page_src)
            m_short = re.search(r'disqus_shortname\s*=\s*[\'\"]([^\'\"]+)[\'\"]', page_src)
            shortname = m_short.group(1) if m_short else "footmercato"
            page_id = m_id.group(1) if m_id else ""

            if not page_id:
                # URL에서 기사 ID 추출 시도
                m_num = re.search(r'-(\d+)(?:\.html)?$', real_url)
                if m_num:
                    page_id = m_num.group(1)

            if not page_id:
                return []

            t_u = urllib.parse.quote(real_url, safe="")
            dsq_url = f"https://disqus.com/embed/comments/?base=default&f={shortname}&t_i={page_id}&t_u={t_u}&s_o=default"

            dsq_req = urllib.request.Request(
                dsq_url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Referer": real_url
                }
            )
            with urllib.request.urlopen(dsq_req, timeout=8) as resp:
                d_html = resp.read().decode("utf-8", errors="ignore")
                for scr in re.findall(r'<script[^>]*>(.*?)</script>', d_html, re.DOTALL):
                    if '"posts":[' in scr:
                        posts = json.loads(scr).get("response", {}).get("posts", [])
                        comments = []
                        for p in posts:
                            msg = p.get("message", "")
                            clean_text = re.sub(r'<[^>]+>', ' ', msg).strip()
                            clean_text = clean_text.replace("&quot;", '"').replace("&amp;", '&').replace("&#39;", "'")
                            user = p.get("author", {}).get("name") or "프랑스 팬"
                            date_str = p.get("createdAt") or ""
                            if len(clean_text) >= 5:
                                comments.append({
                                    "user": user,
                                    "date": date_str,
                                    "text": clean_text
                                })
                        return comments
        except Exception as e:
            self._log_output(f">> [Foot Mercato Disqus 알림] {e}\n")
        return []

    def _extract_dailymail_comments(self, real_url, max_comments=5000):
        """
        영국 Daily Mail 전용: 기사 ID를 추출하여 공식 reader-comments JSON API에서 전체 댓글 연속 페이징 수집
        """
        try:
            m = re.search(r'article-(\d+)', real_url)
            if not m:
                return []
            article_id = m.group(1)

            comments = []
            offset = 0
            limit = 50
            total = 999999

            while offset < total and len(comments) < max_comments and self.is_crawling:
                api_url = f"https://www.dailymail.co.uk/reader-comments/p/articles/comments/{article_id}?offset={offset}&limit={limit}&sortOrder=mostLiked"
                req = urllib.request.Request(
                    api_url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "Referer": real_url
                    }
                )
                try:
                    with urllib.request.urlopen(req, timeout=7) as resp:
                        data = json.loads(resp.read().decode("utf-8", errors="ignore"))
                        payload = data.get("payload", {})
                        total = payload.get("total", 0)
                        items = payload.get("page", [])
                        if not items:
                            break
                        for it in items:
                            msg = it.get("message", "")
                            clean_text = re.sub(r'<[^>]+>', ' ', msg).strip()
                            user = it.get("user", {}).get("screenName") or "영국 팬"
                            date_str = it.get("dateCreated") or ""
                            if len(clean_text) >= 5:
                                comments.append({
                                    "user": user,
                                    "date": date_str,
                                    "text": clean_text
                                })
                        offset += limit
                        if total > 50 and offset < total and len(comments) < max_comments:
                            self._log_output(f">> [Daily Mail 전체 댓글 수집 진행] 총 {total}개 중 {len(comments)}건 확보...\n")
                        time.sleep(0.12)
                except Exception:
                    break

            return comments
        except Exception as e:
            self._log_output(f">> [Daily Mail API 알림] {e}\n")
        return []

    def _extract_yahoo_japan_comments(self, real_url):
        """
        일본 Yahoo Japan Sports 전용: 기사 페이지 소스 내 임베드된 댓글 JSON 데이터 및 DOM 파싱
        """
        try:
            page_src = ""
            if self.driver:
                try:
                    page_src = self.driver.page_source or ""
                except Exception:
                    page_src = ""

            if not page_src:
                req = urllib.request.Request(
                    real_url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "Accept-Language": "ja-JP,ja;q=0.9"
                    }
                )
                with urllib.request.urlopen(req, timeout=6) as resp:
                    page_src = resp.read().decode("utf-8", errors="ignore")

            comments = []
            # 1. JSON-LD 또는 YAHOO.JP.templa.param 검색
            m = re.search(r'YAHOO\.JP\.templa\.param\s*=\s*({.*?});', page_src, re.DOTALL)
            if m:
                try:
                    param_data = json.loads(m.group(1))
                    comment_list = param_data.get("comment", {}).get("list", [])
                    for c in comment_list:
                        txt = c.get("text") or c.get("comment") or ""
                        user = c.get("user", {}).get("name") or "일본 네티즌"
                        if len(txt.strip()) >= 5:
                            comments.append({"user": user, "date": "", "text": txt.strip()})
                except Exception:
                    pass

            # 2. 정규식 DOM 텍스트 파싱 백업 (CommentItem 스타일)
            if not comments:
                items = re.findall(r'<p[^>]*class=\"[^\"]*CommentItem[^\"]*\"[^>]*>(.*?)</p>', page_src, re.DOTALL)
                for it in items:
                    clean = re.sub(r'<[^>]+>', ' ', it).strip()
                    clean = clean.replace("&quot;", '"').replace("&amp;", '&').replace("&#39;", "'")
                    if len(clean) >= 5 and "非表示" not in clean and "返信" not in clean:
                        comments.append({"user": "일본 네티즌", "date": "", "text": clean})

            return comments
        except Exception as e:
            self._log_output(f">> [Yahoo Japan 파싱 알림] {e}\n")
        return []

    def _extract_hupu_comments(self, real_url):
        """
        중국 Hupu 虎扑 전용: 포럼 스레드 본문 및 댓글 고속 추출
        """
        try:
            page_src = ""
            if self.driver:
                try:
                    page_src = self.driver.page_source or ""
                except Exception:
                    page_src = ""

            if not page_src:
                req = urllib.request.Request(
                    real_url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "Accept-Language": "zh-CN,zh;q=0.9"
                    }
                )
                with urllib.request.urlopen(req, timeout=6) as resp:
                    page_src = resp.read().decode("utf-8", errors="ignore")

            comments = []
            # Hupu reply-item 또는 post-reply-list 매칭
            replies = re.findall(r'<div[^>]*class=\"[^\"]*(?:post-reply-list-content|thread-content-detail|reply-item-content)[^\"]*\"[^>]*>(.*?)</div>', page_src, re.DOTALL)
            for r_text in replies:
                clean = re.sub(r'<[^>]+>', ' ', r_text).strip()
                clean = clean.replace("&quot;", '"').replace("&amp;", '&').replace("&#39;", "'")
                if len(clean) >= 5 and "虎扑" not in clean and "下载APP" not in clean:
                    comments.append({"user": "중국 축구팬", "date": "", "text": clean})

            return comments
        except Exception as e:
            self._log_output(f">> [Hupu 파싱 알림] {e}\n")
        return []

    def _check_article_content_match(self, title, headline, body_text, match_tokens, match_mode):
        """
        기사 제목 및 기사 원문(본문)에 키워드가 포함되어 있는지 부분 일치 검사
        사용자가 원하는 키워드가 하나라도 포함되면 True 반환 (부분 일치 모드)
        """
        title_lower = (title + " " + headline).lower()
        body_lower = body_text.lower()

        matched_in_title = set()
        matched_in_body = set()

        for tok in match_tokens:
            if tok in title_lower:
                matched_in_title.add(tok)
            if tok in body_lower:
                matched_in_body.add(tok)

        if "전체 일치" in match_mode:
            all_found = all((tok in title_lower or tok in body_lower) for tok in match_tokens if len(tok) > 2)
            return all_found, sorted(list(matched_in_title)), sorted(list(matched_in_body))

        # 기본: 부분 일치 모드 (제목이나 본문 중 어느 하나라도 키워드가 포함되어 있으면 일치)
        is_matched = bool(matched_in_title or matched_in_body)
        return is_matched, sorted(list(matched_in_title)), sorted(list(matched_in_body))

    def _trigger_open_comments_button(self):
        """Marca 및 AS.com의 댓글 펼치기/보기 버튼 자동 클릭 및 댓글 영역 활성화"""
        # 1. AS.com 전용 댓글 사이드 서랍/패널 및 Disqus 트리거 버튼 우선 탐색
        as_specific_selectors = [
            "button.a_sb_com",
            ".a_sb_bt.a_sb_com",
            "aside.a_com button.a_com_btn",
            ".a_com_nav button",
            "button[aria-label='Ver Comentarios']",
            "button[aria-label='Comentar']",
            ".w_sb_com",
            "aside.a_com .a_com_btn",
            ".mo-comments"
        ]
        for sel in as_specific_selectors:
            try:
                btns = self.driver.find_elements(By.CSS_SELECTOR, sel)
                for b in btns:
                    self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", b)
                    time.sleep(0.3)
                    self.driver.execute_script("arguments[0].click();", b)
                    self._log_output(f">> [AS 댓글 열기] '{sel}' 요소 클릭 트리거 실행\n")
                    time.sleep(1.0)
                    break
            except Exception:
                continue

        # 2. AS.com 댓글 모달 활성화 CSS 클래스 강제 주입 (body에 modal 클래스 추가)
        try:
            self.driver.execute_script("""
                document.body.classList.add('has-modal-comments', 'is-open-comments', 'mo-comments-open');
                var mo = document.querySelector('.mo.mo-comments');
                if (mo) {
                    mo.style.display = 'block';
                    mo.style.visibility = 'visible';
                }
                var dsqThread = document.querySelector('#disqus_thread');
                if (dsqThread) {
                    dsqThread.scrollIntoView({behavior: 'smooth', block: 'center'});
                }
            """)
        except Exception:
            pass

        # 3. 만약 AS.com에서 Disqus가 지연 로딩되지 않고 있다면 직접 Disqus embed 스크립트 실행 트리거
        try:
            self.driver.execute_script("""
                if (!document.querySelector("iframe[src*='disqus.com/embed/comments']")) {
                    var scriptData = document.querySelector('#externalDataCommentDisqus');
                    if (scriptData) {
                        try {
                            var data = JSON.parse(scriptData.textContent || scriptData.innerText).data;
                            if (window.disqus_config === undefined && data.pageUrl) {
                                window.disqus_config = function () {
                                    this.page.url = data.pageUrl;
                                    this.page.identifier = data.pageIdentifier;
                                    this.page.title = data.pageTitle;
                                };
                            }
                            var embedUrl = data.embedScriptUrl || 'https://diarioas.disqus.com/embed.js';
                            if (!document.querySelector("script[src*='disqus.com/embed.js']")) {
                                var s = document.createElement('script');
                                s.src = embedUrl;
                                s.setAttribute('data-timestamp', +new Date());
                                (document.head || document.body).appendChild(s);
                            }
                        } catch(e) {}
                    }
                }
            """)
        except Exception:
            pass

        # 4. 일반적인 언론사(Marca 등) 댓글 열기 버튼 클릭
        btn_selectors = [
            "button[id*='btn-comments']",
            "button[class*='comments']",
            "button[class*='comentarios']",
            "a[href*='#comentarios']",
            "button[data-testid='comment-button']",
            ".ue-c-article__comments-button",
            ".c-comments__toggle",
            "button[aria-label*='comentario']",
            "button[aria-label*='Comentarios']"
        ]
        for sel in btn_selectors:
            try:
                btns = self.driver.find_elements(By.CSS_SELECTOR, sel)
                for b in btns:
                    if b.is_displayed():
                        self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", b)
                        time.sleep(0.3)
                        self.driver.execute_script("arguments[0].click();", b)
                        self._log_output(f">> [댓글 펼치기] '{b.text or sel}' 버튼 클릭\n")
                        time.sleep(1.0)
                        return True
            except Exception:
                continue
        return False

    def _run_crawler_worker(self):
        """백그라운드에서 동작하는 실제 크롤러 본체"""
        current_tab = self.tabview.get()

        try:
            target_articles = []
            match_tokens = set()
            match_mode = "부분 일치"
            max_crawl_articles = 3

            # 댓글 수집 목표 한도 파싱 (전체 댓글 끝까지 또는 300, 100, 50개)
            if "단일 기사" in current_tab:
                depth_obj = getattr(self, "direct_comment_depth", None)
                depth_val = depth_obj.get() if depth_obj else "전체 댓글 모두 (끝까지)"
            else:
                depth_obj = getattr(self, "comment_depth", None)
                depth_val = depth_obj.get() if depth_obj else "전체 댓글 모두 (끝까지)"

            if "50개" in depth_val:
                max_comments_per_article = 50
            elif "100개" in depth_val:
                max_comments_per_article = 100
            elif "300개" in depth_val:
                max_comments_per_article = 300
            else:
                max_comments_per_article = 5000  # 사실상 제한 없는 기사의 전체 댓글 끝까지 수집

            # 1단계: 크롤링 대상 기사 목록 결정
            if "단일 기사" in current_tab:
                url = self.entry_url.get().strip()
                target_articles.append({"title": "지정 기사", "url": url})
            else:
                raw_kw = self.entry_keyword.get().strip()
                selected_media = self.media_choice.get()
                match_mode = self.match_mode.get()
                limit_str = self.article_limit.get()
                try:
                    max_crawl_articles = int(limit_str.replace("개", "").strip())
                except Exception:
                    max_crawl_articles = 3

                # 다각도 쿼리 및 부분 일치 토큰 추출
                search_queries, match_tokens = self._analyze_query_and_build_tokens(raw_kw)
                self._log_output(f"\n[키워드 분석 완료]\n"
                                 f"• 입력 키워드: '{raw_kw}'\n"
                                 f"• 매칭 모드: {match_mode}\n"
                                 f"• 본문/제목 탐색 토큰: {', '.join(sorted(list(match_tokens))[:10])} 등 총 {len(match_tokens)}개\n")

                # Google News RSS 피드로 후보 기사 풀 추출
                candidate_pool = self._fetch_candidate_articles(search_queries, selected_media, pool_limit=12)

                if not candidate_pool:
                    self._log_output(">> 직접 일치하는 RSS 기사를 찾지 못하여 Marca 축구 섹션으로 직접 탐색합니다.\n")
                    candidate_pool.append({
                        "title": "Marca 축구 메인 최신 기사",
                        "url": "https://www.marca.com/futbol.html"
                    })

                self._log_output(f"\n[후보 기사 총 {len(candidate_pool)}건 확보 - 순차적 본문/제목 매칭 검사 시작]:\n")
                for i, a in enumerate(candidate_pool, 1):
                    self._log_output(f"  {i}. {a['title']}\n")

                target_articles = candidate_pool

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

            try:
                self.driver = uc.Chrome(options=options, use_subprocess=True)
            except Exception as uc_err:
                self._log_output(f">> undetected_chromedriver 옵션 재조정: {uc_err}\n")
                self.driver = uc.Chrome(options=options)

            self.driver.set_page_load_timeout(30)

            # 3단계: 각 기사 접속 -> 제목 & 본문(원문) 부분 일치 검사 -> 댓글 추출
            crawled_count = 0

            for idx, art in enumerate(target_articles, 1):
                if not self.is_crawling:
                    break
                if crawled_count >= max_crawl_articles and "단일 기사" not in current_tab:
                    self._log_output(f"\n>> 설정한 최대 수집 기사 수({max_crawl_articles}개)에 도달하여 수집을 마칩니다.\n")
                    break

                self._ensure_window_valid()
                target_url = art["url"]

                # Google News RSS 링크인 경우 원문 기사 URL로 사전 고속 디코딩
                if "news.google.com" in target_url:
                    self._log_output(f"\n>> Google News RSS 링크를 실제 언론사 기사 URL로 변환 중...\n")
                    decoded_url = self._decode_google_news_url(target_url)
                    if decoded_url and decoded_url != target_url:
                        target_url = decoded_url
                        self._log_output(f">> [변환 완료] 원문 언론사 URL: {target_url}\n")

                self._log_output(f"\n==================================================\n")
                self._log_output(f"[후보 {idx}/{len(target_articles)}] 기사 확인 중: {art['title']}\n")
                self._log_output(f">> 대상 URL: {target_url}\n")
                self._set_status(f"[{crawled_count+1}/{max_crawl_articles}] 기사 확인 중...")

                try:
                    self.driver.set_page_load_timeout(20)
                    self.driver.get(target_url)
                    time.sleep(2)
                except Exception as get_err:
                    err_msg = str(get_err)
                    if "Timed out receiving message from renderer" in err_msg or "timeout" in err_msg.lower():
                        self._log_output(f">> 페이지 응답 대기 시간 초과(Timeout): 브라우저 강제 정지 후 DOM 처리 진행\n")
                        try:
                            self.driver.execute_script("window.stop();")
                        except Exception:
                            pass
                    else:
                        self._log_output(f">> 기사 접속 알림: {err_msg[:60]}\n")
                    self._ensure_window_valid()

                real_url = self.driver.current_url
                if "news.google.com" in real_url and target_url != real_url and "news.google.com" not in target_url:
                    real_url = target_url

                # 기사 제목 및 본문(원문) 텍스트 추출
                try:
                    page_title = self.driver.title or ""
                except Exception:
                    page_title = ""

                try:
                    h1_elem = self.driver.find_element(By.TAG_NAME, "h1")
                    headline = h1_elem.text or ""
                except Exception:
                    headline = ""

                try:
                    body_elem = self.driver.find_element(By.CSS_SELECTOR, ".ue-c-article__body, .c-detail__body, article, main, body")
                    body_text = body_elem.text or ""
                except Exception:
                    body_text = ""

                # 키워드 부분 일치 검사 (단일 기사 탭이 아닐 경우)
                if "단일 기사" not in current_tab and match_tokens:
                    is_matched, in_title, in_body = self._check_article_content_match(
                        page_title, headline, body_text, match_tokens, match_mode
                    )

                    if not is_matched:
                        self._log_output(f">> [일치 없음] 기사 제목이나 본문에 키워드가 포함되어 있지 않아 건너뜁니다.\n")
                        continue

                    self._log_output(f">> [매칭 성공!] 기사에서 검색 키워드가 감지되었습니다.\n"
                                     f"   • 제목 감지: {', '.join(in_title) if in_title else '없음'}\n"
                                     f"   • 원문 본문 감지: {', '.join(in_body) if in_body else '없음'}\n"
                                     f"   -> 해당 기사의 해외 팬 댓글 수집을 시작합니다!\n")

                crawled_count += 1

                # 1순위: 언론사별 전용 고속 API/JSON 추출기 시도 (DOM 렌더링/iframe 미로드 완전 우회)
                api_comments = []
                if "marca.com" in real_url:
                    self._log_output(f">> [Marca 전용] 공식 댓글 서비스 API(ueComments) 전체 페이징 조회 시작 (목표: {'전체 끝까지' if max_comments_per_article > 1000 else f'{max_comments_per_article}개'})...\n")
                    api_comments = self._extract_marca_comments_api(real_url, max_comments=max_comments_per_article)
                elif "as.com" in real_url:
                    self._log_output(">> [AS.com 전용] 공식 Disqus 댓글 스레드 직접 조회 시도...\n")
                    api_comments = self._extract_as_comments_api(real_url)
                elif "footmercato.net" in real_url:
                    self._log_output(">> [Foot Mercato 전용] 프랑스 Disqus 댓글 스레드 직접 조회 시도...\n")
                    api_comments = self._extract_footmercato_comments(real_url)
                elif "dailymail.co.uk" in real_url:
                    self._log_output(f">> [Daily Mail 전용] 영국 reader-comments API 전체 페이징 조회 시작 (목표: {'전체 끝까지' if max_comments_per_article > 1000 else f'{max_comments_per_article}개'})...\n")
                    api_comments = self._extract_dailymail_comments(real_url, max_comments=max_comments_per_article)
                elif "yahoo.co.jp" in real_url:
                    self._log_output(">> [Yahoo Japan 전용] 일본 포털 댓글 임베드 데이터 파싱 시도...\n")
                    api_comments = self._extract_yahoo_japan_comments(real_url)
                elif "hupu.com" in real_url or "dongqiudi.com" in real_url:
                    self._log_output(">> [중국 축구 포럼 전용] Hupu/동치우디 댓글 스레드 파싱 시도...\n")
                    api_comments = self._extract_hupu_comments(real_url)

                if api_comments:
                    self._log_output(f">> [성공] API를 통해 댓글 {len(api_comments)}건을 즉시 확보했습니다!\n")
                    added = 0
                    for c_item in api_comments:
                        raw_text = c_item["text"]
                        user = c_item.get("user", "팬")
                        date_str = c_item.get("date", "")
                        if raw_text in [c['text'] for c in self.collected_comments]:
                            continue
                        added += 1
                        item_data = {
                            "index": len(self.collected_comments) + 1,
                            "url": real_url,
                            "text": f"[{user}{(' ('+date_str+')') if date_str else ''}] {raw_text}"
                        }
                        self.collected_comments.append(item_data)
                        self._set_count(len(self.collected_comments))
                        display_block = (
                            f"[{item_data['index']}] 해외 팬 반응 (출처: {real_url})\n"
                            f"{item_data['text']}\n"
                            f"--------------------------------------------------------------------------------\n"
                        )
                        self._log_output(display_block)
                    self._log_output(f">> 이번 기사에서 유효 댓글 {added}건 추출 완료.\n")
                    time.sleep(1.5)
                    continue

                # 2순위: API로 추출되지 않았거나 지원되지 않는 언론사의 경우 브라우저 DOM/iframe 크롤링
                self._log_output(">> 브라우저 DOM 및 동적 댓글 iframe 탐색을 진행합니다.\n")

                # 쿠키/GDPR 동의 팝업 닫기
                self._handle_cookie_consent()

                # 댓글 펼치기 버튼 클릭 시도 (Marca/AS 공통)
                self._trigger_open_comments_button()

                # 댓글 로딩을 위한 부드러운 스크롤
                self._smooth_scroll_to_bottom(steps=5, delay=0.7)

                # 언론사별 셀렉터 자동 판별
                if "as.com" in real_url:
                    iframe_sel = "iframe[src*='disqus.com/embed/comments'], iframe[id*='dsq-app'], iframe[title*='Disqus'], iframe[id*='c-comments'], iframe[id*='coral'], iframe[title*='comentarios'], iframe[src*='coral'], iframe[id*='comments']"
                    comment_sel = ".post-message, .post-message p, [data-role='post-content'], .c-comments__body, .coral-comment-content, div[class*='comment-body'], [data-testid='comment-content']"
                else:
                    iframe_sel = "iframe[id*='ue-comments-iframe'], iframe[src*='coral'], iframe[title*='comentarios'], iframe[id*='coral'], iframe[id*='comments']"
                    comment_sel = ".ue-c-article__comment-content, .coral-comment-content, [data-testid='comment-content'], div[class*='comment-body']"

                # 단일 기사 탭에서 직접 입력한 사용자 지정값 우선 적용
                if "단일 기사" in current_tab:
                    custom_iframe = self.entry_iframe.get().strip()
                    custom_comment = self.entry_comment_css.get().strip()
                    if custom_iframe:
                        iframe_sel = custom_iframe
                    if custom_comment:
                        comment_sel = custom_comment

                # iframe 진입 및 댓글 추출 (iframe 실패 시 메인 본문 댓글도 함께 파싱)
                self._switch_to_comment_iframe(iframe_sel)
                self._extract_comments(comment_sel, article_url=real_url, max_comments=max_comments_per_article)
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

        # Disqus 또는 댓글 iframe이 비동기로 로드될 수 있으므로 최대 8초간 폴링 대기
        selectors = [s.strip() for s in iframe_selector_str.split(",") if s.strip()]
        for attempt in range(4):
            for sel in selectors:
                try:
                    elems = self.driver.find_elements(By.CSS_SELECTOR, sel)
                    if elems:
                        iframe_element = elems[0]
                        self.driver.switch_to.frame(iframe_element)
                        self._log_output(f">> [성공] 댓글 iframe 진입 완료: {sel}\n")
                        time.sleep(2)
                        return True
                except Exception:
                    continue
            time.sleep(1.2)

        # 전체 iframe 목록을 검사하여 src나 title, id에 disqus 또는 comment가 포함된 프레임이 있는지 동적 탐색
        try:
            all_iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            for idx, ifr in enumerate(all_iframes):
                try:
                    src = (ifr.get_attribute("src") or "").lower()
                    title = (ifr.get_attribute("title") or "").lower()
                    ifr_id = (ifr.get_attribute("id") or "").lower()
                    if any(k in src or k in title or k in ifr_id for k in ["disqus", "coral", "comment", "comentario"]):
                        self.driver.switch_to.frame(ifr)
                        self._log_output(f">> [자동 감지] 댓글 iframe 탐지 및 전환 성공 (src: {src[:50]})\n")
                        time.sleep(2)
                        return True
                except Exception:
                    continue
        except Exception:
            pass

        self._log_output(">> 지정된 iframe이 없거나 메인 페이지 DOM에 댓글이 직접 배치되어 있습니다.\n")
        return False

    def _extract_comments(self, comment_selector_str, article_url="", max_comments=5000):
        """
        지정된 CSS 셀렉터로부터 댓글을 파싱하며, '더보기(Load More)' 버튼 클릭 및 스크롤을 반복하여
        기사에 달린 수백 개의 전체 댓글을 끝까지 확장하여 수집합니다.
        """
        self._set_status("댓글 로딩 및 전체 확장 중...")
        selectors = [s.strip() for s in comment_selector_str.split(",") if s.strip()]

        fallback_selectors = [
            ".post-message",
            ".post-message p",
            "[data-role='post-content']",
            ".comment__text",
            "p[class*='comment']",
            "div[class*='comment__text']",
            ".coral-comment-content",
            "div[data-testid='comment-content']",
            ".ue-c-article__comment-content",
            ".c-comments__body",
            ".post-content",
            ".comment-text"
        ]
        all_candidate_selectors = selectors + fallback_selectors

        # 1. 댓글 더보기(Load More) 반복 클릭 및 동적 스크롤 확장 루프
        load_more_selectors = [
            "button[data-action='more-posts']",
            ".load-more__button",
            "button[class*='load-more']",
            "button[class*='more-comments']",
            ".load-more a",
            "button[data-testid='comments-loadMore-button']",
            "button[id*='loadMore']",
            "button[data-testid='load-more-btn']",
            ".ue-c-article__comments-button-more",
            ".c-comments__more button",
            "button[aria-label*='more']",
            "button[aria-label*='cargar']",
            "button[aria-label*='Mehr']"
        ]

        self._log_output(f">> 전체 댓글 확장을 시작합니다 (목표: {'전체 끝까지' if max_comments > 1000 else f'최대 {max_comments}개'})...\n")

        last_found_count = 0
        no_growth_count = 0
        max_expand_rounds = 40 if max_comments > 1000 else min(30, max_comments // 10 + 3)

        for round_idx in range(max_expand_rounds):
            if not self.is_crawling:
                break

            # 현재 로드된 댓글 수 확인
            cur_elements = []
            for sel in all_candidate_selectors:
                try:
                    elems = self.driver.find_elements(By.CSS_SELECTOR, sel)
                    if elems:
                        cur_elements = elems
                        break
                except Exception:
                    continue

            cur_cnt = len(cur_elements)
            if cur_cnt >= max_comments:
                self._log_output(f">> 목표 댓글 수({max_comments}개)에 도달하여 확장을 마칩니다.\n")
                break

            # '더보기' 버튼 탐색 및 클릭
            clicked = False
            for b_sel in load_more_selectors:
                try:
                    btns = self.driver.find_elements(By.CSS_SELECTOR, b_sel)
                    for b in btns:
                        if b.is_displayed():
                            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", b)
                            time.sleep(0.3)
                            self.driver.execute_script("arguments[0].click();", b)
                            clicked = True
                            time.sleep(1.2)
                            break
                    if clicked:
                        break
                except Exception:
                    continue

            # 텍스트 기반 더보기 버튼 탐색 (Cargar más, Load more, 더보기 등)
            if not clicked:
                try:
                    more_candidates = self.driver.find_elements(By.XPATH, "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'more') or contains(., 'cargar') or contains(., 'ver más') or contains(., 'mehr') or contains(., '더보기') or contains(., '더 보기') or contains(., 'もっと見る') or contains(., '展开')] | //a[contains(., 'cargar') or contains(., 'Load more') or contains(., 'Ver más')]")
                    for b in more_candidates:
                        if b.is_displayed():
                            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", b)
                            time.sleep(0.3)
                            self.driver.execute_script("arguments[0].click();", b)
                            clicked = True
                            time.sleep(1.2)
                            break
                except Exception:
                    pass

            # 버튼이 없으면 하단 스크롤을 통해 무한 스크롤 트리거
            if not clicked:
                try:
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);\n")
                    time.sleep(1.0)
                except Exception:
                    pass

            # 확장 후 댓글 개수 변동 확인
            new_elements = []
            for sel in all_candidate_selectors:
                try:
                    elems = self.driver.find_elements(By.CSS_SELECTOR, sel)
                    if elems:
                        new_elements = elems
                        break
                except Exception:
                    continue

            new_cnt = len(new_elements)
            if new_cnt > last_found_count:
                if round_idx > 0 and (round_idx % 2 == 0 or new_cnt >= max_comments):
                    self._log_output(f">> [댓글 확장 {round_idx+1}단계] 현재 {new_cnt}개 댓글 로드됨...\n")
                last_found_count = new_cnt
                no_growth_count = 0
            else:
                no_growth_count += 1
                if no_growth_count >= 3:
                    # 3회 연속 새로운 댓글이 로드되지 않으면 기사의 전체 댓글 끝에 도달한 것으로 판단
                    break

        # 2. 최종 댓글 요소 획득
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

        if not found_elements:
            for fb in fallback_selectors:
                try:
                    elems = self.driver.find_elements(By.CSS_SELECTOR, fb)
                    if elems:
                        found_elements = elems
                        self._log_output(f">> 대체 셀렉터로 발견 ({fb}): {len(elems)}개\n")
                        break
                except Exception:
                    continue

        # 만약 iframe 내부에서 찾지 못했다면 메인 DOM으로 복귀하여 재탐색
        if not found_elements:
            try:
                self.driver.switch_to.default_content()
                for sel in selectors + fallback_selectors:
                    elems = self.driver.find_elements(By.CSS_SELECTOR, sel)
                    if elems:
                        found_elements = elems
                        self._log_output(f">> [메인 DOM] 댓글 요소 {len(elems)}개 발견 ({sel})\n")
                        break
            except Exception:
                pass

        if not found_elements:
            self._log_output(">> 이 기사에는 등록된 댓글이 없거나 아직 작성되지 않았습니다.\n")
            return

        # 필터링 및 출력
        banned_phrases = ["cargar más", "responder", "reportar", "compartir", "iniciar sesión", "ver más comentarios"]
        count = 0

        for elem in found_elements:
            if not self.is_crawling or count >= max_comments:
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

