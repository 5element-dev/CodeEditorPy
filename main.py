import sys
import os
import psutil
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QLabel, QTextBrowser, QMainWindow, QSplitter,
    QPlainTextEdit, QTableWidget, QTableWidgetItem, QHeaderView, QStyleFactory
)
from PyQt5.QtCore import Qt, QRect, QSize, QTimer
from PyQt5.QtGui import QPainter, QColor, QTextFormat, QTextCursor, QTextCharFormat, QMouseEvent

from PyQt5.QtWidgets import QStatusBar, QLabel

from PyQt5.QtWidgets import QMainWindow, QAction, QApplication

from PyQt5.QtWidgets import QTextEdit

from PyQt5.QtWidgets import QFileDialog, QMessageBox
from PyQt5.QtGui import QKeySequence

from datetime import datetime



class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.codeEditor = editor

    def sizeHint(self):
        return QSize(self.codeEditor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self.codeEditor.lineNumberAreaPaintEvent(event)


class CodeEditor(QPlainTextEdit):
    def __init__(self):
        super().__init__()
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.lineNumberArea = LineNumberArea(self)

        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)

        self.updateLineNumberAreaWidth(0)
        self.highlightCurrentLine()

    def lineNumberAreaWidth(self):
        digits = len(str(self.blockCount()))
        space = 3 + self.fontMetrics().width('9') * digits
        return space

    def updateLineNumberAreaWidth(self, _):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

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
        painter.fillRect(event.rect(), QColor(230, 230, 230))

        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(blockNumber + 1)
                painter.setPen(Qt.black)
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
            lineColor = QColor(232, 242, 254)
            selection.format.setBackground(lineColor)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extraSelections.append(selection)

        self.setExtraSelections(extraSelections)


class FileBrowser(QTextBrowser):
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.setLineWrapMode(QTextBrowser.NoWrap)
        self.setStyleSheet("""
            background-color: black;
            color: white;
            font-family: monospace;
        """)
        self.current_dir = os.getcwd()
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
                cursor.insertHtml(f'<span style="color:white;">{item}</span><br>')

        cursor.movePosition(QTextCursor.Start)

    def insert_folder_link(self, cursor, folder_name):
        cursor.insertHtml(f'📁 ')
        fmt = QTextCharFormat()
        fmt.setForeground(Qt.cyan)
        fmt.setAnchor(True)
        fmt.setAnchorHref(folder_name)
        fmt.setFontUnderline(False)
        cursor.insertText(folder_name + '/', fmt)
        cursor.insertHtml('<br>')

    def mouseMoveEvent(self, event: QMouseEvent):
        anchor = self.anchorAt(event.pos())
        if anchor:
            self.setCursor(Qt.PointingHandCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        anchor = self.anchorAt(event.pos())
        if anchor:
            if anchor == "..":
                self.current_dir = os.path.dirname(self.current_dir)
            else:
                potential_dir = os.path.join(self.current_dir, anchor)
                if os.path.isdir(potential_dir):
                    self.current_dir = potential_dir
            self.display_directory_contents()
        else:
            super().mouseReleaseEvent(event)


class TodoPanel(QWidget):
    def __init__(self, editor):
        super().__init__()
        self.editor = editor
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Type", "Description", "Line"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.layout.addWidget(self.table)

        self.keywords = ["TODO", "FIXME", "HACK", "NOTE", "OPTIMIZE"]
        self.update_comments()

        self.editor.textChanged.connect(self.update_comments)
        self.table.cellClicked.connect(self.jump_to_line)

    def update_comments(self):
        self.table.setRowCount(0)
        lines = self.editor.toPlainText().split("\n")

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
        line = int(self.table.item(row, 2).text()) - 1
        cursor = self.editor.textCursor()
        cursor.movePosition(QTextCursor.Start)
        cursor.movePosition(QTextCursor.Down, QTextCursor.MoveAnchor, line)
        self.editor.setTextCursor(cursor)
        self.editor.setFocus()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("CodeEditor")
        self.setGeometry(100, 100, 1000, 600)
        self.current_file = None

        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("File")

        open_action = QAction("Open", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self.open_file)

        save_action = QAction("Save", self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.triggered.connect(self.save_file)

        save_as_action = QAction("Save as...", self)
        save_as_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        save_as_action.triggered.connect(self.save_file_as)

        file_menu.addAction(open_action)
        file_menu.addAction(save_action)
        file_menu.addAction(save_as_action)

        main_splitter = QSplitter(Qt.Horizontal)

        self.editor = CodeEditor()
        main_splitter.addWidget(self.editor)
        main_splitter.setStretchFactor(0, 5)

        right_splitter = QSplitter(Qt.Vertical)

        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_widget.setLayout(right_layout)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search files/folders...")
        right_layout.addWidget(self.search_bar)

        self.file_browser = FileBrowser()
        right_layout.addWidget(self.file_browser, stretch=1)

        right_splitter.addWidget(right_widget)

        self.todo_panel = TodoPanel(self.editor)
        right_splitter.addWidget(self.todo_panel)

        right_splitter.setStretchFactor(0, 3)
        right_splitter.setStretchFactor(1, 2)

        main_splitter.addWidget(right_splitter)
        main_splitter.setStretchFactor(1, 2)

        self.setCentralWidget(main_splitter)

        self.version_label = QLabel("@v0.1-alpha")
        self.version_label.setStyleSheet("color: red;")
        status_bar = QStatusBar()
        status_bar.addPermanentWidget(self.version_label, 1)

        self.setStatusBar(status_bar)

        self.search_bar.textChanged.connect(self.on_search_text_changed)

    def on_search_text_changed(self, text):
        self.file_browser.display_directory_contents(filter_text=text)

    def timestamp(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "All Files (*);;Python Files (*.py)")
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    self.editor.setPlainText(f.read())
                self.current_file = file_path
                self.version_label.setText(f"Opened: {os.path.basename(file_path)} @ {self.timestamp()}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"The file could not be opened:\n{e}")

    def save_file(self):
        if self.current_file:
            try:
                with open(self.current_file, "w", encoding="utf-8") as f:
                    f.write(self.editor.toPlainText())
                self.version_label.setText(f"Saved: {os.path.basename(self.current_file)} @ {self.timestamp()}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"The file could not be saved:\n{e}")
        else:
            self.save_file_as()

    def save_file_as(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save as", "", "All Files (*);;Python Files (*.py)")
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(self.editor.toPlainText())
                self.current_file = file_path
                self.version_label.setText(f"Saved: {os.path.basename(file_path)} @ {self.timestamp()}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"The file could not be saved:\n{e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
