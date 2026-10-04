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
    QListWidgetItem,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QTextEdit,
    QSpinBox,
    QPushButton,
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
            self.btnMyDay,
            self.btnTodoList,
            self.btnStats,
            self.btnLists,
            self.btnSettings,
        ]

        self.page_titles = {
            0: ("Add a ToDo", "Capture it now. Organize it clearly. Finish it with less noise."),
            1: ("My Day", "A focused view of what deserves your attention today."),
            2: ("List of ToDos", "Everything you have captured, in one clean place."),
            3: ("Stats", "Turn your ToDo history into useful productivity insights."),
            4: ("Lists", "Build reusable checklists for groceries, trips, packing and anything else."),
            5: ("Settings", "Control defaults, backups and application behavior."),
        }

        self.setup_navigation()
        self.setup_add_todo_page()
        self.setup_my_day_table()
        self.setup_todo_table()
        self.setup_lists_page()

        self.load_categories()
        self.load_my_day()
        self.load_todos()
        self.load_stats()
        self.load_lists()
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
        self.btnMyDay.clicked.connect(lambda: self.show_page(1))
        self.btnTodoList.clicked.connect(lambda: self.show_page(2))
        self.btnStats.clicked.connect(lambda: self.show_page(3))
        self.btnLists.clicked.connect(lambda: self.show_page(4))
        self.btnSettings.clicked.connect(lambda: self.show_page(5))

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
            self.load_my_day()
        elif index == 2:
            self.load_todos()
        elif index == 3:
            self.load_stats()
        elif index == 4:
            self.load_lists()

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
            self.load_my_day()
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
    # My Day
    # ------------------------------------------------------------------
    def setup_my_day_table(self):
        self.tableMyDay.setColumnCount(8)
        self.tableMyDay.setHorizontalHeaderLabels(["Task", "Why today?", "Category", "Priority", "Status", "Due", "Progress", "Action"])
        self.tableMyDay.verticalHeader().setVisible(False)
        self.tableMyDay.setAlternatingRowColors(True)
        self.tableMyDay.setSelectionBehavior(self.tableMyDay.SelectRows)
        self.tableMyDay.setEditTriggers(self.tableMyDay.NoEditTriggers)
        header = self.tableMyDay.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        for column in range(2, 8): header.setSectionResizeMode(column, QHeaderView.ResizeToContents)
        self.btnRefreshMyDay.clicked.connect(self.load_my_day)

    def load_my_day(self):
        today = datetime.now().strftime("%Y-%m-%d")
        try:
            self.cursor.execute("""
                SELECT
                    t.id,
                    t.task,
                    CASE
                        WHEN t.dueOn < ? THEN 'Overdue'
                        WHEN t.dueOn = ? THEN 'Due today'
                        WHEN t.startOn = ? THEN 'Starts today'
                        WHEN t.status = 'In Progress' THEN 'In progress'
                        WHEN t.priority = 'Critical' THEN 'Critical'
                        WHEN t.priority = 'High' THEN 'High priority'
                        ELSE 'Relevant'
                    END AS reason,
                    COALESCE(c.name, ''),
                    t.priority,
                    t.status,
                    COALESCE(t.dueOn, ''),
                    COALESCE(t.progress, 0)
                FROM todos t
                LEFT JOIN categories c ON c.id = t.categoryId
                WHERE t.status NOT IN ('Done', 'Cancelled')
                  AND (
                        t.dueOn <= ?
                        OR t.startOn = ?
                        OR t.status = 'In Progress'
                        OR (t.priority IN ('Critical', 'High') AND (t.startOn IS NULL OR t.startOn <= ?))
                  )
                ORDER BY
                    CASE
                        WHEN t.dueOn < ? THEN 1
                        WHEN t.dueOn = ? THEN 2
                        WHEN t.startOn = ? THEN 3
                        WHEN t.status = 'In Progress' THEN 4
                        WHEN t.priority = 'Critical' THEN 5
                        WHEN t.priority = 'High' THEN 6
                        ELSE 7
                    END,
                    CASE t.priority WHEN 'Critical' THEN 1 WHEN 'High' THEN 2 WHEN 'Medium' THEN 3 WHEN 'Low' THEN 4 ELSE 5 END,
                    CASE WHEN t.dueOn IS NULL THEN 1 ELSE 0 END,
                    t.dueOn,
                    t.id DESC
            """, (today, today, today, today, today, today, today, today, today))
            rows = self.cursor.fetchall()
            self.tableMyDay.setRowCount(len(rows))
            for row_index, row_data in enumerate(rows):
                todo_id = row_data[0]
                display_values = list(row_data[1:])
                display_values[-1] = f"{display_values[-1]}%"
                for column_index, value in enumerate(display_values):
                    item = QTableWidgetItem(str(value if value is not None else ""))
                    item.setTextAlignment((Qt.AlignCenter if column_index in (1, 3, 4, 5, 6) else Qt.AlignLeft) | Qt.AlignVCenter)
                    if column_index == 0: item.setData(Qt.UserRole, todo_id)
                    self.tableMyDay.setItem(row_index, column_index, item)
                self.tableMyDay.setCellWidget(row_index, 7, self.create_finish_button(todo_id))

            self.cursor.execute("""
                SELECT
                    SUM(CASE WHEN dueOn < ? AND status NOT IN ('Done', 'Cancelled') THEN 1 ELSE 0 END),
                    SUM(CASE WHEN dueOn = ? AND status NOT IN ('Done', 'Cancelled') THEN 1 ELSE 0 END),
                    SUM(CASE WHEN status = 'In Progress' THEN 1 ELSE 0 END)
                FROM todos
            """, (today, today))
            counts = self.cursor.fetchone() or (0, 0, 0)
            self.lblMyDayOverdueValue.setText(str(counts[0] or 0))
            self.lblMyDayDueValue.setText(str(counts[1] or 0))
            self.lblMyDayProgressValue.setText(str(counts[2] or 0))
        except sqlite3.Error as error:
            QMessageBox.warning(self, "My Day could not be loaded", f"The relevant ToDos could not be read.\n\n{error}")

    # ------------------------------------------------------------------
    # ToDo list + completion workflow
    # ------------------------------------------------------------------
    def setup_todo_table(self):
        self.tableTodos.setColumnCount(9)
        self.tableTodos.setHorizontalHeaderLabels(["Task", "Category", "Priority", "Status", "Created", "Start", "Due", "Progress", "Action"])
        self.tableTodos.verticalHeader().setVisible(False)
        self.tableTodos.setAlternatingRowColors(True)
        self.tableTodos.setSelectionBehavior(self.tableTodos.SelectRows)
        self.tableTodos.setEditTriggers(self.tableTodos.NoEditTriggers)
        header = self.tableTodos.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        for column in range(1, 9): header.setSectionResizeMode(column, QHeaderView.ResizeToContents)

    def create_finish_button(self, todo_id, status=None):
        button = QPushButton("Done" if status == "Done" else "✓  Finish")
        button.setCursor(Qt.PointingHandCursor)
        if status == "Done":
            button.setEnabled(False)
            button.setStyleSheet("QPushButton{background:#EEF7F1;color:#4F735D;border:1px solid #D1E3D7;border-radius:8px;padding:6px 11px;font-weight:800;}")
        elif status == "Cancelled":
            button.setText("Cancelled")
            button.setEnabled(False)
            button.setStyleSheet("QPushButton{background:#F3F3F3;color:#8A8A8A;border:1px solid #DDDDDD;border-radius:8px;padding:6px 11px;font-weight:750;}")
        else:
            button.setStyleSheet("QPushButton{background:#EAF4EE;color:#356247;border:1px solid #C9DFD1;border-radius:8px;padding:6px 11px;font-weight:850;} QPushButton:hover{background:#DCEDE3;}")
            button.clicked.connect(lambda checked=False, current_id=todo_id: self.finish_todo(current_id))
        return button

    def load_todos(self):
        try:
            self.cursor.execute("""
                SELECT
                    t.id,
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
                    CASE t.status WHEN 'In Progress' THEN 1 WHEN 'Open' THEN 2 WHEN 'Inbox' THEN 3 WHEN 'Waiting' THEN 4 WHEN 'Done' THEN 5 WHEN 'Cancelled' THEN 6 ELSE 7 END,
                    CASE WHEN t.dueOn IS NULL THEN 1 ELSE 0 END,
                    t.dueOn,
                    t.id DESC
            """)
            rows = self.cursor.fetchall()
            self.tableTodos.setRowCount(len(rows))
            for row_index, row_data in enumerate(rows):
                todo_id = row_data[0]
                status = row_data[4]
                display_values = list(row_data[1:])
                display_values[-1] = f"{display_values[-1]}%"
                for column_index, value in enumerate(display_values):
                    item = QTableWidgetItem(str(value if value is not None else ""))
                    item.setTextAlignment((Qt.AlignCenter if column_index in (2, 3, 4, 5, 6, 7) else Qt.AlignLeft) | Qt.AlignVCenter)
                    if column_index == 0: item.setData(Qt.UserRole, todo_id)
                    self.tableTodos.setItem(row_index, column_index, item)
                self.tableTodos.setCellWidget(row_index, 8, self.create_finish_button(todo_id, status))
        except sqlite3.Error as error:
            QMessageBox.warning(self, "ToDo list could not be loaded", f"The ToDo table could not be read.\n\n{error}")

    def finish_todo(self, todo_id):
        try:
            self.cursor.execute("""
                SELECT task, status, progress, doneOn, actualMinutes, COALESCE(comment, '')
                FROM todos
                WHERE id = ?
            """, (todo_id,))
            row = self.cursor.fetchone()
        except sqlite3.Error as error:
            QMessageBox.warning(self, "ToDo could not be loaded", f"The ToDo could not be read.\n\n{error}")
            return

        if not row: return
        task, old_status, old_progress, old_done_on, old_actual_minutes, old_comment = row
        if old_status == "Done":
            QMessageBox.information(self, "Already finished", f'“{task}” is already marked as Done.')
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Finish ToDo")
        dialog.setMinimumWidth(520)
        dialog.setStyleSheet("QDialog{background:#F6F9F9;color:#263A42;} QLabel{color:#40555D;} QTextEdit,QSpinBox{background:#FFFFFF;border:1px solid #C9D7DB;border-radius:9px;padding:7px;} QPushButton{border-radius:9px;padding:9px 15px;font-weight:800;}")
        layout = QVBoxLayout(dialog)
        title = QLabel(f"Finish: {task}")
        title.setStyleSheet("font-size:18px;font-weight:900;color:#29453E;")
        helper = QLabel("Add a final note or the actual effort if useful. Both are optional.")
        helper.setWordWrap(True)
        helper.setStyleSheet("color:#6B7D84;font-size:11px;margin-bottom:6px;")
        layout.addWidget(title)
        layout.addWidget(helper)
        form = QFormLayout()
        spin_actual = QSpinBox()
        spin_actual.setRange(0, 100000)
        spin_actual.setSuffix(" min")
        spin_actual.setValue(old_actual_minutes or 0)
        txt_completion = QTextEdit()
        txt_completion.setPlaceholderText("What was completed? Anything worth remembering about this ToDo?")
        txt_completion.setMinimumHeight(120)
        form.addRow("Actual time", spin_actual)
        form.addRow("Completion comment", txt_completion)
        layout.addLayout(form)
        buttons = QHBoxLayout()
        buttons.addStretch()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setStyleSheet("QPushButton{background:#EDF2F3;color:#40555D;border:1px solid #D1DDE0;}")
        btn_finish = QPushButton("✓  Mark as Done")
        btn_finish.setStyleSheet("QPushButton{background:#587F73;color:#FFFFFF;border:0;} QPushButton:hover{background:#4C7166;}")
        btn_cancel.clicked.connect(dialog.reject)
        btn_finish.clicked.connect(dialog.accept)
        buttons.addWidget(btn_cancel)
        buttons.addWidget(btn_finish)
        layout.addLayout(buttons)
        if dialog.exec_() != QDialog.Accepted: return

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        actual_minutes = spin_actual.value() or None
        completion_comment = txt_completion.toPlainText().strip()
        new_comment = old_comment
        if completion_comment:
            completion_entry = f"[Completed {now}]\n{completion_comment}"
            new_comment = f"{old_comment.rstrip()}\n\n{completion_entry}" if old_comment.strip() else completion_entry

        try:
            self.cursor.execute("""
                UPDATE todos
                SET status = 'Done', progress = 100, doneOn = ?, actualMinutes = ?, comment = ?
                WHERE id = ?
            """, (now, actual_minutes, new_comment or None, todo_id))
            history_changes = [("status", old_status, "Done"), ("progress", str(old_progress or 0), "100"), ("doneOn", old_done_on, now)]
            if actual_minutes != old_actual_minutes: history_changes.append(("actualMinutes", old_actual_minutes, actual_minutes))
            if completion_comment: history_changes.append(("comment", old_comment or None, new_comment))
            for field, old_value, new_value in history_changes:
                self.cursor.execute("INSERT INTO todo_history (todoId, changedAt, field, oldValue, newValue) VALUES (?, ?, ?, ?, ?)", (todo_id, now, field, None if old_value is None else str(old_value), None if new_value is None else str(new_value)))
            self.conn.commit()
            self.load_todos()
            self.load_my_day()
            self.load_stats()
            QMessageBox.information(self, "ToDo finished", f'“{task}” was marked as Done.')
        except sqlite3.Error as error:
            self.conn.rollback()
            QMessageBox.critical(self, "Database error", f"The ToDo could not be completed.\n\n{error}")

    # ------------------------------------------------------------------
    # Reusable Lists page
    # ------------------------------------------------------------------
    def setup_lists_page(self):
        self.current_list_id = None

        self.btnCreateList.clicked.connect(self.create_list)
        self.btnDeleteList.clicked.connect(self.delete_list)
        self.btnAddListItem.clicked.connect(self.add_list_item)
        self.btnDeleteListItem.clicked.connect(self.delete_list_item)
        self.btnResetListChecks.clicked.connect(self.reset_list_checks)

        self.listCustomLists.currentItemChanged.connect(self.on_list_selected)
        self.tableListItems.itemChanged.connect(self.on_list_item_changed)

        self.tableListItems.setColumnCount(3)
        self.tableListItems.setHorizontalHeaderLabels([
            "Done",
            "Item",
            "Note",
        ])
        self.tableListItems.verticalHeader().setVisible(False)
        self.tableListItems.setAlternatingRowColors(True)
        self.tableListItems.setSelectionBehavior(self.tableListItems.SelectRows)

        header = self.tableListItems.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)

        self.set_list_editor_enabled(False)

    def set_list_editor_enabled(self, enabled):
        self.editListItem.setEnabled(enabled)
        self.editListItemNote.setEnabled(enabled)
        self.btnAddListItem.setEnabled(enabled)
        self.btnDeleteListItem.setEnabled(enabled)
        self.btnResetListChecks.setEnabled(enabled)
        self.btnDeleteList.setEnabled(enabled)
        self.tableListItems.setEnabled(enabled)

        if not enabled:
            self.lblSelectedListName.setText("Select a list")
            self.lblSelectedListDescription.setText(
                "Choose a list on the left or create a new one."
            )
            self.lblListItemCount.setText("0 items")
            self.tableListItems.setRowCount(0)

    def load_lists(self, select_list_id=None):
        try:
            self.cursor.execute("""
                SELECT id, name, COALESCE(description, '')
                FROM custom_lists
                ORDER BY name COLLATE NOCASE
            """)
            rows = self.cursor.fetchall()

        except sqlite3.Error as error:
            # This keeps the rest of ToDoZaM fully usable until the user runs
            # the two CREATE TABLE statements supplied with this version.
            self.listCustomLists.clear()
            self.current_list_id = None
            self.set_list_editor_enabled(False)
            self.lblListsDatabaseHint.setText(
                "Run the supplied SQL once to create custom_lists and "
                "custom_list_items."
            )
            return

        self.lblListsDatabaseHint.setText(
            "Reusable lists are stored locally in your ToDoZaM database."
        )

        previous_id = select_list_id or self.current_list_id
        self.listCustomLists.blockSignals(True)
        self.listCustomLists.clear()

        selected_row = -1

        for row_index, (list_id, name, description) in enumerate(rows):
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, list_id)
            item.setData(Qt.UserRole + 1, description)
            self.listCustomLists.addItem(item)

            if list_id == previous_id:
                selected_row = row_index

        self.listCustomLists.blockSignals(False)

        if rows:
            if selected_row < 0:
                selected_row = 0
            self.listCustomLists.setCurrentRow(selected_row)
            self.on_list_selected(self.listCustomLists.currentItem(), None)
        else:
            self.current_list_id = None
            self.set_list_editor_enabled(False)

    def create_list(self):
        name = self.editNewListName.text().strip()
        description = self.editNewListDescription.toPlainText().strip() or None

        if not name:
            QMessageBox.warning(self, "List name required", "Please enter a list name.")
            self.editNewListName.setFocus()
            return

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            self.cursor.execute("""
                INSERT INTO custom_lists (
                    name,
                    description,
                    createdAt,
                    updatedAt
                )
                VALUES (?, ?, ?, ?)
            """, (name, description, now, now))

            list_id = self.cursor.lastrowid
            self.conn.commit()

            self.editNewListName.clear()
            self.editNewListDescription.clear()
            self.load_lists(select_list_id=list_id)
            self.editListItem.setFocus()

        except sqlite3.IntegrityError:
            self.conn.rollback()
            QMessageBox.warning(
                self,
                "List already exists",
                "A list with this name already exists.",
            )
        except sqlite3.Error as error:
            self.conn.rollback()
            QMessageBox.critical(
                self,
                "Database error",
                f"The list could not be created.\n\n{error}",
            )

    def on_list_selected(self, current, previous):
        if current is None:
            self.current_list_id = None
            self.set_list_editor_enabled(False)
            return

        self.current_list_id = current.data(Qt.UserRole)
        self.lblSelectedListName.setText(current.text())

        description = current.data(Qt.UserRole + 1) or "No description added."
        self.lblSelectedListDescription.setText(description)
        self.set_list_editor_enabled(True)
        self.load_list_items()

    def load_list_items(self):
        if self.current_list_id is None:
            self.tableListItems.setRowCount(0)
            return

        try:
            self.cursor.execute("""
                SELECT
                    id,
                    item,
                    COALESCE(note, ''),
                    checked
                FROM custom_list_items
                WHERE listId = ?
                ORDER BY sortOrder, id
            """, (self.current_list_id,))

            rows = self.cursor.fetchall()

            self.tableListItems.blockSignals(True)
            self.tableListItems.setRowCount(len(rows))

            for row_index, (item_id, item_text, note, checked) in enumerate(rows):
                check_item = QTableWidgetItem("")
                check_item.setData(Qt.UserRole, item_id)
                check_item.setFlags(
                    Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable
                )
                check_item.setCheckState(Qt.Checked if checked else Qt.Unchecked)
                check_item.setTextAlignment(Qt.AlignCenter)

                text_item = QTableWidgetItem(item_text)
                text_item.setData(Qt.UserRole, item_id)

                note_item = QTableWidgetItem(note)
                note_item.setData(Qt.UserRole, item_id)

                self.tableListItems.setItem(row_index, 0, check_item)
                self.tableListItems.setItem(row_index, 1, text_item)
                self.tableListItems.setItem(row_index, 2, note_item)

            self.tableListItems.blockSignals(False)
            self.lblListItemCount.setText(
                f"{len(rows)} item{'s' if len(rows) != 1 else ''}"
            )

        except sqlite3.Error as error:
            self.tableListItems.blockSignals(False)
            QMessageBox.warning(
                self,
                "List items could not be loaded",
                f"The list items could not be read.\n\n{error}",
            )

    def add_list_item(self):
        if self.current_list_id is None:
            return

        item_text = self.editListItem.text().strip()
        note = self.editListItemNote.text().strip() or None

        if not item_text:
            QMessageBox.warning(self, "Item required", "Please enter an item.")
            self.editListItem.setFocus()
            return

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            self.cursor.execute("""
                SELECT COALESCE(MAX(sortOrder), 0) + 1
                FROM custom_list_items
                WHERE listId = ?
            """, (self.current_list_id,))
            next_order = self.cursor.fetchone()[0]

            self.cursor.execute("""
                INSERT INTO custom_list_items (
                    listId,
                    item,
                    note,
                    checked,
                    sortOrder,
                    createdAt
                )
                VALUES (?, ?, ?, 0, ?, ?)
            """, (
                self.current_list_id,
                item_text,
                note,
                next_order,
                now,
            ))

            self.cursor.execute("""
                UPDATE custom_lists
                SET updatedAt = ?
                WHERE id = ?
            """, (now, self.current_list_id))

            self.conn.commit()
            self.editListItem.clear()
            self.editListItemNote.clear()
            self.load_list_items()
            self.editListItem.setFocus()

        except sqlite3.Error as error:
            self.conn.rollback()
            QMessageBox.critical(
                self,
                "Database error",
                f"The item could not be added.\n\n{error}",
            )

    def on_list_item_changed(self, item):
        if self.current_list_id is None:
            return

        item_id = item.data(Qt.UserRole)
        if item_id is None:
            return

        try:
            if item.column() == 0:
                checked = 1 if item.checkState() == Qt.Checked else 0
                self.cursor.execute("""
                    UPDATE custom_list_items
                    SET checked = ?
                    WHERE id = ? AND listId = ?
                """, (checked, item_id, self.current_list_id))

            elif item.column() == 1:
                value = item.text().strip()
                if not value:
                    self.load_list_items()
                    return
                self.cursor.execute("""
                    UPDATE custom_list_items
                    SET item = ?
                    WHERE id = ? AND listId = ?
                """, (value, item_id, self.current_list_id))

            elif item.column() == 2:
                self.cursor.execute("""
                    UPDATE custom_list_items
                    SET note = ?
                    WHERE id = ? AND listId = ?
                """, (item.text().strip() or None, item_id, self.current_list_id))

            self.cursor.execute("""
                UPDATE custom_lists
                SET updatedAt = ?
                WHERE id = ?
            """, (
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                self.current_list_id,
            ))

            self.conn.commit()

        except sqlite3.Error as error:
            self.conn.rollback()
            QMessageBox.warning(
                self,
                "Item could not be updated",
                f"The change could not be saved.\n\n{error}",
            )

    def delete_list_item(self):
        selected_rows = self.tableListItems.selectionModel().selectedRows()

        if not selected_rows:
            QMessageBox.information(
                self,
                "Select an item",
                "Please select the item you want to delete.",
            )
            return

        row = selected_rows[0].row()
        first_item = self.tableListItems.item(row, 0)
        item_id = first_item.data(Qt.UserRole)
        item_name = self.tableListItems.item(row, 1).text()

        answer = QMessageBox.question(
            self,
            "Delete item",
            f'Delete “{item_name}” from this list?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:
            return

        try:
            self.cursor.execute("""
                DELETE FROM custom_list_items
                WHERE id = ? AND listId = ?
            """, (item_id, self.current_list_id))
            self.conn.commit()
            self.load_list_items()

        except sqlite3.Error as error:
            self.conn.rollback()
            QMessageBox.critical(
                self,
                "Database error",
                f"The item could not be deleted.\n\n{error}",
            )

    def reset_list_checks(self):
        if self.current_list_id is None:
            return


        try:
            self.cursor.execute("""
                UPDATE custom_list_items
                SET checked = 0
                WHERE listId = ?
            """, (self.current_list_id,))
            self.conn.commit()
            self.load_list_items()

        except sqlite3.Error as error:
            self.conn.rollback()
            QMessageBox.critical(
                self,
                "Database error",
                f"The checklist could not be reset.\n\n{error}",
            )

    def delete_list(self):
        if self.current_list_id is None:
            return

        current = self.listCustomLists.currentItem()
        list_name = current.text() if current else "this list"

        answer = QMessageBox.question(
            self,
            "Delete list",
            f'Delete “{list_name}” and all of its items?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:
            return

        try:
            self.cursor.execute(
                "DELETE FROM custom_lists WHERE id = ?",
                (self.current_list_id,),
            )
            self.conn.commit()
            self.current_list_id = None
            self.load_lists()

        except sqlite3.Error as error:
            self.conn.rollback()
            QMessageBox.critical(
                self,
                "Database error",
                f"The list could not be deleted.\n\n{error}",
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
