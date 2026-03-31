import sys
import os
import platform
import subprocess
import json
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLineEdit,
    QListWidgetItem,
    QSystemTrayIcon,
    QMenu,
    QHBoxLayout,
    QMessageBox,
    QListWidget,
    QAbstractItemView,
    QStyledItemDelegate,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QIcon, QPalette, QColor

folder_data = []
data_file = "folders.json"


def open_folder(folder_path):
    if platform.system() == "Windows":
        os.startfile(folder_path)
    elif platform.system() == "Darwin":
        subprocess.run(["open", folder_path])
    elif platform.system() == "Linux":
        subprocess.run(["xdg-open", folder_path])


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def get_data_file_path():
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(os.path.dirname(sys.executable), data_file)
    return resource_path(data_file)


class FolderItemDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        editor.setFrame(True)
        editor.setTextMargins(0, 0, 0, 0)
        editor.setContentsMargins(0, 0, 0, 0)
        editor.setStyleSheet(
            """
            QLineEdit {
                padding: 0px 2px;
                border: 1px solid #777;
                border-radius: 2px;
                background-color: #414141;
                color: #FFFFFF;
            }
            """
        )
        return editor

    def sizeHint(self, option, index):
        s = super().sizeHint(option, index)
        s.setHeight(max(s.height(), 22))
        return s

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect.adjusted(2, 1, -2, -1))


class FolderListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setEditTriggers(QAbstractItemView.EditTrigger.EditKeyPressed)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def mousePressEvent(self, event):
        item = self.itemAt(event.pos())
        if item is None:
            self.clearSelection()
            self.setCurrentRow(-1)
        super().mousePressEvent(event)


class TrayIcon(QSystemTrayIcon):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setIcon(QIcon(resource_path("快捷文件夹.ico")))

        self.menu = QMenu(parent)
        open_action = QAction("打开", self)
        exit_action = QAction("退出", self)

        open_action.triggered.connect(self.show_window)
        exit_action.triggered.connect(self.exit_app)

        self.menu.addAction(open_action)
        self.menu.addAction(exit_action)
        self.setContextMenu(self.menu)

        self.activated.connect(self.on_activated)

    def show_window(self):
        self.parent().showNormal()
        self.parent().activateWindow()

    def exit_app(self):
        QApplication.quit()

    def on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show_window()


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("快捷文件夹")
        self.setWindowIcon(QIcon(resource_path("快捷文件夹.ico")))

        self._updating_display = False

        self.set_dark_theme()

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        input_layout = QHBoxLayout()

        self.entry = QLineEdit(self)
        self.entry.setPlaceholderText("输入文件夹路径")
        input_layout.addWidget(self.entry)

        self.add_button = QPushButton("添加", self)
        self.add_button.clicked.connect(self.add_folder)
        input_layout.addWidget(self.add_button)

        self.layout.addLayout(input_layout)

        self.folder_listbox = FolderListWidget(self)
        self.folder_listbox.setItemDelegate(FolderItemDelegate(self.folder_listbox))
        self.folder_listbox.itemDoubleClicked.connect(self.on_folder_select)
        self.folder_listbox.model().rowsMoved.connect(self.on_rows_moved)
        self.folder_listbox.itemChanged.connect(self.on_item_changed)
        self.layout.addWidget(self.folder_listbox)

        self.tray_icon = TrayIcon(self)

        self.load_data()
        self.refresh_display()
        self.apply_styles()

    def set_dark_theme(self):
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Base, QColor(35, 35, 35))
        dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(142, 45, 197).lighter())
        dark_palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
        self.setPalette(dark_palette)

    def apply_styles(self):
        self.setStyleSheet(
            """
            QWidget {
                background-color: #353535;
                color: #FFFFFF;
                font-size: 14px;
            }
            QLineEdit {
                padding: 6px;
                border: 1px solid #666;
                border-radius: 4px;
                background-color: #414141;
                color: #FFFFFF;
            }
            QPushButton {
                padding: 6px 12px;
                background-color: #5A5A5A;
                color: #FFFFFF;
                border-radius: 4px;
                border: 1px solid #666;
            }
            QPushButton:hover {
                background-color: #787878;
            }
            QPushButton:pressed {
                background-color: #6A6A6A;
            }
            QListWidget {
                background-color: #414141;
                border: 1px solid #666;
                border-radius: 4px;
                color: #FFFFFF;
            }
            QListWidget::item {
                padding: 0px 2px;
            }
            QListWidget::item:selected {
                background-color: #6A6A6A;
                color: #FFFFFF;
            }
            """
        )

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete:
            self.delete_selected_folder()
            return
        if event.key() == Qt.Key.Key_F2:
            item = self.folder_listbox.currentItem()
            if item is not None:
                self.folder_listbox.editItem(item)
            return
        super().keyPressEvent(event)

    def delete_selected_folder(self):
        selected_row = self.folder_listbox.currentRow()
        if selected_row >= 0:
            folder_data.pop(selected_row)
            self.save_data()
            self.refresh_display()

    def add_folder(self):
        new_folder_path = self.entry.text().strip()
        if new_folder_path:
            display_name = os.path.basename(new_folder_path)
            folder_data.append({"path": new_folder_path, "name": display_name})
            self.entry.clear()
            self.save_data()
            self.refresh_display()

    def on_folder_select(self, item):
        folder_path = item.data(Qt.ItemDataRole.UserRole)
        if folder_path and os.path.exists(folder_path):
            open_folder(folder_path)
        else:
            QMessageBox.warning(self, "错误", "选中的文件夹路径无效。")

    def refresh_display(self):
        self._updating_display = True
        try:
            self.folder_listbox.clear()
            for folder in folder_data:
                item = QListWidgetItem(folder["name"])
                item.setData(Qt.ItemDataRole.UserRole, folder["path"])
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                self.folder_listbox.addItem(item)
        finally:
            self._updating_display = False

    def sync_data_from_list(self):
        global folder_data
        new_data = []
        for i in range(self.folder_listbox.count()):
            item = self.folder_listbox.item(i)
            new_data.append(
                {
                    "path": item.data(Qt.ItemDataRole.UserRole),
                    "name": item.text(),
                }
            )
        folder_data = new_data

    def on_rows_moved(self, parent, start, end, destination, row):
        self.sync_data_from_list()
        self.save_data()

    def on_item_changed(self, item):
        if self._updating_display:
            return
        self.sync_data_from_list()
        self.save_data()

    def load_data(self):
        global folder_data
        folder_data = []
        data_file_path = get_data_file_path()
        try:
            with open(data_file_path, "r", encoding="utf-8") as f:
                folder_data = json.load(f)
        except FileNotFoundError:
            folder_data = []
        self.refresh_display()

    def save_data(self):
        data_file_path = get_data_file_path()
        with open(data_file_path, "w", encoding="utf-8") as f:
            json.dump(folder_data, f, ensure_ascii=False, indent=4)

    def showEvent(self, event):
        self.tray_icon.hide()
        super().showEvent(event)

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.tray_icon.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    window = MainWindow()
    window.resize(240, 350)
    window.show()

    sys.exit(app.exec())