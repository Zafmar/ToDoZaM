# Front-End
# ToDoZaM - Main Menu

# before everything else, make the screen adjust to the displaying unit
import os
import sys
import ctypes

if sys.platform.startswith("win"):
    try:
        scale_factor = ctypes.windll.shcore.GetScaleFactorForDevice(0) / 100
        os.environ["QT_SCALE_FACTOR"] = str(scale_factor)
    except Exception:
        pass

# Libraries
import sqlite3
from datetime import datetime

from PyQt5 import uic
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QMessageBox,
    QTableWidgetItem,
    QHeaderView,
)


# Keep .py, .ui and database in the same folder.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UI_FILE = os.path.join(BASE_DIR, "ToDoZaM.ui")

# Your DB was named "ToDoZam_DB". The extra candidates simply make the
# program tolerant in case Windows currently shows/hides a file extension.
DB_CANDIDATES = [
    os.path.join(BASE_DIR, "ToDoZam_DB"),
    os.path.join(BASE_DIR, "ToDoZam_DB.db"),
    os.path.join(BASE_DIR, "ToDoZam_DB.sqlite"),
    os.path.join(BASE_DIR, "ToDoZam_DB.sqlite3"),
]
DB_FILE = next((path for path in DB_CANDIDATES if os.path.exists(path)), DB_CANDIDATES[0])


class MainMenuWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        uic.loadUi(UI_FILE, self)

        # Database
        self.conn = sqlite3.connect(DB_FILE)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.cursor = self.conn.cursor()

        self.setWindowTitle("ToDoZaM")

        self.nav_buttons = [
            self.btnAddTodo,
            self.btnTodoList,
            self.btnStats,
            self.btnLists,
            self.btnSettings,
        ]

        self.page_titles = {
            0: ("Add a ToDo", "Capture it now. Organize it clearly. Finish it with less noise."),
            1: ("List of ToDos", "Everything you have captured, in one clean place."),
            2: ("Stats", "Turn your ToDo history into useful productivity insights."),
            3: ("Lists", "Reusable structures for categories, projects, tags and more."),
            4: ("Settings", "Control defaults, backups and application behavior."),
        }

        self.setup_navigation()
        self.setup_add_todo_page()
        self.setup_todo_table()

        self.load_categories()
        self.load_todos()
        self.load_stats()
        self.refresh_created_at_preview()

        self.lblDatabasePath.setText(f"Database: {DB_FILE}")
        self.show_page(0)

    # ------------------------------------------------------------------
    # Main navigation
    # ------------------------------------------------------------------
    def setup_navigation(self):
        # Give all five menu buttons the same style class used by the .ui file.
        for button in self.nav_buttons:
            button.setProperty("class", "navButton")
            button.setProperty("active", False)
            button.style().unpolish(button)
            button.style().polish(button)

        self.btnAddTodo.clicked.connect(lambda: self.show_page(0))
        self.btnTodoList.clicked.connect(lambda: self.show_page(1))
        self.btnStats.clicked.connect(lambda: self.show_page(2))
        self.btnLists.clicked.connect(lambda: self.show_page(3))
        self.btnSettings.clicked.connect(lambda: self.show_page(4))

        self.lblToday.setText(datetime.now().strftime("%A, %d %B %Y"))

    def show_page(self, index):
        self.stackedWidget.setCurrentIndex(index)

        title, subtitle = self.page_titles[index]
        self.lblHeaderTitle.setText(title)
        self.lblHeaderSubtitle.setText(subtitle)

        for i, button in enumerate(self.nav_buttons):
            button.setProperty("active", i == index)
            button.style().unpolish(button)
            button.style().polish(button)

        # Refresh data when entering the pages that display database content.
        if index == 1:
            self.load_todos()
        elif index == 2:
            self.load_stats()

    # ------------------------------------------------------------------
    # Add ToDo page
    # ------------------------------------------------------------------
    def setup_add_todo_page(self):
        today = QDate.currentDate()
        self.dateStartOn.setDate(today)
        self.dateDueOn.setDate(today)

        # Defaults discussed in our design.
        self.comboPriority.setCurrentText("Medium")
        self.comboStatus.setCurrentText("Inbox")
        self.comboRecurring.setCurrentText("None")
        self.editRequestedBy.setText("Myself")

        self.checkStartOn.toggled.connect(self.dateStartOn.setEnabled)
        self.checkDueOn.toggled.connect(self.dateDueOn.setEnabled)
        self.comboStatus.currentTextChanged.connect(self.on_status_changed)

        self.btnSubmitTodo.clicked.connect(self.add_todo)
        self.btnClearTodo.clicked.connect(self.clear_todo_form)

    def refresh_created_at_preview(self):
        self.lblCreatedAtValue.setText(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def on_status_changed(self, status):
        if status == "Done":
            self.lblDoneOnValue.setText("Will be set to the current time when you submit")
            self.lblDoneOnValue.setStyleSheet(
                "color:#3F6E53;background:#EEF7F1;border:1px solid #CFE1D5;"
                "border-radius:9px;padding:7px 9px;font-weight:700;"
            )
            self.spinProgress.setValue(100)
        else:
            self.lblDoneOnValue.setText("Set automatically when status is Done")
            self.lblDoneOnValue.setStyleSheet(
                "color:#6B7D84;background:#F8FAFA;border:1px solid #E1E7E9;"
                "border-radius:9px;padding:7px 9px;"
            )
            if self.spinProgress.value() == 100 and status not in ("Done", "Cancelled"):
                self.spinProgress.setValue(0)

    def load_categories(self):
        self.comboCategory.clear()
        self.comboCategory.addItem("No category", None)

        try:
            self.cursor.execute("""
                SELECT id, name
                FROM categories
                WHERE active = 1
                ORDER BY name COLLATE NOCASE
            """)

            for category_id, category_name in self.cursor.fetchall():
                self.comboCategory.addItem(category_name, category_id)

        except sqlite3.Error as error:
            QMessageBox.warning(
                self,
                "Categories could not be loaded",
                f"The category list could not be read from the database.\n\n{error}",
            )

    def add_todo(self):
        task = self.editTask.text().strip()

        if not task:
            QMessageBox.warning(self, "Task required", "Please enter a task title.")
            self.editTask.setFocus()
            return

        start_on = self.dateStartOn.date().toString("yyyy-MM-dd") if self.checkStartOn.isChecked() else None
        due_on = self.dateDueOn.date().toString("yyyy-MM-dd") if self.checkDueOn.isChecked() else None

        if start_on and due_on and due_on < start_on:
            QMessageBox.warning(
                self,
                "Invalid dates",
                "Due On cannot be before Start On.",
            )
            return

        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status = self.comboStatus.currentText()
        done_on = created_at if status == "Done" else None

        estimated_minutes = self.spinEstimatedMinutes.value() or None
        actual_minutes = self.spinActualMinutes.value() or None
        category_id = self.comboCategory.currentData()

        values = (
            task,
            self.txtDescription.toPlainText().strip() or None,
            self.editRequestedBy.text().strip() or None,
            category_id,
            self.comboPriority.currentText(),
            status,
            created_at,
            start_on,
            due_on,
            done_on,
            estimated_minutes,
            actual_minutes,
            self.editProject.text().strip() or None,
            self.comboRecurring.currentText(),
            self.spinProgress.value(),
            self.txtComment.toPlainText().strip() or None,
        )

        try:
            self.cursor.execute("""
                INSERT INTO todos (
                    task,
                    description,
                    requestedBy,
                    categoryId,
                    priority,
                    status,
                    createdAt,
                    startOn,
                    dueOn,
                    doneOn,
                    estimatedMinutes,
                    actualMinutes,
                    project,
                    recurring,
                    progress,
                    comment
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, values)

            todo_id = self.cursor.lastrowid

            # A compact creation entry gives us a clean starting point for the
            # later history/timeline feature without duplicating every field.
            self.cursor.execute("""
                INSERT INTO todo_history (
                    todoId,
                    changedAt,
                    field,
                    oldValue,
                    newValue
                )
                VALUES (?, ?, ?, ?, ?)
            """, (todo_id, created_at, "status", None, status))

            self.conn.commit()

            QMessageBox.information(
                self,
                "ToDo added",
                f'“{task}” was added successfully.',
            )

            self.clear_todo_form()
            self.load_todos()
            self.load_stats()

        except sqlite3.Error as error:
            self.conn.rollback()
            QMessageBox.critical(
                self,
                "Database error",
                f"The ToDo could not be saved.\n\n{error}",
            )

    def clear_todo_form(self):
        self.editTask.clear()
        self.txtDescription.clear()
        self.editRequestedBy.setText("Myself")
        self.comboCategory.setCurrentIndex(0)
        self.comboPriority.setCurrentText("Medium")
        self.comboStatus.setCurrentText("Inbox")
        self.editProject.clear()
        self.comboRecurring.setCurrentText("None")
        self.spinProgress.setValue(0)
        self.spinEstimatedMinutes.setValue(0)
        self.spinActualMinutes.setValue(0)
        self.checkStartOn.setChecked(False)
        self.checkDueOn.setChecked(False)
        self.dateStartOn.setDate(QDate.currentDate())
        self.dateDueOn.setDate(QDate.currentDate())
        self.txtComment.clear()
        self.refresh_created_at_preview()
        self.on_status_changed(self.comboStatus.currentText())
        self.editTask.setFocus()

    # ------------------------------------------------------------------
    # Simple ToDo list preview
    # ------------------------------------------------------------------
    def setup_todo_table(self):
        self.tableTodos.setColumnCount(8)
        self.tableTodos.setHorizontalHeaderLabels([
            "Task",
            "Category",
            "Priority",
            "Status",
            "Created",
            "Start",
            "Due",
            "Progress",
        ])

        self.tableTodos.verticalHeader().setVisible(False)
        self.tableTodos.setAlternatingRowColors(True)
        self.tableTodos.setSelectionBehavior(self.tableTodos.SelectRows)
        self.tableTodos.setEditTriggers(self.tableTodos.NoEditTriggers)

        header = self.tableTodos.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        for column in range(1, 8):
            header.setSectionResizeMode(column, QHeaderView.ResizeToContents)

    def load_todos(self):
        try:
            self.cursor.execute("""
                SELECT
                    t.task,
                    COALESCE(c.name, ''),
                    t.priority,
                    t.status,
                    substr(t.createdAt, 1, 10),
                    COALESCE(t.startOn, ''),
                    COALESCE(t.dueOn, ''),
                    COALESCE(t.progress, 0)
                FROM todos t
                LEFT JOIN categories c ON c.id = t.categoryId
                ORDER BY
                    CASE t.status
                        WHEN 'In Progress' THEN 1
                        WHEN 'Open' THEN 2
                        WHEN 'Inbox' THEN 3
                        WHEN 'Waiting' THEN 4
                        WHEN 'Done' THEN 5
                        WHEN 'Cancelled' THEN 6
                        ELSE 7
                    END,
                    CASE WHEN t.dueOn IS NULL THEN 1 ELSE 0 END,
                    t.dueOn,
                    t.id DESC
            """)

            rows = self.cursor.fetchall()
            self.tableTodos.setRowCount(len(rows))

            for row_index, row_data in enumerate(rows):
                for column_index, value in enumerate(row_data):
                    if column_index == 7:
                        value = f"{value}%"

                    item = QTableWidgetItem(str(value if value is not None else ""))
                    item.setTextAlignment(
                        (Qt.AlignCenter if column_index in (2, 3, 4, 5, 6, 7) else Qt.AlignLeft)
                        | Qt.AlignVCenter
                    )
                    self.tableTodos.setItem(row_index, column_index, item)

        except sqlite3.Error as error:
            QMessageBox.warning(
                self,
                "ToDo list could not be loaded",
                f"The ToDo table could not be read.\n\n{error}",
            )

    # ------------------------------------------------------------------
    # Simple KPI cards - charts will be built later
    # ------------------------------------------------------------------
    def load_stats(self):
        try:
            self.cursor.execute("""
                SELECT
                    COUNT(*) AS total,
                    SUM(CASE WHEN status NOT IN ('Done', 'Cancelled') THEN 1 ELSE 0 END) AS open_count,
                    SUM(CASE WHEN status = 'In Progress' THEN 1 ELSE 0 END) AS in_progress,
                    SUM(CASE WHEN status = 'Done' THEN 1 ELSE 0 END) AS done_count,
                    SUM(CASE
                        WHEN dueOn < DATE('now')
                         AND status NOT IN ('Done', 'Cancelled')
                        THEN 1 ELSE 0 END
                    ) AS overdue_count
                FROM todos
            """)

            row = self.cursor.fetchone() or (0, 0, 0, 0, 0)

            self.lblKpiTotalValue.setText(str(row[0] or 0))
            self.lblKpiOpenValue.setText(str(row[1] or 0))
            self.lblKpiProgressValue.setText(str(row[2] or 0))
            self.lblKpiDoneValue.setText(str(row[3] or 0))
            self.lblKpiOverdueValue.setText(str(row[4] or 0))

        except sqlite3.Error as error:
            QMessageBox.warning(
                self,
                "Statistics could not be loaded",
                f"The KPI cards could not be calculated.\n\n{error}",
            )

    # ------------------------------------------------------------------
    def closeEvent(self, event):
        self.conn.close()
        event.accept()


if __name__ == "__main__":

    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)

    window = MainMenuWindow()
    window.showMaximized()

    sys.exit(app.exec_())
