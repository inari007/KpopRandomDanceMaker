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


def validate_time_string(s: str) -> bool:
    """Validates time in hh:mm:ss, mm:ss or seconds (int/float)."""
    s = s.strip()
    if not s:
        return True
    if s.isdigit():
        return True
    parts = s.split(":")
    if len(parts) > 3:
        return False
    try:
        for p in parts:
            if p == '':
                return False
            float(p)
        return True
    except Exception:
        return False


class UI(QWidget):
    def __init__(self, engine):
        super().__init__()
        self.setWindowTitle("Kpop Random Dance Maker")
        self.resize(1000, 600)

        self._build_ui()

        self.engine = engine
        self.load_config_default()

    def _build_ui(self):
        main = QHBoxLayout(self)

        # Left side
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
       
        # Add config to left
        cfg_group.setLayout(cfg_layout)
        left.addWidget(cfg_group)
        left.addStretch(1)

        # Buttons for song import/add/remove
        left.addWidget(QLabel("Song operations:"))
        ops = QVBoxLayout()
        self.btn_import_folder = QPushButton("Import audio from folder")
        self.btn_add_song = QPushButton("Add song")
        self.btn_remove_song = QPushButton("Remove selected")
        self.btn_swap = QPushButton("Swap two selected")
        self.btn_move_up = QPushButton("Move up")
        self.btn_move_down = QPushButton("Move down")
        ops.addWidget(self.btn_import_folder)
        ops.addWidget(self.btn_add_song)
        ops.addWidget(self.btn_remove_song)
        ops.addWidget(self.btn_swap)
        ops.addWidget(self.btn_move_up)
        ops.addWidget(self.btn_move_down)
        left.addLayout(ops)

        main.addLayout(left, 0)

        # Right: table
        right = QVBoxLayout()
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Order", "Name", "Start", "End"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.DoubleClicked | QTableWidget.EditKeyPressed | QTableWidget.SelectedClicked)
        right.addWidget(self.table)

        # Bottom actions
        bottom = QHBoxLayout()
        self.btn_print = QPushButton("Print songs to console")
        self.btn_validate = QPushButton("Validate times")
        bottom.addWidget(self.btn_print)
        bottom.addWidget(self.btn_validate)
        right.addLayout(bottom)

        main.addLayout(right, 1)

        # Connections config
        self.chk_countdown.clicked.connect(self.check_countdown)
        self.btn_countdown_file.clicked.connect(self.select_countdown_file)
        self.chk_random.clicked.connect(self.check_random)
        self.btn_select_folder.clicked.connect(self.select_music_folder)


        # Connections
        self.btn_import_folder.clicked.connect(self.import_from_folder)
        self.btn_add_song.clicked.connect(self.add_song)
        self.btn_remove_song.clicked.connect(self.remove_selected)
        self.btn_swap.clicked.connect(self.swap_two_selected)
        self.btn_move_up.clicked.connect(lambda: self.move_selected(-1))
        self.btn_move_down.clicked.connect(lambda: self.move_selected(1))
        self.btn_print.clicked.connect(self.print_songs)
        self.btn_validate.clicked.connect(self.validate_times)

    # ----------------- Config actions -----------------
    def load_config_default(self):
        config = self.engine.getConfig()
        self.chk_countdown.setChecked(config['countdown_enable'])
        self.chk_random.setChecked(config['random_order'])
        self.btn_countdown_file.setText(os.path.basename(config['countdown_file']))
        self.btn_select_folder.setText(os.path.basename(os.path.normpath(config['music_folder'])))

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

    # ----------------- Save/Load -----------------
    def get_songs_from_table(self):
        songs = []
        for r in range(self.table.rowCount()):
            name = self.table.item(r, 1).text() if self.table.item(r, 1) else ''
            start = self.table.item(r, 2).text() if self.table.item(r, 2) else ''
            end = self.table.item(r, 3).text() if self.table.item(r, 3) else ''
            songs.append({'name': name, 'start': start, 'end': end})
        return songs

    # ----------------- Helpers -----------------
    def _append_song(self, s: dict):
        r = self.table.rowCount()
        self.table.insertRow(r)
        order_item = QTableWidgetItem(str(r + 1))
        order_item.setFlags(order_item.flags() & ~Qt.ItemIsEditable)
        self.table.setItem(r, 0, order_item)
        name_item = QTableWidgetItem(s.get('name', ''))
        start_item = QTableWidgetItem(s.get('start', ''))
        end_item = QTableWidgetItem(s.get('end', ''))
        self.table.setItem(r, 1, name_item)
        self.table.setItem(r, 2, start_item)
        self.table.setItem(r, 3, end_item)

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

    def print_songs(self):
        songs = self.get_songs_from_table()
        print(json.dumps(songs, indent=2, ensure_ascii=False))
        QMessageBox.information(self, "Printed", "Song list printed to console.")

    def validate_times(self):
        errors = []
        for r in range(self.table.rowCount()):
            start = self.table.item(r, 2).text() if self.table.item(r, 2) else ''
            end = self.table.item(r, 3).text() if self.table.item(r, 3) else ''
            if not validate_time_string(start):
                errors.append(f"Row {r+1} start time invalid: '{start}'")
            if not validate_time_string(end):
                errors.append(f"Row {r+1} end time invalid: '{end}'")
        if errors:
            QMessageBox.warning(self, "Validation errors", "\n".join(errors))
        else:
            QMessageBox.information(self, "OK", "All times look valid (or empty).")


if __name__ == '__main__':
    engine = KpopRandomDanceMaker(enable_printing=False)

    app = QApplication(sys.argv)
    w = UI(engine=engine)
    w.show()
    sys.exit(app.exec())
