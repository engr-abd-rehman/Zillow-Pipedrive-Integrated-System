#!/usr/bin/env python3
"""
Zillow-Pipedrive Integrated System UI
Professional UI for managing properties, scraping, and Pipedrive sync
Configuration from config.ini file
"""

import sys
import sqlite3
import csv
import os
import requests
import ctypes
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem, QLabel, QComboBox, QLineEdit,
    QTextEdit, QMessageBox, QFileDialog, QProgressBar, QSpinBox, QHeaderView,
    QGroupBox, QCheckBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QIcon, QCursor
from datetime import datetime
import time
from zillow_advanced_scraper import AdvancedZillowScraper
from config_manager import get_config

# Load configuration
config = get_config()

# Paths (from config.ini)
DB_PATH = config.get_database_path()
CSV_PATH = config.get_csv_path()

# Pipedrive API Configuration (from config.ini)
PIPEDRIVE_API_TOKEN = config.get_pipedrive_api_token()
PIPEDRIVE_API_URL = config.get_pipedrive_api_url()
PIPELINE_ID = 9  # On Market pipeline

# Stage mapping (Display names) - UPDATED 2026-01-31
STAGE_MAPPING = {
    'lead_in': 'Lead In',
    'no_response': 'No Response',
    'verbal_follow_up': 'Verbal Follow Up',
    'contract_follow_up': 'Contract Follow up',
    'day_30_follow_up': '30 Day Follow Up',
    'day_60_follow_up': '60 Day Follow Up',
    'day_90_follow_up': '90 Day Follow Up',
    'pending': 'Pending',
    'expired_listing': 'Expired Listing',
    'dead_deal': 'Dead Deal'
}

# Pipedrive Stage ID to Table mapping (UPDATED 2026-01-31)
STAGE_ID_TO_TABLE = {
    101: 'lead_in',                      # Lead In
    109: 'no_response',                  # No Response
    134: 'verbal_follow_up',             # Verbal Follow Up
    104: 'contract_follow_up',           # Contract Follow up
    111: 'day_30_follow_up',             # 30 Day Follow Up
    113: 'day_60_follow_up',             # 60 Day Follow Up
    112: 'day_90_follow_up',             # 90 Day Follow Up
    114: 'pending',                      # Pending
    105: 'expired_listing',              # Expired Listing
    133: 'dead_deal'                     # Dead Deal
}


class ZillowPipedriveUI(QMainWindow):
    """Main UI Window"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Zillow Integrated System - Terry Royer")
        self.setGeometry(50, 50, 1400, 900)

        # Set window icon
        icon_path = 'lcon.png'
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # Create tabs
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # Tab 1: Properties Database
        self.properties_tab = QWidget()
        self.init_properties_tab()
        self.tabs.addTab(self.properties_tab, "📊 Properties Database")
        
        # Tab 2: CSV Editor
        self.csv_tab = QWidget()
        self.init_csv_tab()
        self.tabs.addTab(self.csv_tab, "📝 CSV Editor")
        
        # Tab 3: Auto Scraper
        self.scraper_tab = QWidget()
        self.init_scraper_tab()
        self.tabs.addTab(self.scraper_tab, "🔍 Auto Scraper")
        
        # Tab 4: Pipedrive Sync
        self.sync_tab = QWidget()
        self.init_sync_tab()
        self.tabs.addTab(self.sync_tab, "🔄 Pipedrive Sync")
        
        # Load initial data
        self.load_properties()
    
    def init_properties_tab(self):
        """Initialize Properties Database Tab"""
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("PROPERTIES DATABASE")
        header.setFont(QFont("Arial", 16, QFont.Bold))
        header.setStyleSheet("color: #2c3e50; padding: 10px;")
        layout.addWidget(header)
        
        # Filters Section
        filters_group = QGroupBox("🔍 FILTERS")
        filters_group.setFont(QFont("Arial", 10, QFont.Bold))
        filters_layout = QVBoxLayout()
        
        # Row 1: Status and Property Type
        row1 = QHBoxLayout()
        
        # Status filter
        row1.addWidget(QLabel("Status:"))
        self.status_combo = QComboBox()
        self.status_combo.addItems(list(STAGE_MAPPING.values()))
        self.status_combo.setCurrentText("Lead In")
        self.status_combo.currentTextChanged.connect(self.load_properties)
        row1.addWidget(self.status_combo)
        
        # Property Type filter
        row1.addWidget(QLabel("Property Type:"))
        self.property_type_combo = QComboBox()
        self.property_type_combo.addItems([
            "All",
            "AS-IS",
            "INVESTOR SPECIAL",
            "INVESTOR OPPORTUNITY",
            "NEEDS WORK",
            "OUTDATED",
            "DATED",
            "NEEDS UPDATING",
            "FIXER UPPER",
            "MOTIVATED",
            "TLC"
        ])
        self.property_type_combo.currentTextChanged.connect(self.load_properties)
        row1.addWidget(self.property_type_combo)
        
        row1.addStretch()
        filters_layout.addLayout(row1)
        
        # Row 2: Search
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search address, agent...")
        self.search_input.textChanged.connect(self.filter_properties)
        row2.addWidget(self.search_input)
        filters_layout.addLayout(row2)
        
        filters_group.setLayout(filters_layout)
        layout.addWidget(filters_group)
        
        # Statistics Section
        stats_layout = QHBoxLayout()
        self.stats_label = QLabel("Total Properties: 0")
        self.stats_label.setFont(QFont("Arial", 10))
        self.stats_label.setStyleSheet("color: #27ae60; font-weight: bold;")
        stats_layout.addWidget(self.stats_label)
        stats_layout.addStretch()

        # Update button
        update_btn = QPushButton("✏️ Update Property")
        update_btn.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                font-weight: bold;
                padding: 5px 15px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
        """)
        update_btn.clicked.connect(self.update_property)
        stats_layout.addWidget(update_btn)

        # Delete button
        delete_btn = QPushButton("🗑️ Delete Property")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                font-weight: bold;
                padding: 5px 15px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        delete_btn.clicked.connect(self.delete_property)
        stats_layout.addWidget(delete_btn)

        # Export button
        export_btn = QPushButton("📤 Export CSV")
        export_btn.clicked.connect(self.export_properties)
        stats_layout.addWidget(export_btn)

        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.load_properties)
        stats_layout.addWidget(refresh_btn)

        layout.addLayout(stats_layout)

        # Properties Table
        self.properties_table = QTableWidget()
        self.properties_table.setColumnCount(11)
        self.properties_table.setHorizontalHeaderLabels([
            "ID", "Address", "Beds", "Baths", "Sqft", "Price",
            "Property Type", "Agent", "Phone", "Person ID", "Synced At"
        ])

        # Set column widths
        header = self.properties_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Address
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Beds
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Baths
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Sqft
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Price
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Property Type
        header.setSectionResizeMode(7, QHeaderView.Stretch)  # Agent
        header.setSectionResizeMode(8, QHeaderView.ResizeToContents)  # Phone
        header.setSectionResizeMode(9, QHeaderView.ResizeToContents)  # Person ID
        header.setSectionResizeMode(10, QHeaderView.ResizeToContents)  # Synced At

        self.properties_table.setAlternatingRowColors(True)
        self.properties_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #bdc3c7;
                background-color: white;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
        """)

        layout.addWidget(self.properties_table)

        # Property Details Section
        details_group = QGroupBox("📋 PROPERTY DETAILS")
        details_group.setFont(QFont("Arial", 10, QFont.Bold))
        details_layout = QVBoxLayout()

        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setMaximumHeight(150)
        details_layout.addWidget(self.details_text)

        # Action buttons
        actions_layout = QHBoxLayout()

        open_browser_btn = QPushButton("🌐 Open in Browser")
        open_browser_btn.clicked.connect(self.open_in_browser)
        actions_layout.addWidget(open_browser_btn)

        actions_layout.addStretch()
        details_layout.addLayout(actions_layout)

        details_group.setLayout(details_layout)
        layout.addWidget(details_group)

        self.properties_tab.setLayout(layout)

        # Connect table selection
        self.properties_table.itemSelectionChanged.connect(self.show_property_details)

    def init_csv_tab(self):
        """Initialize CSV Editor Tab"""
        layout = QVBoxLayout()

        # Header
        header = QLabel("CSV EDITOR")
        header.setFont(QFont("Arial", 16, QFont.Bold))
        header.setStyleSheet("color: #2c3e50; padding: 10px;")
        layout.addWidget(header)

        # Info
        info = QLabel(f"📁 File: {CSV_PATH}")
        info.setStyleSheet("color: #7f8c8d; padding: 5px;")
        layout.addWidget(info)

        # Buttons
        buttons_layout = QHBoxLayout()

        load_btn = QPushButton("📂 Load CSV")
        load_btn.clicked.connect(self.load_csv)
        buttons_layout.addWidget(load_btn)

        save_btn = QPushButton("💾 Save CSV")
        save_btn.clicked.connect(self.save_csv)
        buttons_layout.addWidget(save_btn)

        # Add Create button
        create_btn = QPushButton("➕ Create Row")
        create_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                padding: 5px 15px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        create_btn.clicked.connect(self.create_csv_row)
        buttons_layout.addWidget(create_btn)

        # Add Update button
        update_csv_btn = QPushButton("✏️ Update Row")
        update_csv_btn.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                font-weight: bold;
                padding: 5px 15px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
        """)
        update_csv_btn.clicked.connect(self.update_csv_row)
        buttons_layout.addWidget(update_csv_btn)

        # Add Delete button
        delete_csv_btn = QPushButton("🗑️ Delete Row")
        delete_csv_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                font-weight: bold;
                padding: 5px 15px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        delete_csv_btn.clicked.connect(self.delete_csv_row)
        buttons_layout.addWidget(delete_csv_btn)

        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)

        # CSV Table
        self.csv_table = QTableWidget()
        self.csv_table.setAlternatingRowColors(True)
        layout.addWidget(self.csv_table)

        self.csv_tab.setLayout(layout)

    def init_scraper_tab(self):
        """Initialize Auto Scraper Tab with full functionality"""
        layout = QVBoxLayout()

        # Header
        header = QLabel("🔍 ADVANCED ZILLOW SCRAPER")
        header.setFont(QFont("Arial", 16, QFont.Bold))
        header.setStyleSheet("color: #2c3e50; padding: 10px;")
        layout.addWidget(header)

        # ========== SETTINGS SECTION ==========
        settings_group = QGroupBox("⚙️ SCRAPER SETTINGS")
        settings_group.setFont(QFont("Arial", 10, QFont.Bold))
        settings_group.setStyleSheet("""
            QGroupBox {
                border: 2px solid #3498db;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                color: #3498db;
            }
        """)
        settings_layout = QVBoxLayout()

        # Row 1: Max Properties
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Maximum Properties to Scrape:"))
        self.max_properties_spin = QSpinBox()
        self.max_properties_spin.setMinimum(1)
        self.max_properties_spin.setMaximum(1000)
        self.max_properties_spin.setValue(50)
        self.max_properties_spin.setMinimumWidth(100)
        row1.addWidget(self.max_properties_spin)
        row1.addStretch()
        settings_layout.addLayout(row1)

        # Row 2: Delay
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Delay Between Properties (seconds):"))
        self.delay_spin = QSpinBox()
        self.delay_spin.setMinimum(1)
        self.delay_spin.setMaximum(60)
        self.delay_spin.setValue(5)
        self.delay_spin.setMinimumWidth(100)
        row2.addWidget(self.delay_spin)
        row2.addStretch()
        settings_layout.addLayout(row2)

        # Row 3: Batch Size
        row3 = QHBoxLayout()
        row3.addWidget(QLabel("Properties per URL Category:"))
        self.batch_size_spin = QSpinBox()
        self.batch_size_spin.setMinimum(1)
        self.batch_size_spin.setMaximum(50)
        self.batch_size_spin.setValue(5)
        self.batch_size_spin.setMinimumWidth(100)
        row3.addWidget(self.batch_size_spin)
        row3.addStretch()
        settings_layout.addLayout(row3)

        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)

        # ========== CONTROL BUTTONS ==========
        buttons_layout = QHBoxLayout()

        self.start_scraper_btn = QPushButton("🚀 START SCRAPING")
        self.start_scraper_btn.setMinimumHeight(50)
        self.start_scraper_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.start_scraper_btn.clicked.connect(self.start_scraping)
        buttons_layout.addWidget(self.start_scraper_btn)

        self.stop_scraper_btn = QPushButton("⏸️ STOP SCRAPING")
        self.stop_scraper_btn.setMinimumHeight(50)
        self.stop_scraper_btn.setEnabled(False)
        self.stop_scraper_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.stop_scraper_btn.clicked.connect(self.stop_scraping)
        buttons_layout.addWidget(self.stop_scraper_btn)

        layout.addLayout(buttons_layout)

        # ========== PROGRESS SECTION ==========
        progress_group = QGroupBox("📊 PROGRESS")
        progress_group.setFont(QFont("Arial", 10, QFont.Bold))
        progress_layout = QVBoxLayout()

        # Status label
        self.scraper_status_label = QLabel("Status: Ready")
        self.scraper_status_label.setStyleSheet("font-size: 12px; color: #27ae60; font-weight: bold;")
        progress_layout.addWidget(self.scraper_status_label)

        # Progress bar
        self.scraper_progress = QProgressBar()
        self.scraper_progress.setMinimum(0)
        self.scraper_progress.setMaximum(100)
        self.scraper_progress.setValue(0)
        self.scraper_progress.setTextVisible(True)
        self.scraper_progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                text-align: center;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #3498db;
            }
        """)
        progress_layout.addWidget(self.scraper_progress)

        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)

        # ========== LOG SECTION ==========
        log_group = QGroupBox("📋 SCRAPING LOG")
        log_group.setFont(QFont("Arial", 10, QFont.Bold))
        log_layout = QVBoxLayout()

        # Clear button for log
        clear_log_btn = QPushButton("🧹 Clear Terminal")
        clear_log_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                font-weight: bold;
                padding: 5px 15px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        clear_log_btn.clicked.connect(self.clear_scraper_log)
        log_layout.addWidget(clear_log_btn)

        self.scraper_log = QTextEdit()
        self.scraper_log.setReadOnly(True)
        self.scraper_log.setFont(QFont("Consolas", 9))
        self.scraper_log.setStyleSheet("""
            QTextEdit {
                background-color: #2c3e50;
                color: #ecf0f1;
                border: 2px solid #34495e;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        log_layout.addWidget(self.scraper_log)

        log_group.setLayout(log_layout)
        layout.addWidget(log_group)

        self.scraper_tab.setLayout(layout)

        # Initialize scraper worker as None
        self.scraper_worker = None

    def init_sync_tab(self):
        """Initialize Pipedrive Sync Tab"""
        layout = QVBoxLayout()

        # Header
        header = QLabel("PIPEDRIVE SYNC")
        header.setFont(QFont("Arial", 16, QFont.Bold))
        header.setStyleSheet("color: #2c3e50; padding: 10px;")
        layout.addWidget(header)

        # ========== SECTION 1: Upload New Properties ==========
        section1 = QGroupBox("📤 UPLOAD NEW PROPERTIES TO PIPEDRIVE")
        section1.setFont(QFont("Arial", 10, QFont.Bold))
        section1.setStyleSheet("""
            QGroupBox {
                border: 2px solid #3498db;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                color: #3498db;
            }
        """)
        section1_layout = QVBoxLayout()

        # Stats
        stats1_layout = QHBoxLayout()
        self.db_count_label = QLabel("Database Properties: 0")
        self.pd_count_label = QLabel("Pipedrive Deals: 0")
        self.new_count_label = QLabel("New Properties: 0")
        self.new_count_label.setStyleSheet("color: #27ae60; font-weight: bold;")

        stats1_layout.addWidget(self.db_count_label)
        stats1_layout.addWidget(QLabel("|"))
        stats1_layout.addWidget(self.pd_count_label)
        stats1_layout.addWidget(QLabel("|"))
        stats1_layout.addWidget(self.new_count_label)
        stats1_layout.addStretch()
        section1_layout.addLayout(stats1_layout)

        # Buttons
        buttons1_layout = QHBoxLayout()

        check_new_btn = QPushButton("🔍 Check New Properties")
        check_new_btn.setMinimumHeight(40)
        check_new_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        check_new_btn.clicked.connect(self.check_new_properties)
        buttons1_layout.addWidget(check_new_btn)

        upload_btn = QPushButton("📤 Upload to Pipedrive")
        upload_btn.setMinimumHeight(40)
        upload_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        upload_btn.clicked.connect(self.upload_new_to_pipedrive)
        buttons1_layout.addWidget(upload_btn)

        section1_layout.addLayout(buttons1_layout)
        section1.setLayout(section1_layout)
        layout.addWidget(section1)

        # ========== SECTION 2: Sync Stage Changes ==========
        section2 = QGroupBox("🔄 SYNC STAGE CHANGES FROM PIPEDRIVE")
        section2.setFont(QFont("Arial", 10, QFont.Bold))
        section2.setStyleSheet("""
            QGroupBox {
                border: 2px solid #e67e22;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                color: #e67e22;
            }
        """)
        section2_layout = QVBoxLayout()

        # Stats
        stats2_layout = QHBoxLayout()
        self.last_sync_label = QLabel("Last Sync: Never")
        self.changes_count_label = QLabel("Changes Detected: 0")
        self.changes_count_label.setStyleSheet("color: #e67e22; font-weight: bold;")

        stats2_layout.addWidget(self.last_sync_label)
        stats2_layout.addWidget(QLabel("|"))
        stats2_layout.addWidget(self.changes_count_label)
        stats2_layout.addStretch()
        section2_layout.addLayout(stats2_layout)

        # Buttons
        buttons2_layout = QHBoxLayout()

        check_changes_btn = QPushButton("🔍 Check Changes")
        check_changes_btn.setMinimumHeight(40)
        check_changes_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        check_changes_btn.clicked.connect(self.check_stage_changes)
        buttons2_layout.addWidget(check_changes_btn)

        sync_changes_btn = QPushButton("🔄 Sync to Database")
        sync_changes_btn.setMinimumHeight(40)
        sync_changes_btn.setStyleSheet("""
            QPushButton {
                background-color: #e67e22;
                color: white;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #d35400;
            }
        """)
        sync_changes_btn.clicked.connect(self.sync_stage_changes)
        buttons2_layout.addWidget(sync_changes_btn)

        section2_layout.addLayout(buttons2_layout)
        section2.setLayout(section2_layout)
        layout.addWidget(section2)

        # ========== SECTION 3: Clean Duplicates ==========
        section3 = QGroupBox("🗑️ CLEAN DUPLICATES")
        section3.setFont(QFont("Arial", 10, QFont.Bold))
        section3.setStyleSheet("""
            QGroupBox {
                border: 2px solid #e74c3c;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                color: #e74c3c;
            }
        """)
        section3_layout = QVBoxLayout()

        # Stats
        stats3_layout = QHBoxLayout()
        self.db_dupes_label = QLabel("Database Duplicates: 0")
        self.pd_dupes_label = QLabel("Pipedrive Duplicates: 0")

        stats3_layout.addWidget(self.db_dupes_label)
        stats3_layout.addWidget(QLabel("|"))
        stats3_layout.addWidget(self.pd_dupes_label)
        stats3_layout.addStretch()
        section3_layout.addLayout(stats3_layout)

        # Buttons
        buttons3_layout = QHBoxLayout()

        find_dupes_btn = QPushButton("🔍 Find Duplicates")
        find_dupes_btn.setMinimumHeight(40)
        find_dupes_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        find_dupes_btn.clicked.connect(self.find_duplicates)
        buttons3_layout.addWidget(find_dupes_btn)

        remove_dupes_btn = QPushButton("🗑️ Remove Duplicates")
        remove_dupes_btn.setMinimumHeight(40)
        remove_dupes_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        remove_dupes_btn.clicked.connect(self.remove_duplicates)
        buttons3_layout.addWidget(remove_dupes_btn)

        section3_layout.addLayout(buttons3_layout)
        section3.setLayout(section3_layout)
        layout.addWidget(section3)

        # ========== SECTION 4: Full Sync from Pipedrive ==========
        section4 = QGroupBox("🔄 FULL SYNC FROM PIPEDRIVE")
        section4.setFont(QFont("Arial", 10, QFont.Bold))
        section4.setStyleSheet("""
            QGroupBox {
                border: 2px solid #27ae60;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                color: #27ae60;
            }
        """)
        section4_layout = QVBoxLayout()

        # Description
        desc_label = QLabel("⚠️ This will clear all database tables and re-sync everything from Pipedrive")
        desc_label.setStyleSheet("color: #e67e22; font-weight: bold;")
        section4_layout.addWidget(desc_label)

        # Stats
        stats4_layout = QHBoxLayout()
        self.full_sync_status_label = QLabel("Status: Ready")
        self.full_sync_count_label = QLabel("Last Sync: Never")

        stats4_layout.addWidget(self.full_sync_status_label)
        stats4_layout.addWidget(QLabel("|"))
        stats4_layout.addWidget(self.full_sync_count_label)
        stats4_layout.addStretch()
        section4_layout.addLayout(stats4_layout)

        # Button
        full_sync_btn = QPushButton("🔄 FULL SYNC FROM PIPEDRIVE")
        full_sync_btn.setMinimumHeight(50)
        full_sync_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        full_sync_btn.clicked.connect(self.full_sync_from_pipedrive)
        section4_layout.addWidget(full_sync_btn)

        section4.setLayout(section4_layout)
        layout.addWidget(section4)

        # ========== SYNC LOG ==========
        log_group = QGroupBox("📋 SYNC LOG")
        log_group.setFont(QFont("Arial", 10, QFont.Bold))
        log_layout = QVBoxLayout()

        self.sync_log = QTextEdit()
        self.sync_log.setReadOnly(True)
        self.sync_log.setMaximumHeight(200)
        self.sync_log.setStyleSheet("""
            QTextEdit {
                background-color: #2c3e50;
                color: #ecf0f1;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
            }
        """)
        log_layout.addWidget(self.sync_log)

        # Clear log button
        clear_log_btn = QPushButton("🗑️ Clear Log")
        clear_log_btn.clicked.connect(lambda: self.sync_log.clear())
        log_layout.addWidget(clear_log_btn)

        log_group.setLayout(log_layout)
        layout.addWidget(log_group)

        self.sync_tab.setLayout(layout)

    # ========== SCRAPER TAB METHODS ==========

    def start_scraping(self):
        """Start the scraping process"""
        try:
            # Disable start button, enable stop button
            self.start_scraper_btn.setEnabled(False)
            self.stop_scraper_btn.setEnabled(True)

            # Clear log
            self.scraper_log.clear()

            # Reset progress
            self.scraper_progress.setValue(0)

            # Get settings
            max_properties = self.max_properties_spin.value()
            delay_seconds = self.delay_spin.value()
            batch_size = self.batch_size_spin.value()

            # Update status
            self.scraper_status_label.setText(f"Status: Running (0/{max_properties})")
            self.scraper_status_label.setStyleSheet("font-size: 12px; color: #f39c12; font-weight: bold;")

            # Create and start worker thread
            self.scraper_worker = ScraperWorker(
                max_properties=max_properties,
                delay_seconds=delay_seconds,
                batch_size=batch_size
            )

            # Connect signals
            self.scraper_worker.log_signal.connect(self.append_scraper_log)
            self.scraper_worker.progress_signal.connect(self.update_scraper_progress)
            self.scraper_worker.status_signal.connect(self.update_scraper_status)
            self.scraper_worker.finished_signal.connect(self.scraping_finished)

            # Start thread
            self.scraper_worker.start()

            self.append_scraper_log("✅ Scraper started successfully!")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start scraper: {str(e)}")
            self.start_scraper_btn.setEnabled(True)
            self.stop_scraper_btn.setEnabled(False)

    def stop_scraping(self):
        """Stop the scraping process"""
        if self.scraper_worker and self.scraper_worker.isRunning():
            self.append_scraper_log("\n⏸️ Stopping scraper...")
            self.scraper_worker.stop()
            self.scraper_worker.wait()  # Wait for thread to finish

            self.scraper_status_label.setText("Status: Stopped by user")
            self.scraper_status_label.setStyleSheet("font-size: 12px; color: #e74c3c; font-weight: bold;")

            self.start_scraper_btn.setEnabled(True)
            self.stop_scraper_btn.setEnabled(False)

    def append_scraper_log(self, message):
        """Append message to scraper log"""
        self.scraper_log.append(message)
        # Auto-scroll to bottom
        scrollbar = self.scraper_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def clear_scraper_log(self):
        """Clear the scraper log terminal"""
        self.scraper_log.clear()
        self.append_scraper_log("🧹 Terminal cleared!")

    def update_scraper_progress(self, current, total):
        """Update progress bar"""
        if total > 0:
            percentage = int((current / total) * 100)
            self.scraper_progress.setValue(percentage)
            self.scraper_progress.setFormat(f"{current}/{total} properties ({percentage}%)")

            # Update status label
            self.scraper_status_label.setText(f"Status: Running ({current}/{total})")

    def update_scraper_status(self, status):
        """Update status label"""
        self.scraper_status_label.setText(f"Status: {status}")

    def scraping_finished(self, stats):
        """Handle scraping completion"""
        # Re-enable buttons
        self.start_scraper_btn.setEnabled(True)
        self.stop_scraper_btn.setEnabled(False)

        if stats.get('success'):
            # Update status
            self.scraper_status_label.setText("Status: Complete ✅")
            self.scraper_status_label.setStyleSheet("font-size: 12px; color: #27ae60; font-weight: bold;")

            # Set progress to 100%
            self.scraper_progress.setValue(100)

            # Show summary message
            summary = f"""
Scraping Complete!

📊 Total Properties Scraped: {stats.get('total_scraped', 0)}
💾 Saved to CSV: {stats.get('saved_csv', 0)}
🗄️ Saved to Database: {stats.get('saved_db', 0)}
📤 Uploaded to Pipedrive: {stats.get('uploaded_pd', 0)}
⏭️ Duplicates Skipped: {stats.get('duplicates', 0)}
❌ Errors: {stats.get('errors', 0)}
"""
            QMessageBox.information(self, "Scraping Complete", summary)

            # Reload properties table
            self.load_properties()

        else:
            # Update status
            self.scraper_status_label.setText("Status: Error ❌")
            self.scraper_status_label.setStyleSheet("font-size: 12px; color: #e74c3c; font-weight: bold;")

            # Show error message
            error_msg = stats.get('error', 'Unknown error')
            QMessageBox.critical(self, "Scraping Error", f"Scraping failed:\n{error_msg}")

    # ========== HELPER METHODS ==========

    def set_loading_cursor(self, loading=True):
        """Set loading cursor (waiting cursor) when processing"""
        if loading:
            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        else:
            QApplication.restoreOverrideCursor()

    # ========== PROPERTIES TAB METHODS ==========

    def load_properties(self):
        """Load properties from database"""
        self.set_loading_cursor(True)  # Show loading cursor
        try:
            # Get selected stage
            stage_display = self.status_combo.currentText()
            stage_table = [k for k, v in STAGE_MAPPING.items() if v == stage_display][0]

            # Get selected property type
            property_type = self.property_type_combo.currentText()

            # Connect to database
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Fetch properties with property_type filter
            if property_type == "All":
                cursor.execute(f'''
                    SELECT deal_id, address, beds, baths, sqft, price,
                           property_type, agent_name, agent_phone, person_id, synced_at
                    FROM {stage_table}
                    ORDER BY synced_at DESC
                ''')
            else:
                cursor.execute(f'''
                    SELECT deal_id, address, beds, baths, sqft, price,
                           property_type, agent_name, agent_phone, person_id, synced_at
                    FROM {stage_table}
                    WHERE property_type = ?
                    ORDER BY synced_at DESC
                ''', (property_type,))

            rows = cursor.fetchall()
            conn.close()

            # Update table - optimized with batch updates
            self.properties_table.setUpdatesEnabled(False)  # Disable updates during load
            self.properties_table.setRowCount(len(rows))

            for i, row in enumerate(rows):
                for j, value in enumerate(row):
                    item = QTableWidgetItem(str(value) if value else '')
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # Read-only
                    self.properties_table.setItem(i, j, item)

            self.properties_table.setUpdatesEnabled(True)  # Re-enable updates

            # Update stats
            self.stats_label.setText(f"Total Properties: {len(rows)}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load properties:\n{str(e)}")
        finally:
            self.set_loading_cursor(False)  # Hide loading cursor

    def filter_properties(self):
        """Filter properties based on search"""
        search_text = self.search_input.text().lower()

        for i in range(self.properties_table.rowCount()):
            show_row = False

            for j in range(self.properties_table.columnCount()):
                item = self.properties_table.item(i, j)
                if item and search_text in item.text().lower():
                    show_row = True
                    break

            self.properties_table.setRowHidden(i, not show_row)

    def show_property_details(self):
        """Show selected property details"""
        selected_rows = self.properties_table.selectedItems()
        if not selected_rows:
            return

        row = selected_rows[0].row()

        deal_id = self.properties_table.item(row, 0).text()
        address = self.properties_table.item(row, 1).text()
        beds = self.properties_table.item(row, 2).text()
        baths = self.properties_table.item(row, 3).text()
        sqft = self.properties_table.item(row, 4).text()
        price = self.properties_table.item(row, 5).text()
        property_type = self.properties_table.item(row, 6).text()
        agent = self.properties_table.item(row, 7).text()
        phone = self.properties_table.item(row, 8).text()
        person_id = self.properties_table.item(row, 9).text()

        details = f"""
<b>Deal ID:</b> {deal_id}<br>
<b>Address:</b> {address}<br>
<b>Beds:</b> {beds} | <b>Baths:</b> {baths} | <b>Sqft:</b> {sqft}<br>
<b>Price:</b> {price}<br>
<b>Property Type:</b> <span style="color: #e67e22; font-weight: bold;">{property_type}</span><br>
<b>Agent:</b> {agent}<br>
<b>Phone:</b> {phone}<br>
<b>Person ID:</b> {person_id}
        """

        self.details_text.setHtml(details)

    def update_property(self):
        """Update selected property in database"""
        selected_rows = self.properties_table.selectionModel().selectedRows()

        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select a property to update.")
            return

        row = selected_rows[0].row()
        deal_id = self.properties_table.item(row, 0).text()

        # Get current values
        current_address = self.properties_table.item(row, 1).text()
        current_beds = self.properties_table.item(row, 2).text()
        current_baths = self.properties_table.item(row, 3).text()
        current_sqft = self.properties_table.item(row, 4).text()
        current_price = self.properties_table.item(row, 5).text()
        current_type = self.properties_table.item(row, 6).text()
        current_agent = self.properties_table.item(row, 7).text()
        current_phone = self.properties_table.item(row, 8).text()

        # Create dialog for editing
        from PyQt5.QtWidgets import QDialog, QFormLayout, QDialogButtonBox

        dialog = QDialog(self)
        dialog.setWindowTitle("Update Property")
        dialog.setMinimumWidth(500)

        layout = QFormLayout()

        # Create input fields
        address_input = QLineEdit(current_address)
        beds_input = QLineEdit(current_beds)
        baths_input = QLineEdit(current_baths)
        sqft_input = QLineEdit(current_sqft)
        price_input = QLineEdit(current_price)
        type_input = QLineEdit(current_type)
        agent_input = QLineEdit(current_agent)
        phone_input = QLineEdit(current_phone)

        layout.addRow("Address:", address_input)
        layout.addRow("Beds:", beds_input)
        layout.addRow("Baths:", baths_input)
        layout.addRow("Sqft:", sqft_input)
        layout.addRow("Price:", price_input)
        layout.addRow("Property Type:", type_input)
        layout.addRow("Agent Name:", agent_input)
        layout.addRow("Agent Phone:", phone_input)

        # Add buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)

        dialog.setLayout(layout)

        if dialog.exec_() == QDialog.Accepted:
            try:
                # Get current stage
                stage_display = self.status_combo.currentText()
                stage_table = [k for k, v in STAGE_MAPPING.items() if v == stage_display][0]

                # Update database
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()

                cursor.execute(f'''
                    UPDATE {stage_table}
                    SET address = ?, beds = ?, baths = ?, sqft = ?, price = ?,
                        property_type = ?, agent_name = ?, agent_phone = ?
                    WHERE deal_id = ?
                ''', (
                    address_input.text(),
                    beds_input.text(),
                    baths_input.text(),
                    sqft_input.text(),
                    price_input.text(),
                    type_input.text(),
                    agent_input.text(),
                    phone_input.text(),
                    deal_id
                ))

                conn.commit()
                conn.close()

                QMessageBox.information(self, "Success", "Property updated successfully!")
                self.load_properties()

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to update property:\n{str(e)}")

    def delete_property(self):
        """Delete selected property from database"""
        selected_rows = self.properties_table.selectionModel().selectedRows()

        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select a property to delete.")
            return

        row = selected_rows[0].row()
        deal_id = self.properties_table.item(row, 0).text()
        address = self.properties_table.item(row, 1).text()

        # Confirm deletion
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete this property?\n\n{address}",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                # Get current stage
                stage_display = self.status_combo.currentText()
                stage_table = [k for k, v in STAGE_MAPPING.items() if v == stage_display][0]

                # Delete from database
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()

                cursor.execute(f'DELETE FROM {stage_table} WHERE deal_id = ?', (deal_id,))

                conn.commit()
                conn.close()

                QMessageBox.information(self, "Success", "Property deleted successfully!")
                self.load_properties()

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete property:\n{str(e)}")

    def export_properties(self):
        """Export properties to CSV"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Properties", "", "CSV Files (*.csv)"
        )

        if not file_path:
            return

        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)

                # Write headers
                headers = []
                for j in range(self.properties_table.columnCount()):
                    headers.append(self.properties_table.horizontalHeaderItem(j).text())
                writer.writerow(headers)

                # Write data
                for i in range(self.properties_table.rowCount()):
                    if not self.properties_table.isRowHidden(i):
                        row_data = []
                        for j in range(self.properties_table.columnCount()):
                            item = self.properties_table.item(i, j)
                            row_data.append(item.text() if item else '')
                        writer.writerow(row_data)

            QMessageBox.information(self, "Success", f"Exported to:\n{file_path}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export:\n{str(e)}")

    def open_in_browser(self):
        """Open property in browser"""
        QMessageBox.information(self, "Info", "Browser functionality coming soon!")

    def create_or_find_person(self, agent_name, agent_phone, property_address):
        """Create or find person in Pipedrive"""
        try:
            # Search for existing person by phone
            if agent_phone:
                r = requests.get(
                    f"{PIPEDRIVE_API_URL}/persons/search",
                    params={
                        'api_token': PIPEDRIVE_API_TOKEN,
                        'term': agent_phone,
                        'fields': 'phone'
                    },
                    timeout=30
                )

                if r.status_code == 200:
                    results = r.json().get('data', {}).get('items', [])
                    if results:
                        person_id = results[0].get('item', {}).get('id')
                        self.log(f"   Found existing person: {person_id}")
                        return person_id

            # Create new person
            person_data = {
                'name': agent_name,
                'phone': [{'value': agent_phone, 'primary': True}] if agent_phone else [],
                'e1e3aea16d6dd6827c567816d150a0567c54449c': property_address  # Address custom field
            }

            r = requests.post(
                f"{PIPEDRIVE_API_URL}/persons",
                params={'api_token': PIPEDRIVE_API_TOKEN},
                json=person_data,
                timeout=30
            )

            if r.status_code == 201:
                person_id = r.json().get('data', {}).get('id')
                self.log(f"   Created new person: {person_id}")
                return person_id
            else:
                self.log(f"   ❌ Failed to create person: {r.status_code}")
                return None

        except Exception as e:
            self.log(f"   ❌ Error creating person: {str(e)}")
            return None

    def create_deal_with_details(self, address, price, beds, baths, sqft,
                                  property_type, agent_name, agent_phone,
                                  person_id, url):
        """Create deal in Pipedrive with all details"""
        try:
            # Clean price (remove $ and commas)
            price_value = price.replace('$', '').replace(',', '').strip()
            try:
                price_value = float(price_value)
            except:
                price_value = 0

            # Create deal
            deal_data = {
                'title': address,
                'value': price_value,
                'currency': 'USD',
                'person_id': person_id,
                'stage_id': 101,  # Lead In stage
                '2ad561ae448ea1e1cdfa03632d7b579b7aca0c46': agent_name,  # Agent Name custom field
                'e21efd113e42560cb52b1f3d62ec046158477c4e': agent_phone  # Agent Phone custom field
            }

            r = requests.post(
                f"{PIPEDRIVE_API_URL}/deals",
                params={'api_token': PIPEDRIVE_API_TOKEN},
                json=deal_data,
                timeout=30
            )

            if r.status_code == 201:
                deal_id = r.json().get('data', {}).get('id')
                return deal_id
            else:
                self.log(f"   ❌ Failed to create deal: {r.status_code}")
                return None

        except Exception as e:
            self.log(f"   ❌ Error creating deal: {str(e)}")
            return None

    def create_deal_note(self, deal_id, address, price, beds, baths, sqft,
                         property_type, agent_name, agent_phone, url):
        """Create formatted note for deal"""
        try:
            from datetime import datetime

            # Create formatted note
            note_content = f"""🏠 PROPERTY DETAILS
📍 Address: {address}
💰 Price: {price}
🛏️ Beds: {beds}bd | 🛁 Baths: {baths}ba | 📐 Sqft: {sqft}sqft

👤 Agent: {agent_name}
📞 Agent Phone: {agent_phone}

🔗 Property URL: {url if url else 'N/A'}
📋 Scraped From: {property_type}

📅 Added: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""

            note_data = {
                'content': note_content,
                'deal_id': deal_id
            }

            r = requests.post(
                f"{PIPEDRIVE_API_URL}/notes",
                params={'api_token': PIPEDRIVE_API_TOKEN},
                json=note_data,
                timeout=30
            )

            if r.status_code == 201:
                return True
            else:
                self.log(f"   ❌ Failed to create note: {r.status_code}")
                return False

        except Exception as e:
            self.log(f"   ❌ Error creating note: {str(e)}")
            return False

    # ========== CSV TAB METHODS ==========

    def load_csv(self):
        """Load CSV file"""
        self.set_loading_cursor(True)  # Show loading cursor
        try:
            with open(CSV_PATH, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                data = list(reader)

            if not data:
                return

            # Set table
            self.csv_table.setRowCount(len(data) - 1)
            self.csv_table.setColumnCount(len(data[0]))
            self.csv_table.setHorizontalHeaderLabels(data[0])

            # Fill data
            for i, row in enumerate(data[1:]):
                for j, value in enumerate(row):
                    self.csv_table.setItem(i, j, QTableWidgetItem(value))

            QMessageBox.information(self, "Success", f"Loaded {len(data)-1} rows from CSV")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load CSV:\n{str(e)}")
        finally:
            self.set_loading_cursor(False)  # Hide loading cursor

    def save_csv(self):
        """Save CSV file"""
        try:
            with open(CSV_PATH, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)

                # Write headers
                headers = []
                for j in range(self.csv_table.columnCount()):
                    headers.append(self.csv_table.horizontalHeaderItem(j).text())
                writer.writerow(headers)

                # Write data
                for i in range(self.csv_table.rowCount()):
                    row_data = []
                    for j in range(self.csv_table.columnCount()):
                        item = self.csv_table.item(i, j)
                        row_data.append(item.text() if item else '')
                    writer.writerow(row_data)

            QMessageBox.information(self, "Success", "CSV saved successfully!")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save CSV:\n{str(e)}")

    def create_csv_row(self):
        """Create new row in CSV"""
        from PyQt5.QtWidgets import QDialog, QFormLayout, QDialogButtonBox

        dialog = QDialog(self)
        dialog.setWindowTitle("Create New Row")
        dialog.setMinimumWidth(500)

        layout = QFormLayout()

        # Create input fields based on CSV headers
        inputs = {}
        if self.csv_table.columnCount() > 0:
            for j in range(self.csv_table.columnCount()):
                header = self.csv_table.horizontalHeaderItem(j).text()
                input_field = QLineEdit()
                inputs[header] = input_field
                layout.addRow(f"{header}:", input_field)
        else:
            QMessageBox.warning(self, "No Headers", "Please load CSV first!")
            return

        # Add buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)

        dialog.setLayout(layout)

        if dialog.exec_() == QDialog.Accepted:
            # Add new row to table
            row_position = self.csv_table.rowCount()
            self.csv_table.insertRow(row_position)

            for j, (header, input_field) in enumerate(inputs.items()):
                self.csv_table.setItem(row_position, j, QTableWidgetItem(input_field.text()))

            QMessageBox.information(self, "Success", "Row created! Don't forget to save CSV.")

    def update_csv_row(self):
        """Update selected row in CSV"""
        selected_rows = self.csv_table.selectionModel().selectedRows()

        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select a row to update.")
            return

        row = selected_rows[0].row()

        from PyQt5.QtWidgets import QDialog, QFormLayout, QDialogButtonBox

        dialog = QDialog(self)
        dialog.setWindowTitle("Update Row")
        dialog.setMinimumWidth(500)

        layout = QFormLayout()

        # Create input fields with current values
        inputs = {}
        for j in range(self.csv_table.columnCount()):
            header = self.csv_table.horizontalHeaderItem(j).text()
            current_value = self.csv_table.item(row, j).text() if self.csv_table.item(row, j) else ''
            input_field = QLineEdit(current_value)
            inputs[header] = input_field
            layout.addRow(f"{header}:", input_field)

        # Add buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)

        dialog.setLayout(layout)

        if dialog.exec_() == QDialog.Accepted:
            # Update row in table
            for j, (header, input_field) in enumerate(inputs.items()):
                self.csv_table.setItem(row, j, QTableWidgetItem(input_field.text()))

            QMessageBox.information(self, "Success", "Row updated! Don't forget to save CSV.")

    def delete_csv_row(self):
        """Delete selected row from CSV"""
        selected_rows = self.csv_table.selectionModel().selectedRows()

        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select a row to delete.")
            return

        row = selected_rows[0].row()

        # Get first column value for confirmation
        first_col_value = self.csv_table.item(row, 0).text() if self.csv_table.item(row, 0) else "this row"

        # Confirm deletion
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete row {row + 1}?\n\n{first_col_value}",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.csv_table.removeRow(row)
            QMessageBox.information(self, "Success", "Row deleted! Don't forget to save CSV.")

    # ========== SYNC TAB METHODS ==========

    def log(self, message):
        """Add message to sync log with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.sync_log.append(f"[{timestamp}] {message}")

    def check_new_properties(self):
        """Check for new properties in database that don't exist in Pipedrive"""
        self.log("🔍 Checking for new properties...")
        self.set_loading_cursor(True)  # Show loading cursor

        try:
            import requests
            from requests.exceptions import ConnectionError, Timeout, RequestException

            API = "d43b4e8b2f06c9ccee9c7eefe6fbfcef4c9f2fe1"
            URL = "https://api.pipedrive.com/v1"

            # Get all deals from Pipedrive
            self.log("📥 Fetching deals from Pipedrive...")
            all_deals = []
            start = 0
            limit = 500

            while True:
                try:
                    r = requests.get(
                        f"{URL}/deals",
                        params={
                            'api_token': API,
                            'pipeline_id': 9,  # On Market
                            'start': start,
                            'limit': limit,
                            'status': 'all_not_deleted'
                        },
                        timeout=30
                    )
                except (ConnectionError, Timeout) as e:
                    self.log("❌ Internet connection error!")
                    QMessageBox.critical(
                        self,
                        "Connection Error",
                        "⚠️ Internet Connection Error!\n\n"
                        "Please check your internet connection and try again.\n\n"
                        "Details: Connection to Pipedrive API timed out."
                    )
                    return

                data = r.json().get('data', [])
                if not data:
                    break

                all_deals.extend(data)

                if len(data) < limit:
                    break

                start += limit

            self.log(f"✅ Fetched {len(all_deals)} deals from Pipedrive")

            # Get all properties from database
            self.log("📥 Fetching properties from database...")
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Get all deal IDs from database
            db_deal_ids = set()
            for table in STAGE_MAPPING.keys():
                cursor.execute(f'SELECT deal_id FROM {table}')
                rows = cursor.fetchall()
                db_deal_ids.update([row[0] for row in rows])

            conn.close()

            self.log(f"✅ Found {len(db_deal_ids)} properties in database")

            # Get Pipedrive deal IDs
            pd_deal_ids = set([deal['id'] for deal in all_deals])

            # Find new properties (in database but not in Pipedrive)
            new_properties = db_deal_ids - pd_deal_ids

            # Update labels
            self.db_count_label.setText(f"Database Properties: {len(db_deal_ids)}")
            self.pd_count_label.setText(f"Pipedrive Deals: {len(pd_deal_ids)}")
            self.new_count_label.setText(f"New Properties: {len(new_properties)}")

            if new_properties:
                self.log(f"✅ Found {len(new_properties)} new properties to upload")
                self.log(f"   Deal IDs: {list(new_properties)[:10]}...")
            else:
                self.log("✅ No new properties found. Database and Pipedrive are in sync!")

        except Exception as e:
            self.log(f"❌ Error: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to check new properties:\n{str(e)}")

    def upload_new_to_pipedrive(self):
        """Upload new properties from database to Pipedrive"""
        self.log("📤 Upload functionality coming soon...")
        self.log("   This will create new deals in Pipedrive with:")
        self.log("   • Deal title (address + price)")
        self.log("   • Notes (property details)")
        self.log("   • Agent Name custom field")
        self.log("   • Agent Phone custom field")
        self.log("   • Person record (auto-create)")
        QMessageBox.information(self, "Info", "Upload functionality will be implemented next!")

    def check_stage_changes(self):
        """Check for stage changes in Pipedrive"""
        self.log("🔍 Checking for stage changes...")
        self.set_loading_cursor(True)  # Show loading cursor

        try:
            import requests
            from requests.exceptions import ConnectionError, Timeout, RequestException

            API = "d43b4e8b2f06c9ccee9c7eefe6fbfcef4c9f2fe1"
            URL = "https://api.pipedrive.com/v1"

            # Get all deals from Pipedrive
            self.log("📥 Fetching deals from Pipedrive...")
            all_deals = []
            start = 0
            limit = 500

            while True:
                try:
                    r = requests.get(
                        f"{URL}/deals",
                        params={
                            'api_token': API,
                            'pipeline_id': 9,
                            'start': start,
                            'limit': limit,
                            'status': 'all_not_deleted'
                        },
                        timeout=30
                    )
                except (ConnectionError, Timeout) as e:
                    self.log("❌ Internet connection error!")
                    QMessageBox.critical(
                        self,
                        "Connection Error",
                        "⚠️ Internet Connection Error!\n\n"
                        "Please check your internet connection and try again.\n\n"
                        "Details: Connection to Pipedrive API timed out."
                    )
                    return

                data = r.json().get('data', [])
                if not data:
                    break

                all_deals.extend(data)

                if len(data) < limit:
                    break

                start += limit

            self.log(f"✅ Fetched {len(all_deals)} deals from Pipedrive")

            # Check database for each deal
            self.log("🔍 Comparing with database...")
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            changes = []

            # Use the same stage mapping as defined at top of file
            stage_id_to_table = STAGE_ID_TO_TABLE

            for deal in all_deals:
                deal_id = deal['id']
                pipedrive_stage_id = deal.get('stage_id')
                pipedrive_table = stage_id_to_table.get(pipedrive_stage_id)

                if not pipedrive_table:
                    continue

                # Find deal in database
                found_in_table = None
                for table in STAGE_MAPPING.keys():
                    cursor.execute(f'SELECT deal_id FROM {table} WHERE deal_id = ?', (deal_id,))
                    if cursor.fetchone():
                        found_in_table = table
                        break

                # If found in different table, it's a change
                if found_in_table and found_in_table != pipedrive_table:
                    changes.append({
                        'deal_id': deal_id,
                        'title': deal.get('title', ''),
                        'from_stage': found_in_table,
                        'to_stage': pipedrive_table
                    })

            conn.close()

            # Update labels
            self.changes_count_label.setText(f"Changes Detected: {len(changes)}")
            self.last_sync_label.setText(f"Last Check: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

            if changes:
                self.log(f"✅ Found {len(changes)} stage changes:")
                for change in changes[:5]:
                    self.log(f"   • Deal {change['deal_id']}: {STAGE_MAPPING[change['from_stage']]} → {STAGE_MAPPING[change['to_stage']]}")
                if len(changes) > 5:
                    self.log(f"   ... and {len(changes) - 5} more")
            else:
                self.log("✅ No stage changes detected. Database is in sync!")

        except Exception as e:
            self.log(f"❌ Error: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to check stage changes:\n{str(e)}")

    def sync_stage_changes(self):
        """Sync stage changes from Pipedrive to database"""
        self.log("🔄 Starting sync to database...")
        self.set_loading_cursor(True)  # Show loading cursor

        try:
            from requests.exceptions import ConnectionError, Timeout, RequestException

            # Fetch all deals from Pipedrive
            self.log("📥 Fetching deals from Pipedrive...")

            all_deals = []
            start = 0
            limit = 500

            while True:
                try:
                    r = requests.get(
                        f"{PIPEDRIVE_API_URL}/deals",
                        params={
                            'api_token': PIPEDRIVE_API_TOKEN,
                            'pipeline_id': PIPELINE_ID,
                            'start': start,
                            'limit': limit,
                            'status': 'all_not_deleted'
                        },
                        timeout=30
                    )
                except (ConnectionError, Timeout) as e:
                    self.log("❌ Internet connection error!")
                    QMessageBox.critical(
                        self,
                        "Connection Error",
                        "⚠️ Internet Connection Error!\n\n"
                        "Please check your internet connection and try again.\n\n"
                        "Details: Connection to Pipedrive API timed out."
                    )
                    return

                data = r.json().get('data', [])
                if not data:
                    break

                all_deals.extend(data)

                if len(data) < limit:
                    break

                start += limit

            self.log(f"✅ Fetched {len(all_deals)} deals from Pipedrive")
            self.log("🔄 Syncing stage changes...")

            # Connect to database
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            synced_count = 0
            moved_count = 0

            # Process each deal
            for deal in all_deals:
                deal_id = deal['id']
                stage_id = deal.get('stage_id')

                if not stage_id or stage_id not in STAGE_ID_TO_TABLE:
                    continue

                # Get target table from stage ID
                target_table = STAGE_ID_TO_TABLE[stage_id]

                # Find current table (where deal currently exists in database)
                current_table = None
                for table in STAGE_MAPPING.keys():
                    try:
                        cursor.execute(f'SELECT COUNT(*) FROM {table} WHERE deal_id = ?', (deal_id,))
                        if cursor.fetchone()[0] > 0:
                            current_table = table
                            break
                    except:
                        continue

                # If deal needs to move
                if current_table and current_table != target_table:
                    # Get deal data from current table (excluding id column)
                    cursor.execute(f'''
                        SELECT deal_id, address, beds, baths, sqft, price, property_type,
                               agent_name, agent_phone, person_id, synced_at
                        FROM {current_table} WHERE deal_id = ?
                    ''', (deal_id,))
                    deal_data = cursor.fetchone()

                    if deal_data:
                        # Delete from current table
                        cursor.execute(f'DELETE FROM {current_table} WHERE deal_id = ?', (deal_id,))

                        # Insert into target table
                        cursor.execute(f'''
                            INSERT OR REPLACE INTO {target_table}
                            (deal_id, address, beds, baths, sqft, price, property_type,
                             agent_name, agent_phone, person_id, synced_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', deal_data)

                        moved_count += 1
                        if moved_count <= 10:  # Show first 10
                            self.log(f"   ✅ Deal {deal_id}: {STAGE_MAPPING[current_table]} → {STAGE_MAPPING[target_table]}")

                synced_count += 1

            if moved_count > 10:
                self.log(f"   ... and {moved_count - 10} more")

            conn.commit()
            conn.close()

            self.log(f"\n🎉 Sync Complete!")
            self.log(f"   • Total deals processed: {synced_count}")
            self.log(f"   • Deals moved: {moved_count}")
            self.log(f"   • Database is now synced with Pipedrive!")

            # Update stats
            self.last_sync_label.setText(f"Last Sync: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.changes_count_label.setText(f"Changes Detected: 0")

            QMessageBox.information(self, "Success", f"Synced {moved_count} stage changes to database!")

        except Exception as e:
            self.log(f"❌ Error: {str(e)}")
            import traceback
            self.log(traceback.format_exc())
            QMessageBox.critical(self, "Error", f"Failed to sync stage changes:\n{str(e)}")
        finally:
            self.set_loading_cursor(False)  # Hide loading cursor

    def full_sync_from_pipedrive(self):
        """Full sync from Pipedrive - clear all tables and re-sync everything"""
        # Show confirmation dialog
        reply = QMessageBox.question(
            self,
            "Confirm Full Sync",
            "⚠️ WARNING: This will clear ALL database tables and re-sync everything from Pipedrive!\n\n"
            "This action will:\n"
            "• Delete all data from all 10 database tables\n"
            "• Fetch all deals from Pipedrive\n"
            "• Re-sync everything to database\n\n"
            "Are you sure you want to continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            self.log("❌ Full sync cancelled by user")
            return

        self.log("🔄 Starting FULL SYNC from Pipedrive...")
        self.full_sync_status_label.setText("Status: Syncing...")
        self.set_loading_cursor(True)  # Show loading cursor

        try:
            from requests.exceptions import ConnectionError, Timeout

            # Step 1: Fetch all deals from Pipedrive
            self.log("📥 Step 1/3: Fetching all deals from Pipedrive...")

            all_deals = []
            start = 0
            limit = 500

            while True:
                try:
                    r = requests.get(
                        f"{PIPEDRIVE_API_URL}/deals",
                        params={
                            'api_token': PIPEDRIVE_API_TOKEN,
                            'pipeline_id': PIPELINE_ID,
                            'start': start,
                            'limit': limit,
                            'status': 'all_not_deleted'
                        },
                        timeout=30
                    )
                except (ConnectionError, Timeout) as e:
                    self.log("❌ Internet connection error!")
                    self.full_sync_status_label.setText("Status: Failed")
                    QMessageBox.critical(
                        self,
                        "Connection Error",
                        "⚠️ Internet Connection Error!\n\n"
                        "Please check your internet connection and try again."
                    )
                    return

                data = r.json().get('data', [])
                if not data:
                    break

                all_deals.extend(data)
                self.log(f"   Fetched {len(all_deals)} deals...")

                if len(data) < limit:
                    break

                start += limit

            self.log(f"✅ Fetched {len(all_deals)} total deals from Pipedrive")

            # Step 2: Clear all database tables
            self.log("\n🗑️ Step 2/3: Clearing all database tables...")

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            for table in STAGE_MAPPING.keys():
                try:
                    cursor.execute(f"DELETE FROM {table}")
                    self.log(f"   ✅ Cleared {table}")
                except Exception as e:
                    self.log(f"   ⚠️ Error clearing {table}: {str(e)}")

            conn.commit()
            self.log("✅ All tables cleared")

            # Step 3: Sync all deals to database
            self.log(f"\n📥 Step 3/3: Syncing {len(all_deals)} deals to database...")

            synced_count = 0
            skipped_count = 0
            error_count = 0
            by_table = {}

            for deal in all_deals:
                try:
                    deal_id = deal.get('id')
                    title = deal.get('title', 'N/A')
                    stage_id = deal.get('stage_id')
                    value = deal.get('value', 0)
                    person_id = deal.get('person_id', {})
                    if isinstance(person_id, dict):
                        person_id = person_id.get('value')

                    # Skip if not in our pipeline
                    if stage_id not in STAGE_ID_TO_TABLE:
                        skipped_count += 1
                        continue

                    # Get custom fields
                    agent_name = deal.get('e1e3aea16d6dd6827c567816d150a0567c54449c', 'N/A')
                    agent_phone = deal.get('4e0f8a4b4c6dd6827c567816d150a0567c54449c', 'N/A')
                    zillow_link = deal.get('a4e0f8a4b4c6dd6827c567816d150a0567c54449c', 'N/A')

                    table = STAGE_ID_TO_TABLE[stage_id]

                    cursor.execute(f"""
                        INSERT INTO {table}
                        (deal_id, address, price, agent_name, agent_phone, url, person_id, synced_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
                    """, (deal_id, title, value, agent_name, agent_phone, zillow_link, person_id))

                    synced_count += 1
                    by_table[table] = by_table.get(table, 0) + 1

                except Exception as e:
                    error_count += 1
                    if error_count <= 5:  # Show first 5 errors
                        self.log(f"   ❌ Error syncing deal {deal_id}: {str(e)}")

            if error_count > 5:
                self.log(f"   ... and {error_count - 5} more errors")

            conn.commit()
            conn.close()

            # Log results
            self.log(f"\n🎉 FULL SYNC COMPLETE!")
            self.log(f"   • Total deals: {len(all_deals)}")
            self.log(f"   • Synced: {synced_count}")
            self.log(f"   • Skipped: {skipped_count}")
            self.log(f"   • Errors: {error_count}")
            self.log(f"\n📋 By Table:")
            for table, count in sorted(by_table.items()):
                self.log(f"   • {STAGE_MAPPING[table]}: {count}")

            # Update UI labels
            self.full_sync_status_label.setText("Status: Complete ✅")
            self.full_sync_count_label.setText(f"Last Sync: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ({synced_count} deals)")

            # Refresh properties tab
            self.load_properties()

            QMessageBox.information(
                self,
                "Success",
                f"✅ Full Sync Complete!\n\n"
                f"• Synced: {synced_count} deals\n"
                f"• Skipped: {skipped_count}\n"
                f"• Errors: {error_count}\n\n"
                f"Database is now fully synced with Pipedrive!"
            )

        except Exception as e:
            self.log(f"❌ Error: {str(e)}")
            import traceback
            self.log(traceback.format_exc())
            self.full_sync_status_label.setText("Status: Failed ❌")
            QMessageBox.critical(self, "Error", f"Failed to complete full sync:\n{str(e)}")
        finally:
            self.set_loading_cursor(False)  # Hide loading cursor

    def find_duplicates(self):
        """Find duplicate properties"""
        self.log("🔍 Finding duplicates...")

        try:
            # Check database duplicates
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            db_duplicates = []

            # Check for duplicate addresses across all tables
            all_addresses = []
            for table in STAGE_MAPPING.keys():
                cursor.execute(f'SELECT deal_id, address FROM {table}')
                rows = cursor.fetchall()
                all_addresses.extend([(row[0], row[1], table) for row in rows])

            # Find duplicates
            address_counts = {}
            for deal_id, address, table in all_addresses:
                if address not in address_counts:
                    address_counts[address] = []
                address_counts[address].append((deal_id, table))

            for address, deals in address_counts.items():
                if len(deals) > 1:
                    db_duplicates.append(address)

            conn.close()

            # Update labels
            self.db_dupes_label.setText(f"Database Duplicates: {len(db_duplicates)}")
            self.pd_dupes_label.setText(f"Pipedrive Duplicates: 0 (check manually)")

            if db_duplicates:
                self.log(f"⚠️ Found {len(db_duplicates)} duplicate addresses in database:")
                for addr in db_duplicates[:5]:
                    self.log(f"   • {addr}")
                if len(db_duplicates) > 5:
                    self.log(f"   ... and {len(db_duplicates) - 5} more")
            else:
                self.log("✅ No duplicates found in database!")

        except Exception as e:
            self.log(f"❌ Error: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to find duplicates:\n{str(e)}")

    def remove_duplicates(self):
        """Remove duplicate properties from database and Pipedrive"""
        self.log("🗑️ Starting duplicate removal...")
        self.set_loading_cursor(True)  # Show loading cursor

        try:
            # First, find duplicates
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Database duplicates
            db_duplicates = []
            all_addresses = []

            for table in STAGE_MAPPING.keys():
                cursor.execute(f'SELECT deal_id, LOWER(TRIM(address)) as addr FROM {table}')
                rows = cursor.fetchall()
                all_addresses.extend([(row[0], row[1], table) for row in rows])

            # Find duplicate addresses
            from collections import Counter
            address_counts = Counter([addr[1] for addr in all_addresses])
            duplicate_addresses = {addr: count for addr, count in address_counts.items() if count > 1}

            if duplicate_addresses:
                self.log(f"\n📊 Found {len(duplicate_addresses)} duplicate addresses in database")

                # Ask for confirmation
                reply = QMessageBox.question(
                    self,
                    "Confirm Removal",
                    f"⚠️ Found {len(duplicate_addresses)} duplicate addresses in database.\n\n"
                    f"This will keep the latest version and remove older duplicates.\n\n"
                    f"Do you want to proceed?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )

                if reply == QMessageBox.Yes:
                    removed_count = 0

                    for dup_addr in duplicate_addresses:
                        # Get all deals with this address
                        deals_with_addr = [(deal_id, table) for deal_id, addr, table in all_addresses if addr == dup_addr]

                        if len(deals_with_addr) > 1:
                            # Keep the first one (latest), remove others
                            keep_deal = deals_with_addr[0]
                            remove_deals = deals_with_addr[1:]

                            for deal_id, table in remove_deals:
                                cursor.execute(f'DELETE FROM {table} WHERE deal_id = ?', (deal_id,))
                                removed_count += 1
                                if removed_count <= 10:
                                    self.log(f"   ✅ Removed duplicate deal {deal_id} from {table}")

                    if removed_count > 10:
                        self.log(f"   ... and {removed_count - 10} more")

                    conn.commit()
                    self.log(f"\n✅ Removed {removed_count} duplicate deals from database")
                    self.db_dupes_label.setText(f"Database Duplicates: 0")
                else:
                    self.log("❌ Database duplicate removal cancelled")
            else:
                self.log("✅ No duplicates found in database")

            conn.close()

            # Pipedrive duplicates
            self.log("\n🔍 Checking Pipedrive for duplicates...")

            r = requests.get(
                f"{PIPEDRIVE_API_URL}/deals",
                params={
                    'api_token': PIPEDRIVE_API_TOKEN,
                    'pipeline_id': PIPELINE_ID,
                    'limit': 500,
                    'status': 'all_not_deleted'
                },
                timeout=30
            )

            all_deals = []
            data = r.json().get('data', [])
            all_deals.extend(data)

            # Get more pages if needed
            start = 500
            while len(data) == 500:
                r = requests.get(
                    f"{PIPEDRIVE_API_URL}/deals",
                    params={
                        'api_token': PIPEDRIVE_API_TOKEN,
                        'pipeline_id': PIPELINE_ID,
                        'start': start,
                        'limit': 500,
                        'status': 'all_not_deleted'
                    },
                    timeout=30
                )
                data = r.json().get('data', [])
                if not data:
                    break
                all_deals.extend(data)
                start += 500

            # Find Pipedrive duplicates
            pd_addresses = [(deal['id'], deal['title'].lower().strip()) for deal in all_deals]
            pd_address_counts = Counter([addr[1] for addr in pd_addresses])
            pd_duplicate_addresses = {addr: count for addr, count in pd_address_counts.items() if count > 1}

            if pd_duplicate_addresses:
                self.log(f"\n📊 Found {len(pd_duplicate_addresses)} duplicate addresses in Pipedrive")

                # Ask for confirmation
                reply = QMessageBox.question(
                    self,
                    "Confirm Pipedrive Removal",
                    f"⚠️ Found {len(pd_duplicate_addresses)} duplicate addresses in Pipedrive.\n\n"
                    f"This will keep the latest version and delete older duplicates from Pipedrive.\n\n"
                    f"Do you want to proceed?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )

                if reply == QMessageBox.Yes:
                    pd_removed_count = 0

                    for dup_addr in pd_duplicate_addresses:
                        # Get all deals with this address
                        deals_with_addr = [(deal_id, addr) for deal_id, addr in pd_addresses if addr == dup_addr]

                        if len(deals_with_addr) > 1:
                            # Keep the first one, remove others
                            remove_deals = deals_with_addr[1:]

                            for deal_id, addr in remove_deals:
                                try:
                                    # Delete from Pipedrive
                                    r = requests.delete(
                                        f"{PIPEDRIVE_API_URL}/deals/{deal_id}",
                                        params={'api_token': PIPEDRIVE_API_TOKEN},
                                        timeout=30
                                    )

                                    if r.status_code == 200:
                                        pd_removed_count += 1
                                        if pd_removed_count <= 10:
                                            self.log(f"   ✅ Deleted duplicate deal {deal_id} from Pipedrive")
                                except Exception as e:
                                    self.log(f"   ❌ Error deleting deal {deal_id}: {str(e)}")

                    if pd_removed_count > 10:
                        self.log(f"   ... and {pd_removed_count - 10} more")

                    self.log(f"\n✅ Removed {pd_removed_count} duplicate deals from Pipedrive")
                    self.pd_dupes_label.setText(f"Pipedrive Duplicates: 0")
                else:
                    self.log("❌ Pipedrive duplicate removal cancelled")
            else:
                self.log("✅ No duplicates found in Pipedrive")

            self.log("\n🎉 Duplicate removal complete!")

            # Refresh properties
            self.load_properties()

            QMessageBox.information(
                self,
                "Success",
                "✅ Duplicate removal complete!\n\n"
                "Check the log for details."
            )

        except Exception as e:
            self.log(f"❌ Error: {str(e)}")
            import traceback
            self.log(traceback.format_exc())
            QMessageBox.critical(self, "Error", f"Failed to remove duplicates:\n{str(e)}")
        finally:
            self.set_loading_cursor(False)  # Hide loading cursor


def main():
    # Set Windows taskbar icon (Windows only)
    if sys.platform == 'win32':
        try:
            # Set AppUserModelID to make Windows recognize our icon
            myappid = 'terryroyer.zillow.integrated.system'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except:
            pass  # Ignore errors on non-Windows systems

    app = QApplication(sys.argv)

    # Set application style
    app.setStyle('Fusion')

    # Set application icon globally
    icon_path = 'lcon.png'
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window = ZillowPipedriveUI()
    window.show()

    sys.exit(app.exec_())


# ========== SCRAPER WORKER THREAD ==========
class ScraperWorker(QThread):
    """Background thread for scraping with detailed progress updates"""

    # Signals for UI updates
    log_signal = pyqtSignal(str)  # Log messages
    progress_signal = pyqtSignal(int, int)  # (current, total)
    status_signal = pyqtSignal(str)  # Status updates
    finished_signal = pyqtSignal(dict)  # Final stats

    def __init__(self, max_properties=50, delay_seconds=5, batch_size=5):
        super().__init__()
        self.max_properties = max_properties
        self.delay_seconds = delay_seconds
        self.batch_size = batch_size
        self.is_running = True
        self.scraper = AdvancedZillowScraper()

    def run(self):
        """Main scraping loop with detailed logging"""
        try:
            self.log_signal.emit("🚀 Starting Advanced Zillow Scraper...")
            self.log_signal.emit("=" * 70)

            # Load URLs
            self.status_signal.emit("Loading URLs...")
            urls = self.scraper.load_urls()
            if not urls:
                self.log_signal.emit("❌ No URLs found in scraping_urls.txt")
                self.finished_signal.emit({'success': False, 'error': 'No URLs'})
                return

            self.log_signal.emit(f"✅ Loaded {len(urls)} URL categories")

            # Stats
            total_scraped = 0
            total_saved_csv = 0
            total_saved_db = 0
            total_uploaded_pd = 0
            total_duplicates = 0
            total_errors = 0

            # Process each URL category
            for url_index, (url, property_type) in enumerate(urls):
                if not self.is_running:
                    self.log_signal.emit("⏸️ Scraping stopped by user")
                    break

                self.log_signal.emit(f"\n{'='*70}")
                self.log_signal.emit(f"📂 Category {url_index + 1}/{len(urls)}: {property_type}")
                self.log_signal.emit(f"{'='*70}")
                self.status_signal.emit(f"Scraping {property_type}...")

                # Calculate how many properties we still need
                remaining = self.max_properties - total_scraped

                # Scrape properties from this URL (with pagination)
                # Pass log_callback so pagination logs appear in UI
                properties = self.scraper.scrape_properties_from_url(
                    url,
                    property_type,
                    max_properties=remaining,
                    log_callback=lambda msg: self.log_signal.emit(msg)
                )

                if not properties:
                    self.log_signal.emit(f"⚠️ No properties found for {property_type}")
                    continue

                self.log_signal.emit(f"✅ Found {len(properties)} properties from pagination")

                # Process each property
                for prop_index, prop in enumerate(properties):
                    if not self.is_running:
                        break

                    if total_scraped >= self.max_properties:
                        self.log_signal.emit(f"\n✅ Reached maximum limit of {self.max_properties} properties")
                        break

                    total_scraped += 1
                    self.progress_signal.emit(total_scraped, self.max_properties)

                    self.log_signal.emit(f"\n{'─'*70}")
                    self.log_signal.emit(f"🏠 Property {total_scraped}/{self.max_properties}")
                    self.log_signal.emit(f"{'─'*70}")
                    self.log_signal.emit(f"📍 Address: {prop.get('address', 'N/A')}")
                    self.log_signal.emit(f"💰 Price: {prop.get('price', 'N/A')}")
                    self.log_signal.emit(f"🏷️ Type: {prop.get('property_type', 'N/A')}")
                    self.log_signal.emit(f"🛏️ Beds: {prop.get('beds', 'N/A')} | 🚿 Baths: {prop.get('baths', 'N/A')} | 📐 Sqft: {prop.get('sqft', 'N/A')}")

                    # Extract agent info
                    self.status_signal.emit(f"Extracting agent info ({total_scraped}/{self.max_properties})...")
                    self.log_signal.emit(f"🔍 Extracting agent information...")

                    agent_info = self.scraper.extract_agent_info_advanced(prop.get('url', ''))
                    prop['agent_name'] = agent_info.get('agent_name', 'N/A')
                    prop['agent_phone'] = agent_info.get('agent_phone', 'N/A')

                    self.log_signal.emit(f"👤 Agent: {prop['agent_name']}")
                    self.log_signal.emit(f"📞 Phone: {prop['agent_phone']}")

                    # Check duplicates
                    is_dup_csv = self.scraper.is_duplicate_in_csv(prop['address'])
                    is_dup_db = self.scraper.is_duplicate_in_database(prop['address'])

                    # If duplicate in CSV OR Database, skip everything (including Pipedrive)
                    if is_dup_csv or is_dup_db:
                        if is_dup_csv and is_dup_db:
                            self.log_signal.emit(f"⏭️ DUPLICATE - Skipping (already in CSV and Database)")
                        elif is_dup_csv:
                            self.log_signal.emit(f"⏭️ DUPLICATE - Skipping (already in CSV)")
                        else:
                            self.log_signal.emit(f"⏭️ DUPLICATE - Skipping (already in Database)")
                        total_duplicates += 1
                        continue

                    # Property is NEW - Save to all three places

                    # Save to CSV
                    self.status_signal.emit(f"Saving to CSV ({total_scraped}/{self.max_properties})...")
                    if self.scraper.save_to_csv(prop):
                        self.log_signal.emit(f"✅ Saved to CSV")
                        total_saved_csv += 1
                    else:
                        self.log_signal.emit(f"❌ Failed to save to CSV")
                        total_errors += 1

                    # Save to Database
                    self.status_signal.emit(f"Saving to Database ({total_scraped}/{self.max_properties})...")
                    if self.scraper.save_to_database(prop):
                        self.log_signal.emit(f"✅ Saved to Database (lead_in table)")
                        total_saved_db += 1
                    else:
                        self.log_signal.emit(f"❌ Failed to save to Database")
                        total_errors += 1

                    # Upload to Pipedrive (only if NEW property)
                    self.status_signal.emit(f"Uploading to Pipedrive ({total_scraped}/{self.max_properties})...")
                    upload_result = self.scraper.upload_to_pipedrive(prop)

                    if upload_result.get('success'):
                        self.log_signal.emit(f"✅ Uploaded to Pipedrive")
                        self.log_signal.emit(f"   📋 Deal ID: {upload_result.get('deal_id', 'N/A')}")
                        self.log_signal.emit(f"   👤 Person ID: {upload_result.get('person_id', 'N/A')}")
                        self.log_signal.emit(f"   📝 Note Created: Yes")
                        total_uploaded_pd += 1
                    else:
                        self.log_signal.emit(f"❌ Failed to upload to Pipedrive: {upload_result.get('error', 'Unknown')}")
                        total_errors += 1

                    # Delay between properties
                    if prop_index < len(properties) - 1:
                        self.log_signal.emit(f"⏳ Waiting {self.delay_seconds} seconds before next property...")
                        time.sleep(self.delay_seconds)

                # Check if reached max
                if total_scraped >= self.max_properties:
                    break

                # Delay between URL categories
                if url_index < len(urls) - 1 and total_scraped < self.max_properties:
                    self.log_signal.emit(f"\n⏳ Waiting {self.delay_seconds} seconds before next category...")
                    time.sleep(self.delay_seconds)

            # Final summary
            self.log_signal.emit(f"\n{'='*70}")
            self.log_signal.emit(f"🎉 SCRAPING COMPLETE!")
            self.log_signal.emit(f"{'='*70}")
            self.log_signal.emit(f"📊 Total Properties Scraped: {total_scraped}")
            self.log_signal.emit(f"💾 Saved to CSV: {total_saved_csv}")
            self.log_signal.emit(f"🗄️ Saved to Database: {total_saved_db}")
            self.log_signal.emit(f"📤 Uploaded to Pipedrive: {total_uploaded_pd}")
            self.log_signal.emit(f"⏭️ Duplicates Skipped: {total_duplicates}")
            self.log_signal.emit(f"❌ Errors: {total_errors}")
            self.log_signal.emit(f"{'='*70}")

            self.status_signal.emit("Scraping complete!")
            self.finished_signal.emit({
                'success': True,
                'total_scraped': total_scraped,
                'saved_csv': total_saved_csv,
                'saved_db': total_saved_db,
                'uploaded_pd': total_uploaded_pd,
                'duplicates': total_duplicates,
                'errors': total_errors
            })

        except Exception as e:
            self.log_signal.emit(f"\n❌ CRITICAL ERROR: {str(e)}")
            self.status_signal.emit("Error occurred!")
            self.finished_signal.emit({'success': False, 'error': str(e)})

    def stop(self):
        """Stop the scraping process"""
        self.is_running = False


if __name__ == '__main__':
    main()


