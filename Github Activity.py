# github_activity.py
# A professional, multi-threaded GitHub Activity Viewer.
# Features: Non-blocking UI, caching, API limit display, and more.

import sys
import os
import time
import webbrowser
from typing import Dict, Any, List, Tuple
from io import BytesIO

# Force qtawesome to use PyQt6 for icon rendering
os.environ['QT_API'] = 'pyqt6'

import requests
import qtawesome as qta
from PyQt6.QtCore import (
    Qt, QObject, QRunnable, pyqtSignal, pyqtSlot, QThreadPool, QTimer,
    QPropertyAnimation, QEasingCurve
)
from PyQt6.QtGui import (
    QPixmap, QColor, QFont, QPainter, QBrush, QAction, QPainterPath
)
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QAbstractItemView, QMessageBox, QMenu, QStackedWidget
)

# --- Configuration ---
GITHUB_API_URL = "https://api.github.com"
CACHE_DURATION_SECONDS = 300  # 5 minutes
WINDOW_TITLE = "GitHub Activity Viewer"
USER_AGENT = "GitHub-Activity-Viewer-V2"

# --- Theming and Icons ---
EVENT_ICONS = {
    'PushEvent': 'fa5s.arrow-alt-circle-up', 'IssuesEvent': 'fa5s.exclamation-circle',
    'IssueCommentEvent': 'fa5.comment-dots', 'PullRequestEvent': 'fa5s.code-branch',
    'WatchEvent': 'fa5s.star', 'ForkEvent': 'fa5s.code-branch',
    'CreateEvent': 'fa5s.plus-circle', 'DeleteEvent': 'fa5s.trash-alt',
    'PublicEvent': 'fa5s.globe', 'ReleaseEvent': 'fa5s.tag',
    'default': 'fa5s.question-circle',
}

THEMES = {
    'light': {
        'bg': '#f6f8fa', 'panel_bg': '#ffffff', 'text': '#24292f',
        'subtle_text': '#57606a', 'accent': '#238636', 'accent_text': '#ffffff',
        'border': '#d0d7de', 'icon': 'fa5s.moon', 'icon_color': '#24292f'
    },
    'dark': {
        'bg': '#0d1117', 'panel_bg': '#161b22', 'text': '#c9d1d9',
        'subtle_text': '#8b949e', 'accent': '#2ea043', 'accent_text': '#ffffff',
        'border': '#30363d', 'icon': 'fa5s.sun', 'icon_color': '#c9d1d9'
    }
}

# --- Worker Signals ---
class WorkerSignals(QObject):
    """Defines signals available from a running worker thread."""
    user_data = pyqtSignal(dict, dict)  # user info, rate limits
    events_data = pyqtSignal(list)
    avatar_data = pyqtSignal(QPixmap)
    error = pyqtSignal(str, str)

# --- Network Worker ---
class NetworkWorker(QRunnable):
    """Worker thread for fetching user data and events from GitHub."""
    def __init__(self, username: str, cache: dict):
        super().__init__()
        self.signals = WorkerSignals()
        self.username = username
        self.cache = cache

    @pyqtSlot()
    def run(self):
        try:
            cached = self.cache.get(self.username)
            if cached and time.time() - cached['timestamp'] < CACHE_DURATION_SECONDS:
                user_info, events, rate_limits = (
                    cached['data']['user'], cached['data']['events'], cached['data']['rates']
                )
            else:
                headers = {'User-Agent': USER_AGENT}
                user_res = requests.get(f"{GITHUB_API_URL}/users/{self.username}", headers=headers)
                rate_limit_res = requests.get(f"{GITHUB_API_URL}/rate_limit", headers=headers)
                rate_limits = rate_limit_res.json()

                if user_res.status_code != 200:
                    raise ValueError(f"User '{self.username}' not found (status {user_res.status_code}).")

                user_info = user_res.json()
                events_res = requests.get(user_info['events_url'].replace('{/privacy}', ''), headers=headers)
                events = events_res.json()

                self.cache[self.username] = {
                    'timestamp': time.time(),
                    'data': {'user': user_info, 'events': events, 'rates': rate_limits}
                }

            self.signals.user_data.emit(user_info, rate_limits)
            self.signals.events_data.emit(events)

            if avatar_url := user_info.get('avatar_url'):
                avatar_res = requests.get(avatar_url, headers=headers)
                avatar_res.raise_for_status()
                pixmap = QPixmap()
                pixmap.loadFromData(avatar_res.content)
                self.signals.avatar_data.emit(pixmap)

        except requests.exceptions.RequestException as e:
            self.signals.error.emit("Network Error", f"Could not connect to GitHub API: {e}")
        except ValueError as e:
            self.signals.error.emit("Not Found", str(e))
        except Exception as e:
            self.signals.error.emit("An Error Occurred", str(e))

# --- UI Components ---
class AvatarLabel(QLabel):
    """A QLabel that displays a pixmap in a circle."""
    def __init__(self, size=48):
        super().__init__()
        self.setFixedSize(size, size)
        self.pixmap = None

    def set_pixmap(self, pixmap: QPixmap):
        self.pixmap = pixmap.scaled(
            self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation
        )
        self.update()

    def paintEvent(self, event):
        if not self.pixmap:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addEllipse(0, 0, self.width(), self.height())
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, self.pixmap)

class GitHubActivityApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(WINDOW_TITLE)
        self.setMinimumSize(900, 700)
        self.theme = 'dark'
        self.thread_pool = QThreadPool()
        self.cache = {}
        self._build_ui()
        self._set_theme()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        top_bar = self._create_top_bar()
        self.user_frame = self._create_user_panel()
        self.results_stack = QStackedWidget()
        self.table = self._create_table()
        self.loading_widget = self._create_loading_widget()
        footer_layout = self._create_footer()

        self.results_stack.addWidget(self.table)
        self.results_stack.addWidget(self.loading_widget)

        main_layout.addLayout(top_bar)
        main_layout.addWidget(self.user_frame)
        main_layout.addWidget(self.results_stack)
        main_layout.addLayout(footer_layout)

    def _create_top_bar(self):
        layout = QHBoxLayout()
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Enter GitHub Username")
        self.username_edit.returnPressed.connect(self.start_fetch)
        layout.addWidget(self.username_edit)

        self.show_btn = QPushButton("Show Activity")
        self.show_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.show_btn.clicked.connect(self.start_fetch)
        layout.addWidget(self.show_btn)
        
        self.theme_btn = QPushButton()
        self.theme_btn.setFixedSize(36, 36)
        self.theme_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.theme_btn.clicked.connect(self.toggle_theme)
        layout.addWidget(self.theme_btn)
        
        layout.addStretch()

        return layout

    def _create_user_panel(self):
        frame = QFrame()
        frame.setObjectName("userFrame")
        frame.hide()
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(15)

        self.avatar_label = AvatarLabel(size=48)
        layout.addWidget(self.avatar_label)

        self.userinfo_label = QLabel()
        self.userinfo_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        layout.addWidget(self.userinfo_label)

        layout.addStretch()
        return frame

    def _create_loading_widget(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        spinner_icon = qta.IconWidget()
        self.loading_animation = qta.Spin(spinner_icon)
        spinner_icon.setIcon(qta.icon('fa5s.spinner'))
        layout.addWidget(spinner_icon, alignment=Qt.AlignmentFlag.AlignCenter)
        return widget
        
    def _create_table(self):
        table = QTableWidget(0, 4)
        table.setHorizontalHeaderLabels(["", "Type", "Details", "Date"])
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setShowGrid(False)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(48)
        table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        table.customContextMenuRequested.connect(self._show_table_context_menu)
        table.cellDoubleClicked.connect(self._open_event_url)

        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        return table

    def _create_footer(self):
        layout = QHBoxLayout()
        self.summary_label = QLabel()
        self.rate_limit_label = QLabel()
        self.rate_limit_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.summary_label)
        layout.addWidget(self.rate_limit_label)
        return layout

    def _set_theme(self):
        palette = THEMES[self.theme]
        font_main = QFont("Segoe UI", 10)
        self.setFont(font_main)
        
        self.setStyleSheet(f"""
            QWidget {{ background-color: {palette['bg']}; color: {palette['text']}; }}
            QTableWidget {{ 
                background-color: {palette['panel_bg']};
                border: 1px solid {palette['border']}; border-radius: 8px;
            }}
            QHeaderView::section {{
                background-color: {palette['bg']}; color: {palette['subtle_text']};
                padding: 8px; border: none; border-bottom: 1px solid {palette['border']};
            }}
            QTableWidget::item {{ padding-left: 10px; border-bottom: 1px solid {palette['border']}; }}
            QTableWidget::item:selected {{ background-color: {palette['accent']}; color: {palette['accent_text']}; }}
            #userFrame {{
                background-color: {palette['panel_bg']};
                border: 1px solid {palette['border']}; border-radius: 8px;
            }}
            QLineEdit {{
                padding: 8px 12px; border-radius: 8px;
                border: 1px solid {palette['border']}; background-color: {palette['panel_bg']};
            }}
            QLineEdit:focus {{ border: 1px solid {palette['accent']}; }}
        """)
        
        self.theme_btn.setIcon(qta.icon(palette['icon'], color=palette['icon_color']))
        self.theme_btn.setStyleSheet(f"""
            QPushButton {{ background-color: transparent; border: 1px solid {palette['border']}; border-radius: 18px; }}
            QPushButton:hover {{ background-color: {palette['border']}; }}
        """)
        self.show_btn.setStyleSheet(f"""
            QPushButton {{ padding: 8px 16px; border-radius: 8px; border: none;
                         background-color: {palette['accent']}; color: {palette['accent_text']}; }}
        """)
        self.rate_limit_label.setStyleSheet(f"color: {palette['subtle_text']};")
        self.summary_label.setStyleSheet(f"color: {palette['subtle_text']};")
        
        if self.user_frame.isVisible():
            self.start_fetch(force_refresh=True)

    def toggle_theme(self):
        self.theme = 'dark' if self.theme == 'light' else 'light'
        self._set_theme()

    def start_fetch(self, force_refresh=False):
        username = self.username_edit.text().strip()
        if not username:
            self._show_message("Input Required", "Please enter a GitHub username.")
            return

        self.show_btn.setEnabled(False)
        self.user_frame.hide()
        self.summary_label.setText("")
        self.rate_limit_label.setText("")
        self.table.setRowCount(0)
        self.results_stack.setCurrentWidget(self.loading_widget)
        self.loading_animation.start()

        effective_cache = {} if force_refresh else self.cache
        worker = NetworkWorker(username, effective_cache)
        worker.signals.user_data.connect(self.on_user_data)
        worker.signals.events_data.connect(self.on_events_data)
        worker.signals.avatar_data.connect(self.on_avatar_data)
        worker.signals.error.connect(self.on_fetch_error)
        self.thread_pool.start(worker)

    def on_user_data(self, user_info, rate_limits):
        name = user_info.get('name') or user_info.get('login')
        profile_url = user_info.get('html_url', '')
        palette = THEMES[self.theme]
        self.userinfo_label.setText(f"<a href='{profile_url}' style='color:{palette['text']}; text-decoration:none;'>{name}</a>")
        self.userinfo_label.setOpenExternalLinks(True)

        self.user_frame.setWindowOpacity(0)
        self.user_frame.show()
        anim = QPropertyAnimation(self.user_frame, b"windowOpacity")
        anim.setDuration(400)
        anim.setStartValue(0)
        anim.setEndValue(1)
        anim.start()

        core = rate_limits.get('resources', {}).get('core', {})
        self.rate_limit_label.setText(f"API Rate: {core.get('remaining')} / {core.get('limit')}")

    def on_events_data(self, events):
        if isinstance(events, dict) and 'message' in events:
            self.on_fetch_error("API Error", events['message'])
            return
            
        self.table.setRowCount(0)
        palette = THEMES[self.theme]
        for event in events[:50]:
            row_pos = self.table.rowCount()
            self.table.insertRow(row_pos)
            
            summary, url = self._summarize_event(event)
            type_text = event.get('type', 'UnknownEvent').replace('Event', '')
            icon_name = EVENT_ICONS.get(event.get('type'), EVENT_ICONS['default'])
            date_text = event.get('created_at', '').replace('T', ' ').replace('Z', '')

            icon_item = QTableWidgetItem()
            icon_item.setIcon(qta.icon(icon_name, color=palette['subtle_text']))
            
            summary_item = QTableWidgetItem(summary)
            if url:
                summary_item.setData(Qt.ItemDataRole.UserRole, url)
                summary_item.setToolTip(f"Double-click to open in browser: {url}")

            self.table.setItem(row_pos, 0, icon_item)
            self.table.setItem(row_pos, 1, QTableWidgetItem(type_text))
            self.table.setItem(row_pos, 2, summary_item)
            self.table.setItem(row_pos, 3, QTableWidgetItem(date_text))
        
        self.summary_label.setText(f"Showing {self.table.rowCount()} recent events.")
        self.results_stack.setCurrentWidget(self.table)
        self.loading_animation.stop()
        self.show_btn.setEnabled(True)

    def on_avatar_data(self, pixmap):
        self.avatar_label.set_pixmap(pixmap)

    def on_fetch_error(self, title, message):
        self._show_message(title, message, icon=QMessageBox.Icon.Critical)
        self.results_stack.setCurrentWidget(self.table)
        self.loading_animation.stop()
        self.show_btn.setEnabled(True)
        self.rate_limit_label.setText("API Status: Error")

    @staticmethod
    def _summarize_event(event: Dict[str, Any]) -> Tuple[str, str]:
        repo_name = event.get('repo', {}).get('name', 'N/A')
        repo_url = f"https://github.com/{repo_name}"
        payload = event.get('payload', {})
        type_ = event.get('type')
        
        url, summary = repo_url, f"Performed {type_} in {repo_name}"

        if type_ == 'PushEvent':
            summary = f"Pushed {payload.get('size', 0)} commit(s) to {repo_name}"
        elif type_ == 'IssuesEvent':
            issue = payload.get('issue', {})
            url = issue.get('html_url', repo_url)
            summary = f"{payload.get('action','').capitalize()} issue in {repo_name}: '{issue.get('title', 'N/A')}'"
        elif type_ == 'IssueCommentEvent':
            url = payload.get('comment', {}).get('html_url', repo_url)
            summary = f"Commented on an issue in {repo_name}"
        elif type_ == 'PullRequestEvent':
            pr = payload.get('pull_request', {})
            url = pr.get('html_url', repo_url)
            summary = f"{payload.get('action','').capitalize()} PR #{pr.get('number', '')} in {repo_name}"
        elif type_ == 'WatchEvent':
            summary = f"Starred {repo_name}"
        elif type_ == 'ForkEvent':
            forkee = payload.get('forkee', {})
            url = forkee.get('html_url', repo_url)
            summary = f"Forked {repo_name} to {forkee.get('full_name', 'N/A')}"
        elif type_ in ['CreateEvent', 'DeleteEvent']:
            action = 'Created' if type_ == 'CreateEvent' else 'Deleted'
            summary = f"{action} {payload.get('ref_type', 'N/A')} in {repo_name}"
        elif type_ == 'ReleaseEvent':
            release = payload.get('release', {})
            url = release.get('html_url', repo_url)
            summary = f"Published release in {repo_name}"
        
        return summary, url

    def _show_table_context_menu(self, pos):
        item = self.table.itemAt(pos)
        if not item: return

        menu = QMenu(self)
        summary_item = self.table.item(item.row(), 2)
        url = summary_item.data(Qt.ItemDataRole.UserRole)
        palette = THEMES[self.theme]
        
        if url:
            open_action = QAction(qta.icon('fa5s.external-link-alt', color=palette['text']), "Open on GitHub", self)
            open_action.triggered.connect(lambda: webbrowser.open(url))
            menu.addAction(open_action)
            
            copy_url_action = QAction("Copy Link", self)
            copy_url_action.triggered.connect(lambda: QApplication.clipboard().setText(url))
            menu.addAction(copy_url_action)
            menu.addSeparator()

        copy_summary_action = QAction("Copy Summary", self)
        copy_summary_action.triggered.connect(lambda: QApplication.clipboard().setText(summary_item.text()))
        menu.addAction(copy_summary_action)
        menu.exec(self.table.mapToGlobal(pos))
        
    def _open_event_url(self, row, column):
        item = self.table.item(row, 2)
        if item and (url := item.data(Qt.ItemDataRole.UserRole)):
            webbrowser.open(url)

    def _show_message(self, title, text, icon=QMessageBox.Icon.Information):
        box = QMessageBox(self)
        box.setIcon(icon)
        box.setWindowTitle(title)
        box.setText(text)
        box.setStyleSheet("QLabel{font-size: 11pt;} QPushButton{min-width: 80px;}")
        box.exec()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = GitHubActivityApp()
    window.show()
    sys.exit(app.exec())
