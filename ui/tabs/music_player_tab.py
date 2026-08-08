"""
Music Player tab for Jacarandá application.
Plays the audio file 'Goo Goo Dolls – Iris [Official Music Video] [4K Remaster]-NdYWuo9OFAw.mp4'
with Play and Pause buttons, position slider, and volume control.
Clean audio player design without video display box or stop button.
No emojis used.
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSlider, QGroupBox, QScrollArea, QMessageBox
)
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtGui import QFont


class MusicPlayerTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: #161228; }")
        outer_layout.addWidget(scroll)
        
        container = QWidget()
        scroll.setWidget(container)
        
        main_layout = QVBoxLayout(container)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(24, 24, 24, 24)
        
        # 1. Aesthetic Audio Player Card
        player_card = QGroupBox("Reproductor de Audio - Musica de Fondo")
        card_layout = QVBoxLayout(player_card)
        card_layout.setSpacing(16)
        card_layout.setContentsMargins(24, 24, 24, 24)
        
        # Track Info Panel
        info_layout = QVBoxLayout()
        info_layout.setSpacing(6)
        
        lbl_track_title = QLabel("Iris")
        font_title = QFont()
        font_title.setPointSize(20)
        font_title.setBold(True)
        lbl_track_title.setFont(font_title)
        lbl_track_title.setStyleSheet("color: #F3F0FF;")
        
        lbl_artist = QLabel("Goo Goo Dolls - Official Audio Track")
        lbl_artist.setStyleSheet("color: #38BDF8; font-size: 14px; font-weight: bold;")
        
        lbl_sub = QLabel("Configurado para reproduccion unica (un solo pase sin bucle continuo).")
        lbl_sub.setStyleSheet("color: #A78BFA; font-size: 12px;")
        
        info_layout.addWidget(lbl_track_title)
        info_layout.addWidget(lbl_artist)
        info_layout.addWidget(lbl_sub)
        
        card_layout.addLayout(info_layout)
        
        # Progress slider & Time labels row
        progress_row = QHBoxLayout()
        self.lbl_time_current = QLabel("00:00")
        self.lbl_time_current.setStyleSheet("color: #F3F0FF; font-family: monospace; font-size: 13px; font-weight: bold;")
        
        self.slider_progress = QSlider(Qt.Orientation.Horizontal)
        self.slider_progress.setRange(0, 0)
        self.slider_progress.sliderMoved.connect(self._set_position)
        
        self.lbl_time_total = QLabel("00:00")
        self.lbl_time_total.setStyleSheet("color: #A78BFA; font-family: monospace; font-size: 13px;")
        
        progress_row.addWidget(self.lbl_time_current)
        progress_row.addWidget(self.slider_progress)
        progress_row.addWidget(self.lbl_time_total)
        
        card_layout.addLayout(progress_row)
        
        # Play / Pause Buttons and Volume Row
        controls_row = QHBoxLayout()
        controls_row.setSpacing(16)
        
        self.btn_play = QPushButton("Reproducir")
        self.btn_play.setStyleSheet("padding: 10px 32px; font-size: 14px; font-weight: bold;")
        self.btn_play.clicked.connect(self._play_media)
        controls_row.addWidget(self.btn_play)
        
        self.btn_pause = QPushButton("Pausar")
        self.btn_pause.setObjectName("SecondaryButton")
        self.btn_pause.setStyleSheet("padding: 10px 32px; font-size: 14px;")
        self.btn_pause.clicked.connect(self._pause_media)
        controls_row.addWidget(self.btn_pause)
        
        controls_row.addSpacing(40)
        
        # Volume slider
        controls_row.addWidget(QLabel("Volumen:"))
        self.slider_volume = QSlider(Qt.Orientation.Horizontal)
        self.slider_volume.setRange(0, 100)
        self.slider_volume.setValue(80)
        self.slider_volume.setMaximumWidth(160)
        self.slider_volume.valueChanged.connect(self._set_volume)
        controls_row.addWidget(self.slider_volume)
        
        controls_row.addStretch()
        card_layout.addLayout(controls_row)
        
        main_layout.addWidget(player_card)
        main_layout.addStretch()
        
        # Initialize QMediaPlayer & QAudioOutput
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        
        self.player.setAudioOutput(self.audio_output)
        
        # Signals
        self.player.positionChanged.connect(self._on_position_changed)
        self.player.durationChanged.connect(self._on_duration_changed)
        self.player.mediaStatusChanged.connect(self._on_media_status_changed)
        
        # Load media file
        self.media_path = os.path.abspath("Goo Goo Dolls – Iris [Official Music Video] [4K Remaster]-NdYWuo9OFAw.mp4")
        if os.path.exists(self.media_path):
            self.player.setSource(QUrl.fromLocalFile(self.media_path))
            self.audio_output.setVolume(0.8)
        else:
            lbl_artist.setText("Archivo multimedia no encontrado en la carpeta del proyecto.")

    def _play_media(self):
        if not os.path.exists(self.media_path):
            QMessageBox.warning(self, "Archivo no encontrado", "No se encontro la cancion en la carpeta del proyecto.")
            return
        self.player.play()

    def _pause_media(self):
        self.player.pause()

    def _set_position(self, position):
        self.player.setPosition(position)

    def _set_volume(self, value):
        self.audio_output.setVolume(value / 100.0)

    def _on_position_changed(self, position):
        self.slider_progress.setValue(position)
        self.lbl_time_current.setText(self._format_time(position))

    def _on_duration_changed(self, duration):
        self.slider_progress.setRange(0, duration)
        self.lbl_time_total.setText(self._format_time(duration))

    def _on_media_status_changed(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.player.pause()
            self.player.setPosition(0)

    def _format_time(self, ms):
        seconds = (ms // 1000) % 60
        minutes = (ms // (1000 * 60)) % 60
        return f"{minutes:02d}:{seconds:02d}"
