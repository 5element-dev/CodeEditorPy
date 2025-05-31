import shutil
import sys
import os
import requests
import webbrowser
import re
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QLabel, QTextBrowser, QMainWindow, QSplitter,
    QPlainTextEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QStatusBar, QAction, QFileDialog, QMessageBox, QTextEdit, QMenu, QInputDialog, QTabWidget, QDialog, QSpinBox,
    QPushButton, QFontComboBox, QFontDialog, QComboBox
)
from PyQt5.QtCore import Qt, QRect, QSize, QTimer, QPoint
from PyQt5.QtGui import (
    QPainter, QColor, QTextFormat, QTextCursor,
    QTextCharFormat, QSyntaxHighlighter, QFont, QMouseEvent, QKeySequence, QTextDocument
)


import re
from PyQt5.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont

class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.highlighting_rules = []

        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#e45649"))
        keyword_format.setFontWeight(QFont.Bold)
        keywords = [
            "and", "as", "assert", "async", "await", "break", "continue",
            "def", "del", "elif", "else", "except", "False", "finally", "for",
            "from", "global", "if", "import", "in", "is", "lambda", "None",
            "nonlocal", "not", "or", "pass", "raise", "return", "True", "try",
            "while", "with", "yield", "class", "def"
        ]
        for kw in keywords:
            pattern = re.compile(r'\b' + kw + r'\b')
            self.highlighting_rules.append((pattern, keyword_format))

        builtin_format = QTextCharFormat()
        builtin_format.setForeground(QColor("#a626a4"))
        builtins = [
            "abs", "all", "any", "bin", "bool", "bytearray", "bytes", "callable",
            "chr", "classmethod", "compile", "complex", "delattr", "dict", "dir",
            "divmod", "enumerate", "eval", "exec", "filter", "float", "format",
            "frozenset", "getattr", "globals", "hasattr", "hash", "help", "hex",
            "id", "input", "int", "isinstance", "issubclass", "iter", "len",
            "list", "locals", "map", "max", "memoryview", "min", "next", "object",
            "oct", "open", "ord", "pow", "property", "range", "repr", "self",
            "reversed", "round", "set", "setattr", "slice", "sorted", "staticmethod",
            "str", "sum", "super", "tuple", "type", "vars", "zip", "__import__"
        ]
        for b in builtins:
            pattern = re.compile(r'\b' + b + r'\b')
            self.highlighting_rules.append((pattern, builtin_format))

        builtin2_format = QTextCharFormat()
        builtin2_format.setForeground(QColor("#e45649"))
        builtins2 = [
            "class", "def"
        ]
        for b in builtins2:
            pattern = re.compile(r'\b' + b + r'\b')
            self.highlighting_rules.append((pattern, builtin2_format))



        self.class_format = QTextCharFormat()
        self.class_format.setForeground(QColor("#c18401"))

        self.class_pattern = re.compile(r'\bclass\s+(\w+)')

        self.function_format = QTextCharFormat()
        self.function_format.setForeground(QColor("#e45649"))

        self.function_pattern = re.compile(r'\bdef\s+(\w+)')

        function_call_format = QTextCharFormat()
        function_call_format.setForeground(QColor("#986801"))
        self.highlighting_rules.append((re.compile(r'\b\w+(?=\s*\()'), function_call_format))

        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#50a14f"))
        self.highlighting_rules.append((re.compile(r'"[^"\\]*(\\.[^"\\]*)*"'), string_format))
        self.highlighting_rules.append((re.compile(r"'[^'\\]*(\\.[^'\\]*)*'"), string_format))

        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#a0a1a7"))
        comment_format.setFontItalic(True)
        self.comment_pattern = re.compile(r'#.*')
        self.comment_format = comment_format

        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#d73a49"))
        self.highlighting_rules.append((re.compile(r'\b[0-9]+(\.[0-9]*)?\b'), number_format))

        operator_format = QTextCharFormat()
        operator_format.setForeground(QColor("#0184bc"))
        self.highlighting_rules.append((re.compile(r'[-+*/%=<>!&|^~]+'), operator_format))

        paren_format = QTextCharFormat()
        paren_format.setForeground(QColor("#383a42"))
        self.highlighting_rules.append((re.compile(r'[()\[\]{}]'), paren_format))

        decorator_format = QTextCharFormat()
        decorator_format.setForeground(QColor("#c18401"))
        self.highlighting_rules.append((re.compile(r'@\w+'), decorator_format))

    def highlightBlock(self, text):
        comment_start = text.find('#')
        if comment_start != -1:
            self.setFormat(comment_start, len(text) - comment_start, self.comment_format)
            text_to_highlight = text[:comment_start]
        else:
            text_to_highlight = text

        for match in self.class_pattern.finditer(text_to_highlight):
            start, end = match.span(1)
            self.setFormat(start, end - start, self.class_format)

        for match in self.function_pattern.finditer(text_to_highlight):
            start, end = match.span(1)
            self.setFormat(start, end - start, self.function_format)

        for pattern, fmt in self.highlighting_rules:
            if pattern.pattern == r'#.*':
                continue
            for match in pattern.finditer(text_to_highlight):
                start, end = match.span()
                self.setFormat(start, end - start, fmt)


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.codeEditor = editor

    def sizeHint(self):
        return QSize(self.codeEditor.lineNumberAreaWidth(), self.codeEditor.height())

    def paintEvent(self, event):
        self.codeEditor.lineNumberAreaPaintEvent(event)


class CodeEditor(QPlainTextEdit):
    def __init__(self):
        super().__init__()
        self.theme = "light"
        self.line_highlight_color = QColor("#e8f2fe")
        self.lineNumberColor = Qt.black
        self.file_path = None
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.lineNumberArea = LineNumberArea(self)
        self.highlighter = PythonHighlighter(self.document())

        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)

        self.updateLineNumberAreaWidth(0)
        self.highlightCurrentLine()
        self.setFont(QFont("MS Shell Dlg 2", 10))
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(' ') * 4)

    def change_font(self, font: QFont):
        self.setFont(font)
        self.updateLineNumberAreaWidth(0)
        self.lineNumberArea.update()
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(' ') * 4)
        self.update()
        self.updateGeometry()

    def lineNumberAreaWidth(self):
        digits = max(1, len(str(self.blockCount())))
        space = 3 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def updateLineNumberAreaWidth(self, _):
        width = self.lineNumberAreaWidth()
        self.setViewportMargins(width, 0, 0, 0)
        self.lineNumberArea.setFixedWidth(width)

    def updateLineNumberArea(self, rect, dy):
        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(0, rect.y(), self.lineNumberArea.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height()))

    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.lineNumberArea)
        if self.theme == "dark":
            painter.fillRect(event.rect(), QColor("#2b2b2b"))  # dark gray
        else:
            painter.fillRect(event.rect(), QColor(230, 230, 230))  # light

        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(blockNumber + 1)
                painter.setPen(self.lineNumberColor)
                painter.drawText(0, top, self.lineNumberArea.width() - 2, self.fontMetrics().height(),
                                 Qt.AlignRight, number)
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            blockNumber += 1

    def highlightCurrentLine(self):
        extraSelections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            lineColor = self.line_highlight_color
            selection.format.setBackground(lineColor)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extraSelections.append(selection)
        self.setExtraSelections(extraSelections)


class FileBrowser(QTextBrowser):
    def __init__(self, editor_callback):
        super().__init__()
        self.editor_callback = editor_callback
        self.setReadOnly(True)
        self.setLineWrapMode(QTextBrowser.NoWrap)
        self.setStyleSheet("""
            QTextBrowser {
                background-color: black;
                color: white;
                font-family: monospace;
            }
            a:hover {
                color: yellow;
            }
        """)
        self.current_dir = os.getcwd()
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.context_menu)
        self.anchor_hovered = ""
        self.display_directory_contents()

    def display_directory_contents(self, filter_text=""):
        self.clear()
        cursor = self.textCursor()
        header = f'> {self.current_dir}\n\n'
        cursor.insertHtml(f'<span style="color:lightgray;">{header}</span><br>')

        parent_dir = os.path.dirname(self.current_dir)
        if parent_dir and parent_dir != self.current_dir:
            self.insert_folder_link(cursor, "..")

        for item in sorted(os.listdir(self.current_dir)):
            if filter_text.lower() not in item.lower():
                continue
            full_path = os.path.join(self.current_dir, item)
            cursor.insertHtml('&nbsp;&nbsp;&nbsp;&nbsp;')
            if os.path.isdir(full_path):
                self.insert_folder_link(cursor, item)
            else:
                self.insert_file_link(cursor, item)

        cursor.movePosition(QTextCursor.Start)

    def insert_folder_link(self, cursor, folder_name):
        cursor.insertHtml(f'\U0001F4C1 ')
        fmt = QTextCharFormat()
        fmt.setForeground(Qt.cyan)
        fmt.setAnchor(True)
        fmt.setAnchorHref(folder_name)
        fmt.setFontUnderline(False)
        cursor.insertText(folder_name + '/', fmt)
        cursor.insertHtml('<br>')

    def insert_file_link(self, cursor, file_name):
        fmt = QTextCharFormat()
        fmt.setForeground(Qt.white)
        fmt.setAnchor(True)
        fmt.setAnchorHref(file_name)
        fmt.setFontUnderline(False)
        cursor.insertText(file_name, fmt)
        cursor.insertHtml('<br>')

    def mouseMoveEvent(self, event: QMouseEvent):
        anchor = self.anchorAt(event.pos())
        self.anchor_hovered = anchor
        self.setCursor(Qt.PointingHandCursor if anchor else Qt.ArrowCursor)
        super().mouseMoveEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        anchor = self.anchorAt(event.pos())
        if anchor:
            full_path = os.path.join(self.current_dir, anchor)
            if os.path.isfile(full_path):
                self.editor_callback(full_path)
            elif os.path.isdir(full_path):
                self.current_dir = full_path
                self.display_directory_contents()
        else:
            super().mouseDoubleClickEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        anchor = self.anchorAt(event.pos())
        if anchor:
            potential_dir = os.path.join(self.current_dir, anchor)
            if anchor == "..":
                self.current_dir = os.path.dirname(self.current_dir)
            elif os.path.isdir(potential_dir):
                self.current_dir = potential_dir
            self.display_directory_contents()
        else:
            super().mouseReleaseEvent(event)

    def context_menu(self, pos: QPoint):
        try:
            anchor = self.anchorAt(pos)
            if not anchor:
                return

            full_path = os.path.join(self.current_dir, anchor)
            if not os.path.exists(full_path):
                return

            menu = QMenu(self)
            if os.path.isfile(full_path):
                open_action = menu.addAction("Open")
                delete_action = menu.addAction("Delete")
                rename_action = menu.addAction("Edit name")

                action = menu.exec_(self.mapToGlobal(pos))
                if action == open_action:
                    self.editor_callback(full_path)

                elif action == delete_action:
                    confirm = QMessageBox.question(
                        self, "Delete File",
                        f"Are you sure you want to delete '{anchor}'?",
                        QMessageBox.Yes | QMessageBox.No
                    )
                    if confirm == QMessageBox.Yes:
                        os.remove(full_path)
                        self.display_directory_contents()

                elif action == rename_action:
                    new_name, ok = QInputDialog.getText(self, "Rename File", "Enter new name:", text=anchor)
                    if ok and new_name and new_name != anchor:
                        new_path = os.path.join(self.current_dir, new_name)
                        try:
                            os.rename(full_path, new_path)
                            self.display_directory_contents()

                            if hasattr(self.editor_callback, "__self__"):
                                main_window = self.editor_callback.__self__
                                if hasattr(main_window, "current_file") and main_window.current_file == full_path:
                                    main_window.current_file = new_path
                                    main_window.version_label.setText(
                                        f"Renamed: {os.path.basename(new_path)} @ {main_window.timestamp()}"
                                    )
                        except Exception as e:
                            QMessageBox.warning(self, "Rename Failed", f"Could not rename file:\n{e}")

        except Exception as e:
            print(f"[context_menu ERROR]: {e}")


class TodoPanel(QWidget):
    def __init__(self, get_editor_func):
        super().__init__()
        self.get_editor = get_editor_func
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Type", "Description", "Line"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.layout.addWidget(self.table)

        self.keywords = ["TODO", "FIXME", "HACK", "NOTE", "OPTIMIZE"]

        self.update_comments()

        editor = self.get_editor()
        if editor:
            editor.textChanged.connect(self.update_comments)

        self.table.cellClicked.connect(self.jump_to_line)

    def update_comments(self):
        editor = self.get_editor()
        if not editor:
            return

        self.table.setRowCount(0)
        lines = editor.toPlainText().split("\n")
        for line_number, line_text in enumerate(lines):
            for keyword in self.keywords:
                if f"// {keyword}:" in line_text:
                    content = line_text.split(f"// {keyword}:")[-1].strip()
                    row = self.table.rowCount()
                    self.table.insertRow(row)
                    self.table.setItem(row, 0, QTableWidgetItem(keyword))
                    self.table.setItem(row, 1, QTableWidgetItem(content))
                    self.table.setItem(row, 2, QTableWidgetItem(str(line_number + 1)))

    def jump_to_line(self, row, column):
        editor = self.get_editor()
        if not editor:
            return

        line = int(self.table.item(row, 2).text()) - 1
        cursor = editor.textCursor()
        cursor.movePosition(QTextCursor.Start)
        cursor.movePosition(QTextCursor.Down, QTextCursor.MoveAnchor, line)
        editor.setTextCursor(cursor)
        editor.setFocus()



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CodeEditor")
        self.setGeometry(100, 100, 1000, 600)

        self.current_theme = "Light"

        self.current_file_map = {}

        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")

        new_action = QAction("New File", self)
        new_action.setShortcut(QKeySequence.New)
        new_action.triggered.connect(self.new_file)

        open_action = QAction("Open", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self.open_file)
        save_action = QAction("Save", self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.triggered.connect(self.save_file)
        save_as_action = QAction("Save as...", self)
        save_as_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        save_as_action.triggered.connect(self.save_file_as)
        file_menu.addAction(new_action)
        file_menu.addAction(open_action)
        file_menu.addAction(save_action)
        file_menu.addAction(save_as_action)

        edit_menu = menu_bar.addMenu("Edit")

        undo_action = QAction("Undo", self)
        undo_action.setShortcut(QKeySequence.Undo)
        undo_action.triggered.connect(lambda: self.current_editor() and self.current_editor().undo())
        edit_menu.addAction(undo_action)

        redo_action = QAction("Redo", self)
        redo_action.setShortcut(QKeySequence.Redo)
        redo_action.triggered.connect(lambda: self.current_editor() and self.current_editor().redo())
        edit_menu.addAction(redo_action)

        edit_menu.addSeparator()

        cut_action = QAction("Cut", self)
        cut_action.setShortcut(QKeySequence.Cut)
        cut_action.triggered.connect(lambda: self.current_editor() and self.current_editor().cut())
        edit_menu.addAction(cut_action)

        copy_action = QAction("Copy", self)
        copy_action.setShortcut(QKeySequence.Copy)
        copy_action.triggered.connect(lambda: self.current_editor() and self.current_editor().copy())
        edit_menu.addAction(copy_action)

        paste_action = QAction("Paste", self)
        paste_action.setShortcut(QKeySequence.Paste)
        paste_action.triggered.connect(lambda: self.current_editor() and self.current_editor().paste())
        edit_menu.addAction(paste_action)

        edit_menu.addSeparator()

        find_action = QAction("Find...", self)
        find_action.setShortcut(QKeySequence.Find)
        find_action.triggered.connect(self.find_in_editor)
        edit_menu.addAction(find_action)

        find_next_action = QAction("Find Next", self)
        find_next_action.setShortcut(QKeySequence("F3"))
        find_next_action.triggered.connect(self.find_next_in_editor)
        edit_menu.addAction(find_next_action)

        find_prev_action = QAction("Find Previous", self)
        find_prev_action.setShortcut(QKeySequence("Shift+F3"))
        find_prev_action.triggered.connect(self.find_prev_in_editor)
        edit_menu.addAction(find_prev_action)

        replace_action = QAction("Replace...", self)
        replace_action.setShortcut(QKeySequence("Ctrl+H"))
        replace_action.triggered.connect(self.replace_in_editor)
        edit_menu.addAction(replace_action)

        edit_menu.addSeparator()

        goto_line_action = QAction("Go to Line...", self)
        goto_line_action.setShortcut(QKeySequence("Ctrl+G"))
        goto_line_action.triggered.connect(self.goto_line_dialog)
        edit_menu.addAction(goto_line_action)

        select_all_action = QAction("Select All", self)
        select_all_action.setShortcut(QKeySequence.SelectAll)
        select_all_action.triggered.connect(lambda: self.current_editor() and self.current_editor().selectAll())
        edit_menu.addAction(select_all_action)


        view_menu = self.menuBar().addMenu("View")

        self.toggle_line_numbers_action = QAction("Toggle Line Numbers", self, checkable=True)
        self.toggle_line_numbers_action.setChecked(True)
        self.toggle_line_numbers_action.triggered.connect(self.toggle_line_numbers)
        view_menu.addAction(self.toggle_line_numbers_action)

        self.toggle_whitespace_action = QAction("Toggle Whitespace Characters", self, checkable=True)
        self.toggle_whitespace_action.setChecked(False)
        self.toggle_whitespace_action.triggered.connect(self.toggle_whitespace)
        view_menu.addAction(self.toggle_whitespace_action)

        self.toggle_word_wrap_action = QAction("Toggle Word Wrap", self, checkable=True)
        self.toggle_word_wrap_action.setChecked(False)
        self.toggle_word_wrap_action.triggered.connect(self.toggle_word_wrap)
        view_menu.addAction(self.toggle_word_wrap_action)

        zoom_in_action = QAction("Zoom In", self)
        zoom_in_action.setShortcuts([QKeySequence("Ctrl++"), QKeySequence("Ctrl+=")])
        zoom_in_action.triggered.connect(self.zoom_in)
        view_menu.addAction(zoom_in_action)

        zoom_out_action = QAction("Zoom Out", self)
        zoom_out_action.setShortcut("Ctrl+-")
        zoom_out_action.triggered.connect(self.zoom_out)
        view_menu.addAction(zoom_out_action)

        self.toggle_sidebar_action = QAction("Toggle Sidebar / File Explorer", self, checkable=True)
        self.toggle_sidebar_action.setChecked(True)
        self.toggle_sidebar_action.triggered.connect(self.toggle_sidebar)
        view_menu.addAction(self.toggle_sidebar_action)

        self.toggle_todo_panel_action = QAction("Toggle TODO Panel", self, checkable=True)
        self.toggle_todo_panel_action.setChecked(True)
        self.toggle_todo_panel_action.triggered.connect(self.toggle_todo_panel)
        view_menu.addAction(self.toggle_todo_panel_action)

        help_menu = menu_bar.addMenu("Help")

        doc_action = QAction("Documentation", self)
        doc_action.triggered.connect(self.open_documentation)

        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about_dialog)

        check_updates_action = QAction("Check for Updates", self)
        check_updates_action.triggered.connect(self.check_for_updates)

        report_issue_action = QAction("Report Issue", self)
        report_issue_action.triggered.connect(self.report_issue)

        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.open_settings)

        help_menu.addAction(doc_action)
        help_menu.addAction(about_action)
        help_menu.addAction(check_updates_action)
        help_menu.addAction(report_issue_action)
        help_menu.addSeparator()
        help_menu.addAction(settings_action)

        main_splitter = QSplitter(Qt.Horizontal)

        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        main_splitter.addWidget(self.tab_widget)
        main_splitter.setStretchFactor(0, 8)
        main_splitter.setStretchFactor(1, 2)

        right_splitter = QSplitter(Qt.Vertical)
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_widget.setLayout(right_layout)
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search files/folders...")
        right_layout.addWidget(self.search_bar)
        self.file_browser = FileBrowser(self.open_file_direct)
        right_layout.addWidget(self.file_browser, stretch=1)
        right_splitter.addWidget(right_widget)

        self.todo_panel = TodoPanel(self.current_editor)
        right_splitter.addWidget(self.todo_panel)
        right_splitter.setStretchFactor(0, 3)
        right_splitter.setStretchFactor(1, 3)
        main_splitter.addWidget(right_splitter)
        self.setCentralWidget(main_splitter)

        self.version_label = QLabel("@v0.2")
        self.version_label.setStyleSheet("color: red;")
        status_bar = QStatusBar()
        status_bar.addPermanentWidget(self.version_label, 1)
        self.setStatusBar(status_bar)
        self.apply_theme(self.current_theme)
        self.search_bar.textChanged.connect(self.on_search_text_changed)

    def apply_theme(self, theme):
        if theme == "Dark":
            dark_stylesheet = """
                QWidget { background-color: #2b2b2b; color: #f0f0f0; }
                QPlainTextEdit, QTextBrowser { background-color: #1e1e1e; color: #ffffff; }
                QLineEdit, QSpinBox, QComboBox, QPushButton {
                    background-color: #3c3c3c; color: white;
                }
                QLineEdit::placeholder {
                    color: white;
                }
                QMenuBar, QMenu, QToolTip {
                    background-color: #2b2b2b; color: #ffffff;
                }
                QTabWidget::pane { border: 1px solid #444444; }
                QHeaderView::section { background-color: #444444; color: white; }
            """
            self.setStyleSheet(dark_stylesheet)

            for i in range(self.tab_widget.count()):
                editor = self.tab_widget.widget(i)
                if isinstance(editor, CodeEditor):
                    editor.theme = "dark"
                    editor.line_highlight_color = QColor("#333c4c")
                    editor.lineNumberArea.setStyleSheet("background-color: #2b2b2b;")
                    editor.lineNumberColor = Qt.lightGray
                    editor.highlightCurrentLine()
                    editor.lineNumberArea.update()

            self.search_bar.setStyleSheet("""
                QLineEdit {
                    color: white;
                    background-color: #3c3c3c;
                }
            """)


        else:
            self.setStyleSheet("")
            for i in range(self.tab_widget.count()):
                editor = self.tab_widget.widget(i)
                if isinstance(editor, CodeEditor):
                    editor.theme = "light"
                    editor.line_highlight_color = QColor("#e8f2fe")
                    editor.lineNumberColor = Qt.black
                    editor.lineNumberArea.setStyleSheet("")
                    editor.highlightCurrentLine()
                    editor.lineNumberArea.update()

            self.search_bar.setStyleSheet("")

    def open_settings(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Settings")

        layout = QVBoxLayout()

        font_label = QLabel("Choose Font:")
        font_combo = QFontComboBox()
        layout.addWidget(font_label)
        layout.addWidget(font_combo)

        size_label = QLabel("Choose Font Size:")
        size_spin = QSpinBox()
        size_spin.setRange(6, 72)
        size_spin.setValue(getattr(self, "current_font_size", 10))
        layout.addWidget(size_label)
        layout.addWidget(size_spin)

        theme_label = QLabel("Choose Theme:")
        theme_combo = QComboBox()
        theme_combo.addItems(["Light", "Dark"])
        layout.addWidget(theme_label)
        layout.addWidget(theme_combo)

        if hasattr(self, "current_font_family"):
            font_combo.setCurrentFont(QFont(self.current_font_family))
        if hasattr(self, "current_theme"):
            index = theme_combo.findText(self.current_theme)
            if index != -1:
                theme_combo.setCurrentIndex(index)

        btn_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        btn_layout.addWidget(ok_button)
        btn_layout.addWidget(cancel_button)
        layout.addLayout(btn_layout)

        dialog.setLayout(layout)

        def apply_and_close():
            selected_font = font_combo.currentFont()
            selected_size = size_spin.value()
            selected_theme = theme_combo.currentText()

            self.current_font_family = selected_font.family()
            self.current_font_size = selected_size
            self.current_theme = selected_theme

            font = selected_font
            font.setPointSize(selected_size)

            editor = self.current_editor()
            if editor:
                editor.change_font(font)

            self.apply_theme(selected_theme)

            dialog.accept()

        ok_button.clicked.connect(apply_and_close)
        cancel_button.clicked.connect(dialog.reject)

        dialog.exec_()

    def open_documentation(self):
        webbrowser.open("https://github.com/5element-dev/CodeEditorPy/blob/main/README.md")

    def show_about_dialog(self):
        QMessageBox.about(self, "About", "CodeEditor v0.2\nAuthor: 5element-dev\n© 2025")

    def check_for_updates(self):
        try:
            url = "https://raw.githubusercontent.com/5element-dev/CodeEditorPy/main/.version"

            response = requests.get(url)
            response.raise_for_status()
            remote_version = response.text.strip()

            local_version = None
            local_version_path = ".version"
            if os.path.exists(local_version_path):
                with open(local_version_path, "r") as f:
                    local_version = f.read().strip()

            if local_version is None:
                QMessageBox.information(self, "Check for Updates",
                                        f"No local version file found.\nRemote version is {remote_version}.")
                return

            if remote_version == local_version:
                QMessageBox.information(self, "Check for Updates", f"You have the latest version: {local_version}")
            else:
                QMessageBox.information(self, "Check for Updates",
                                        f"Update available!\nLocal version: {local_version}\nRemote version: {remote_version}")

        except requests.RequestException as e:
            QMessageBox.warning(self, "Check for Updates", f"Failed to check for updates:\n{e}")

    def report_issue(self):
        webbrowser.open("https://github.com/5element-dev/CodeEditorPy/issues/new")


    def toggle_line_numbers(self, checked):
        editor = self.current_editor()
        if editor and hasattr(editor, 'lineNumberArea'):
            editor.lineNumberArea.setVisible(checked)
            editor.updateLineNumberAreaWidth(0)

    def toggle_whitespace(self, checked):
        editor = self.current_editor()
        if editor:
            editor.setWhitespaceVisibility(checked)

    def toggle_word_wrap(self, checked):
        editor = self.current_editor()
        if editor:
            if checked:
                editor.setLineWrapMode(QPlainTextEdit.WidgetWidth)
            else:
                editor.setLineWrapMode(QPlainTextEdit.NoWrap)

    def zoom_in(self):
        editor = self.current_editor()
        if editor:
            font = editor.font()
            size = font.pointSize()
            font.setPointSize(size + 1)
            editor.setFont(font)

    def zoom_out(self):
        editor = self.current_editor()
        if editor:
            font = editor.font()
            size = font.pointSize()
            if size > 1:
                font.setPointSize(size - 1)
                editor.setFont(font)

    def toggle_sidebar(self, checked):
        if checked:
            self.file_browser.show()
            self.search_bar.show()
        else:
            self.file_browser.hide()
            self.search_bar.hide()

    def toggle_todo_panel(self, checked):
        if checked:
            self.todo_panel.show()
        else:
            self.todo_panel.hide()

    def on_search_text_changed(self, text):
        self.file_browser.display_directory_contents(filter_text=text)

    def timestamp(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def current_editor(self):
        widget = self.tab_widget.currentWidget()
        return widget if isinstance(widget, CodeEditor) else None

    def new_file(self):
        editor = CodeEditor()
        if self.current_theme.lower() == "dark":
            editor.theme = "dark"
            editor.line_highlight_color = QColor("#333c4c")
            editor.lineNumberColor = Qt.lightGray
        else:
            editor.theme = "light"
            editor.line_highlight_color = QColor("#e8f2fe")
            editor.lineNumberColor = Qt.black

        editor.file_path = None
        tab_index = self.tab_widget.addTab(editor, "Untitled")
        self.tab_widget.setCurrentIndex(tab_index)
        self.current_file_map[tab_index] = None
        self.version_label.setText("New File")

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "All Files (*);;Python Files (*.py)")
        if file_path:
            self.open_file_direct(file_path)

    def open_file_direct(self, file_path):
        for idx in range(self.tab_widget.count()):
            if self.current_file_map.get(idx) == file_path:
                self.tab_widget.setCurrentIndex(idx)
                return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            editor = CodeEditor()
            if self.current_theme.lower() == "dark":
                editor.theme = "dark"
                editor.line_highlight_color = QColor("#333c4c")
                editor.lineNumberColor = Qt.lightGray
            else:
                editor.theme = "light"
                editor.line_highlight_color = QColor("#e8f2fe")
                editor.lineNumberColor = Qt.black

            editor.setPlainText(content)
            editor.file_path = file_path
            tab_index = self.tab_widget.addTab(editor, os.path.basename(file_path))
            self.tab_widget.setCurrentIndex(tab_index)
            self.current_file_map[tab_index] = file_path
            self.version_label.setText(f"Opened: {os.path.basename(file_path)} @ {self.timestamp()}")
            self.file_browser.display_directory_contents()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"The file could not be opened:\n{e}")

    def save_file(self):
        editor = self.current_editor()
        if editor is None:
            return

        file_path = editor.file_path

        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(editor.toPlainText())
                self.version_label.setText(f"Saved: {os.path.basename(file_path)} @ {self.timestamp()}")
                self.file_browser.display_directory_contents()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"The file could not be saved:\n{e}")
        else:
            self.save_file_as()

    def save_file_as(self):
        editor = self.current_editor()
        if editor is None:
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Save as", "", "All Files (*);;Python Files (*.py)")
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(editor.toPlainText())
                editor.file_path = file_path

                current_index = self.tab_widget.currentIndex()
                self.tab_widget.setTabText(current_index, os.path.basename(file_path))
                self.current_file_map[current_index] = file_path

                self.version_label.setText(f"Saved: {os.path.basename(file_path)} @ {self.timestamp()}")
                self.file_browser.display_directory_contents()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"The file could not be saved:\n{e}")

    def close_tab(self, index):
        if index in self.current_file_map:
            del self.current_file_map[index]

        self.tab_widget.removeTab(index)

        new_map = {}
        for i, path in self.current_file_map.items():
            if i > index:
                new_map[i - 1] = path
            else:
                new_map[i] = path
        self.current_file_map = new_map

        self.update_version_label()

    def update_version_label(self):
        editor = self.current_editor()
        if editor and editor.file_path:
            self.version_label.setText(f"Selected: {os.path.basename(editor.file_path)} @ {self.timestamp()}")
        else:
            self.version_label.setText("@v0.2")

    def on_tab_changed(self, index):
        self.update_version_label()

        editor = self.current_editor()
        if editor:
            self.todo_panel.update_comments()

            try:
                editor.textChanged.disconnect()
            except TypeError:
                pass
            editor.textChanged.connect(self.todo_panel.update_comments)

    def find_in_editor(self):
        editor = self.current_editor()
        if not editor:
            return
        text, ok = QInputDialog.getText(self, "Find", "Find:")
        if ok and text:
            self.last_search = text
            if not editor.find(text):
                QMessageBox.information(self, "Find", f"'{text}' not found.")

    def find_next_in_editor(self):
        editor = self.current_editor()
        if editor and hasattr(self, 'last_search') and self.last_search:
            if not editor.find(self.last_search):
                cursor = editor.textCursor()
                cursor.movePosition(QTextCursor.Start)
                editor.setTextCursor(cursor)
                if not editor.find(self.last_search):
                    QMessageBox.information(self, "Find Next", f"'{self.last_search}' not found.")

    def find_prev_in_editor(self):
        editor = self.current_editor()
        if editor and hasattr(self, 'last_search') and self.last_search:
            if not editor.find(self.last_search, QTextDocument.FindBackward):
                cursor = editor.textCursor()
                cursor.movePosition(QTextCursor.End)
                editor.setTextCursor(cursor)
                if not editor.find(self.last_search, QTextDocument.FindBackward):
                    QMessageBox.information(self, "Find Previous", f"'{self.last_search}' not found.")

    def replace_in_editor(self):
        editor = self.current_editor()
        if not editor:
            return

        find_text, ok1 = QInputDialog.getText(self, "Replace", "Find:")
        if not (ok1 and find_text):
            return
        replace_text, ok2 = QInputDialog.getText(self, "Replace", "Replace with:")
        if not ok2:
            return

        cursor = editor.textCursor()
        cursor.movePosition(QTextCursor.Start)
        editor.setTextCursor(cursor)

        replaced_any = False
        while editor.find(find_text):
            cursor = editor.textCursor()
            cursor.beginEditBlock()
            cursor.removeSelectedText()
            cursor.insertText(replace_text)
            cursor.endEditBlock()
            replaced_any = True

        if not replaced_any:
            QMessageBox.information(self, "Replace", f"'{find_text}' not found.")

    def goto_line_dialog(self):
        editor = self.current_editor()
        if not editor:
            return
        line, ok = QInputDialog.getInt(self, "Go to Line", "Line number:", 1, 1, editor.blockCount())
        if ok:
            cursor = editor.textCursor()
            cursor.movePosition(QTextCursor.Start)
            cursor.movePosition(QTextCursor.Down, QTextCursor.MoveAnchor, line - 1)
            editor.setTextCursor(cursor)



if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())