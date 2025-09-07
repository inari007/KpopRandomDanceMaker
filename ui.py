import sys
import os
import json
import random
from pathlib import Path

from PySide6.QtWidgets import (
        QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QCheckBox, QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView,
        QMessageBox, QLineEdit, QGroupBox
    )
from PySide6.QtCore import Qt

from random_dance import KpopRandomDanceMaker

AUDIO_EXTS = {'.mp3'}

class UI(QWidget):
    def __init__(self, engine):
        super().__init__()
        # Set UI elements
        self.setWindowTitle("Kpop Random Dance Maker")
        self.resize(1000, 600)
        self._build_ui()
        self._set_callbacks()

        # Load init data (config, songs)
        self.engine = engine    # backend
        self.load_config_default()
        self.load_songs_default()

    def _build_ui(self):
        main = QHBoxLayout(self)

        left = QVBoxLayout()

        # Config box
        cfg_group = QGroupBox("Configuration")
        cfg_layout = QVBoxLayout()

        self.chk_countdown = QCheckBox("Enable countdown")
        self.btn_countdown_file = QPushButton("No file selected")
        self.chk_random = QCheckBox("Randomize order on load")
        self.btn_select_folder = QPushButton("No folder selected")
        
        cfg_layout.addWidget(self.chk_countdown)
        cfg_layout.addWidget(self.btn_countdown_file)
        cfg_layout.addWidget(self.chk_random)
        cfg_layout.addWidget(self.btn_select_folder)
       
        cfg_group.setLayout(cfg_layout)
        left.addWidget(cfg_group)
        left.addStretch(1)

        # Song operations box
        ops = QVBoxLayout()
        self.btn_add_song = QPushButton("Add song")
        self.btn_remove_song = QPushButton("Delete")
        self.btn_swap = QPushButton("Swap two selected")
        self.btn_move_up = QPushButton("Move up")
        self.btn_move_down = QPushButton("Move down")
        ops.addWidget(self.btn_add_song)
        ops.addWidget(self.btn_remove_song)
        ops.addWidget(self.btn_swap)
        ops.addWidget(self.btn_move_up)
        ops.addWidget(self.btn_move_down)
        left.addLayout(ops)

        main.addLayout(left, 0)

        # Song table
        right = QVBoxLayout()
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["URL / Name", "Start", "End"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.DoubleClicked | QTableWidget.EditKeyPressed | QTableWidget.SelectedClicked)
        right.addWidget(self.table)

        # Cook the results button
        bottom = QHBoxLayout()
        right.addLayout(bottom)
        self.btn_cook = QPushButton("Cook the playlist")
        bottom.addWidget(self.btn_cook)
        main.addLayout(right, 1)

    def _set_callbacks(self):

        # Config operations
        self.chk_countdown.clicked.connect(self.check_countdown)
        self.btn_countdown_file.clicked.connect(self.select_countdown_file)
        self.chk_random.clicked.connect(self.check_random)
        self.btn_select_folder.clicked.connect(self.select_music_folder)

        # Song operations
        self.btn_add_song.clicked.connect(self.add_song)
        self.btn_remove_song.clicked.connect(self.remove_selected)
        self.btn_swap.clicked.connect(self.swap_two_selected)

        # Song item operations
        self.btn_move_up.clicked.connect(lambda: self.move_selected(-1))
        self.btn_move_down.clicked.connect(lambda: self.move_selected(1))

        # Cook operation
        self.btn_cook.clicked.connect(self.create_playlist)

    # ----------------- Default loading -----------------

    def load_config_default(self):
        config = self.engine.getConfig()
        self.chk_countdown.setChecked(config['countdown_enable'])
        self.chk_random.setChecked(config['random_order'])
        self.btn_countdown_file.setText(os.path.basename(config['countdown_file']))
        self.btn_select_folder.setText(os.path.basename(os.path.normpath(config['music_folder'])))

    def load_songs_default(self):
        songs = self.engine.getSongs()
        for row in songs:
            self._append_song({'name': row['name'], 'start': row['start'], 'end': row['end']})
        

    
    # ----------------- Config actions -----------------

    def check_countdown(self, checked):
        self.engine.config['countdown_enable'] = checked
        self.engine.writeConfig()

    def select_countdown_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select countdown file", str(Path.home()))
        if path:
            self.btn_countdown_file.setText(path)
            self.engine.config['countdown_file'] = path
            self.engine.writeConfig()

    def check_random(self, checked):
        self.engine.config['random_order'] = checked
        self.engine.writeConfig()

    def select_music_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Select music folder", str(Path.home()))
        if path:
            self.btn_select_folder.setText(path)
            self.engine.config['music_folder'] = path
            self.engine.writeConfig()


    # ----------------- Song actions -----------------


    def import_from_folder(self):
        folder = self.lbl_folder.text()
        if not folder or folder == 'No folder selected':
            QMessageBox.warning(self, "No folder", "Please select a music folder first.")
            return
        folder = Path(folder)
        files = [p for p in folder.iterdir() if p.suffix.lower() in AUDIO_EXTS and p.is_file()]
        for f in files:
            name = f.stem
            self._append_song({'name': name, 'start': '', 'end': '', 'path': str(f)})
        self._refresh_order()

    def add_song(self):
        self._append_song({'name': 'New Song', 'start': '', 'end': ''})
        self._refresh_order()

    def remove_selected(self):
        rows = sorted({i.row() for i in self.table.selectedIndexes()}, reverse=True)
        if not rows:
            return
        for r in rows:
            self.table.removeRow(r)
        self._refresh_order()

    def swap_two_selected(self):
        rows = sorted({i.row() for i in self.table.selectedIndexes()})
        if len(rows) != 2:
            QMessageBox.information(self, "Select exactly two rows", "Please select exactly two rows to swap.")
            return
        r1, r2 = rows
        items1 = [self.table.item(r1, c).text() if self.table.item(r1, c) else '' for c in range(1, 4)]
        items2 = [self.table.item(r2, c).text() if self.table.item(r2, c) else '' for c in range(1, 4)]
        for c in range(1, 4):
            self.table.setItem(r1, c, QTableWidgetItem(items2[c-1]))
            self.table.setItem(r2, c, QTableWidgetItem(items1[c-1]))

    def move_selected(self, direction: int):
        rows = sorted({i.row() for i in self.table.selectedIndexes()})
        if not rows:
            return
        row = rows[0]
        new_row = row + direction
        if new_row < 0 or new_row >= self.table.rowCount():
            return
        for c in range(1, 4):
            a = self.table.item(row, c).text() if self.table.item(row, c) else ''
            b = self.table.item(new_row, c).text() if self.table.item(new_row, c) else ''
            self.table.setItem(new_row, c, QTableWidgetItem(a))
            self.table.setItem(row, c, QTableWidgetItem(b))
        self.table.selectRow(new_row)
        self._refresh_order()

    def create_playlist(self):
        pass

    # ----------------- Save/Load -----------------
    def get_songs_from_table(self):
        songs = []
        for r in range(self.table.rowCount()):
            name = self.table.item(r, 0).text() if self.table.item(r, 1) else ''
            start = self.table.item(r, 1).text() if self.table.item(r, 2) else ''
            end = self.table.item(r, 2).text() if self.table.item(r, 3) else ''
            songs.append({'name': name, 'start': start, 'end': end})
        return songs

    # ----------------- Helpers -----------------
    def _append_song(self, s: dict):
        r = self.table.rowCount()
        self.table.insertRow(r)
        order_item = QTableWidgetItem(str(r + 1))
        order_item.setFlags(order_item.flags() & ~Qt.ItemIsEditable)
        name_item = QTableWidgetItem(s.get('name', ''))
        start_item = QTableWidgetItem(s.get('start', ''))
        end_item = QTableWidgetItem(s.get('end', ''))
        self.table.setItem(r, 0, name_item)
        self.table.setItem(r, 1, start_item)
        self.table.setItem(r, 2, end_item)

    def _refresh_order(self):
        for r in range(self.table.rowCount()):
            item = self.table.item(r, 0)
            if not item:
                item = QTableWidgetItem(str(r+1))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(r, 0, item)
            else:
                item.setText(str(r+1))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)


if __name__ == '__main__':
    engine = KpopRandomDanceMaker(enable_printing=False)

    app = QApplication(sys.argv)
    w = UI(engine=engine)
    w.show()
    sys.exit(app.exec())
