import sys
import os
import json
import random
import math
from pathlib import Path

from PySide6.QtWidgets import (
        QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QCheckBox, QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView,
        QMessageBox, QLineEdit, QGroupBox, QProgressBar, QSpacerItem, QSizePolicy
    )
from PySide6.QtCore import Qt, QThread, Signal

from random_dance import KpopRandomDanceMaker

AUDIO_EXTS = {'.mp3'}

class UI(QWidget):
    def __init__(self, engine):
        super().__init__()

        self.setWindowTitle("Kpop Random Dance Maker")
        self.resize(1000, 600)
        self._build_ui()
        self._set_callbacks()

        # Load init data (config, songs)
        self.engine = engine
        self.load_config_default()
        self.load_songs_default()

    def _build_ui(self):
        main = QHBoxLayout(self)

        left = QVBoxLayout()

        # Config box
        cfg_group = QGroupBox("Configuration")
        cfg_layout = QVBoxLayout()

        self.chk_countdown = QCheckBox("Add countdowns")
        self.btn_countdown_file = QPushButton("No file selected")
        self.chk_random = QCheckBox("Random song order")
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
        self.btn_remove_song = QPushButton("Remove")
        ops.addWidget(self.btn_add_song)
        ops.addWidget(self.btn_remove_song)
        left.addLayout(ops)

        main.addLayout(left, 0)

        # Song table
        right = QVBoxLayout()
        self.table = SongTable()
        right.addWidget(self.table)

        # Cook the results button
        self.bottom = QHBoxLayout()
        right.addLayout(self.bottom)
        self.btn_cook = QPushButton("Cook the playlist")
        self.btn_cook.setStyleSheet("padding-top: 5px; padding-bottom: 5px; padding-left: 20px; padding-right: 20px;")
        
        self.left_spacer = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.right_spacer = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.bottom.addItem(self.left_spacer)
        self.bottom.addWidget(self.btn_cook)
        self.bottom.addItem(self.right_spacer)
        main.addLayout(right, 1)

    def _set_callbacks(self):

        # Config operations
        self.chk_countdown.clicked.connect(self.check_countdown)
        self.btn_countdown_file.clicked.connect(self.select_countdown_file)
        self.chk_random.clicked.connect(self.check_random)
        self.btn_select_folder.clicked.connect(self.select_music_folder)

        # Table operations
        self.table.dropSignal.connect(self.dragAndDropOccured)

        # Song operations
        self.btn_add_song.clicked.connect(self.add_song)
        self.btn_remove_song.clicked.connect(self.remove_selected)

        # Cook operation
        self.btn_cook.clicked.connect(self.create_playlist)

    def dragAndDropOccured(self):
        for row in range(self.table.rowCount()):
            self.engine.setSongProperty(row, "name", self.table.item(row, 0).text())
            self.engine.setSongProperty(row, "start", self.table.item(row, 1).text())
            self.engine.setSongProperty(row, "end", self.table.item(row, 2).text())
        self.engine.writeSongs()

    def setCellName(self, row, value):
        value_item = QTableWidgetItem(value)
        self.table.setItem(row, 0, value_item)

    # ----------------- Default loading -----------------

    def load_config_default(self):
        config = self.engine.getConfig()
        self.chk_countdown.setChecked(config['countdown_enable'])
        self.chk_random.setChecked(config['random_order'])
        self.btn_countdown_file.setText(os.path.basename(config['countdown_file']))
        self.btn_select_folder.setText(os.path.basename(os.path.normpath(config['music_folder'])))

    def load_songs_default(self):
        self.table.blockSignals(True)
        songs = self.engine.getSongs()
        for row in songs:
            self._append_song({'name': row['name'], 'start': row['start'], 'end': row['end']})

        self.table.blockSignals(False)
        

    
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

    def add_song(self):
        newElement = {'name': 'New Song', 'start': '0:00', 'end': '0:00'}
        self._append_song(newElement)
        self.engine.addSong(newElement)

    def remove_selected(self):
        rows = sorted({i.row() for i in self.table.selectedIndexes()}, reverse=True)
        if not rows:
            return
        for r in rows:
            self.table.removeRow(r)
            self.engine.removeSong(r)
        
    def create_playlist(self):
        self.progress = QProgressBar()
        self.progress.setRange(0, 2 * self.table.rowCount() + 1)

        self.bottom.takeAt(2)
        self.bottom.takeAt(0)
        self.bottom.replaceWidget(self.btn_cook, self.progress)
        self.btn_cook.hide()

        self.chef = Chef()
        self.chef.setRecipes(self.engine.cookRandomDance, self.setCellName)
        self.chef.progress.connect(self.progress.setValue)
        self.chef.finished.connect(self.create_playlist_finish)
        self.chef.start()

    def create_playlist_finish(self):
        self.btn_cook.show()
        self.bottom.replaceWidget(self.progress, self.btn_cook)
        self.progress.deleteLater()
        self.bottom.insertItem(0, self.left_spacer)
        self.bottom.addItem(self.right_spacer)

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

class Chef(QThread):
    progress = Signal(int)
    currentRow = Signal(int)
    progress_current = 0 

    def run(self):
        if self.recipe:
            self.recipe(self.advance, self.setRowUI)

    def advance(self):
        self.progress_current = self.progress_current + 1
        self.progress.emit(self.progress_current)

    def setRecipes(self, func, funcUI):
        self.recipe = func
        self.setRowUI = funcUI

class SongTable(QTableWidget):
    dropSignal = Signal()

    def __init__(self):
        super().__init__(0, 3)
        self.setHorizontalHeaderLabels(["URL / Name", "Start", "End"])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.setEditTriggers(QTableWidget.DoubleClicked |
                             QTableWidget.EditKeyPressed |
                             QTableWidget.SelectedClicked)

        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setSelectionMode(QTableWidget.SingleSelection)

        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropOverwriteMode(False)
        self.setDragDropMode(QTableWidget.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)

    def dragEnterEvent(self, event):
        if event.source() is self:
            event.setDropAction(Qt.MoveAction)
            event.accept()
        else:
            event.ignore()

    def moveItemsToRow(self, src_row, dst_row):
        for col in range(self.columnCount()):
            src_item = self.takeItem(src_row, col)
            self.setItem(dst_row, col, src_item)

    def dropEvent(self, event):
        src_row = self.currentRow()
        if src_row < 0:
            event.ignore()
            return

        pos = event.position().toPoint()
        dest_row = self.rowAt(pos.y())

        if src_row < dest_row:
            insert_row = dest_row + 1
            self.insertRow(insert_row)
            self.moveItemsToRow(src_row, insert_row)

            for row in range(src_row, dest_row):
                self.moveItemsToRow(row + 1, row)

            self.removeRow(dest_row)
        else:
            insert_row = dest_row
            self.insertRow(dest_row)
            self.moveItemsToRow(src_row + 1, insert_row)
            self.removeRow(src_row + 1)
        
        self.clearSelection()
        self.selectRow(dest_row if src_row < dest_row else insert_row)
        self.dropSignal.emit()
        return

if __name__ == '__main__':
    engine = KpopRandomDanceMaker(enable_printing=False)

    app = QApplication(sys.argv)
    w = UI(engine=engine)
    w.show()
    sys.exit(app.exec())
