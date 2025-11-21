#app.py
import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QPushButton, QScrollArea,
                             QGridLayout, QFrame, QDialog, QSpinBox, QMessageBox,
                             QLineEdit, QFormLayout, QComboBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QFont

from main import DataStorage, Character
from api_client import GenshinAPIClient, GenshinCharacterParser
from image_manager import ImageManager

# === ДОДАВАННЯ ПЕРСОНАЖА ===
class AddCharacterDialog(QDialog):

    def __init__(self, storage, parent=None):
        super().__init__(parent)
        self.storage = storage
        self.result = None
        self.setWindowTitle("Додати персонажа")
        self.setFixedSize(450, 400)
        self.setup_ui()

    def setup_ui(self):
        """Створення форми"""
        layout = QVBoxLayout()

        # Заголовок
        title = QLabel("✨ Створення персонажа")
        title.setFont(QFont('Arial', 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Форма
        form_layout = QFormLayout()
        form_layout.setSpacing(15)

        # Ім'я
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Введіть ім'я персонажа")
        self.name_input.setFont(QFont('Arial', 11))
        form_layout.addRow("Ім'я:", self.name_input)

        # Тип
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Воїн", "Маг", "Лучник", "Танк", "Підтримка"])
        self.type_combo.setFont(QFont('Arial', 11))
        form_layout.addRow("Тип:", self.type_combo)

        # Здоров'я
        self.health_input = QSpinBox()
        self.health_input.setRange(10, 1000)
        self.health_input.setValue(100)
        self.health_input.setFont(QFont('Arial', 11))
        form_layout.addRow("Здоров'я:", self.health_input)

        # Атака
        self.attack_input = QSpinBox()
        self.attack_input.setRange(5, 500)
        self.attack_input.setValue(50)
        self.attack_input.setFont(QFont('Arial', 11))
        form_layout.addRow("Атака:", self.attack_input)

        # URL зображення
        self.image_url_input = QLineEdit()
        self.image_url_input.setPlaceholderText("Необов'язково")
        self.image_url_input.setFont(QFont('Arial', 11))
        form_layout.addRow("URL зображення:", self.image_url_input)

        layout.addLayout(form_layout)
        layout.addSpacing(20)

        # Кнопки
        button_layout = QHBoxLayout()

        create_btn = QPushButton("✓ Створити")
        create_btn.clicked.connect(self.create_character)
        create_btn.setStyleSheet("""
            QPushButton {
                background-color: #5cb85c;
                color: white;
                padding: 10px 25px;
                border: none;
                border-radius: 5px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #449d44;
            }
        """)
        button_layout.addWidget(create_btn)

        cancel_btn = QPushButton("✗ Скасувати")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #d9534f;
                color: white;
                padding: 10px 25px;
                border: none;
                border-radius: 5px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #c9302c;
            }
        """)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

        # Фокус на ім'я
        self.name_input.setFocus()

    def create_character(self):
        """Створення персонажа"""
        name = self.name_input.text().strip()

        if not name:
            QMessageBox.warning(self, "Помилка", "Введіть ім'я персонажа!")
            return

        char_id = len(self.storage.get_all()) + 1
        char_type = self.type_combo.currentText()
        health = self.health_input.value()
        attack = self.attack_input.value()
        image_url = self.image_url_input.text().strip()

        self.result = Character(
            id=char_id,
            name=name,
            char_type=char_type,
            health=health,
            attack=attack,
            image_url=image_url
        )

        self.accept()

# === КАРТА ПЕРСОНАЖА ===
class CharacterCard(QFrame):

    def __init__(self, character, on_delete=None, parent=None):
        super().__init__(parent)
        self.character = character
        self.on_delete = on_delete
        self.setup_ui()

        # Стиль картки
        self.setFrameStyle(QFrame.Box | QFrame.Raised)
        self.setLineWidth(2)
        self.setStyleSheet("""
            CharacterCard {
                background-color: #f0f0f0;
                border: 2px solid #cccccc;
                border-radius: 10px;
                padding: 10px;
            }
            CharacterCard:hover {
                background-color: #e8e8e8;
                border: 2px solid #4a90e2;
            }
        """)

        # Робимо картку клікабельною
        self.setCursor(Qt.PointingHandCursor)

    def setup_ui(self):
        """Створення елементів картки"""
        layout = QVBoxLayout()

        # Зображення
        image_label = QLabel()
        image_label.setAlignment(Qt.AlignCenter)

        if self.character.local_image_path and os.path.exists(self.character.local_image_path):
            pixmap = QPixmap(self.character.local_image_path)
            pixmap = pixmap.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        else:
            # Placeholder
            pixmap = QPixmap(150, 150)
            pixmap.fill(Qt.lightGray)

        image_label.setPixmap(pixmap)
        layout.addWidget(image_label)

        # Ім'я
        name_label = QLabel(self.character.name)
        name_label.setFont(QFont('Arial', 12, QFont.Bold))
        name_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(name_label)

        # Тип
        type_label = QLabel(f"🎭 {self.character.type}")
        type_label.setAlignment(Qt.AlignCenter)
        type_label.setStyleSheet("color: #555555;")
        layout.addWidget(type_label)

        # Статистика
        stats_layout = QHBoxLayout()

        hp_label = QLabel(f"❤️ {self.character.health}")
        hp_label.setAlignment(Qt.AlignCenter)
        stats_layout.addWidget(hp_label)

        atk_label = QLabel(f"⚔️ {self.character.attack}")
        atk_label.setAlignment(Qt.AlignCenter)
        stats_layout.addWidget(atk_label)

        layout.addLayout(stats_layout)

        # Кнопка видалення
        if self.on_delete:
            delete_btn = QPushButton("🗑️ Видалити")
            delete_btn.clicked.connect(lambda: self.on_delete(self.character))
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #d9534f;
                    color: white;
                    padding: 5px;
                    border: none;
                    border-radius: 4px;
                    font-size: 10px;
                }
                QPushButton:hover {
                    background-color: #c9302c;
                }
            """)
            layout.addWidget(delete_btn)

        self.setLayout(layout)
        self.setFixedSize(200, 320)

    def mousePressEvent(self, event):
        """Обробка кліку"""
        if event.button() == Qt.LeftButton:
            # Перевіряємо, чи клік не на кнопці видалення
            widget = self.childAt(event.pos())
            if not isinstance(widget, QPushButton):
                self.show_details()

    def show_details(self):
        """Показ деталей персонажа"""
        dialog = CharacterDetailsDialog(self.character, self)
        dialog.exec_()

# === ВІКНО З ДЕТАЛЯМИ ПЕРСОНАЖА ===
class CharacterDetailsDialog(QDialog):

    def __init__(self, character, parent=None):
        super().__init__(parent)
        self.character = character
        self.setWindowTitle(f"Деталі: {character.name}")
        self.setFixedSize(400, 550)
        self.setup_ui()

    def setup_ui(self):
        """Інтерфейс"""
        layout = QVBoxLayout()

        # Зображення
        image_label = QLabel()
        image_label.setAlignment(Qt.AlignCenter)

        if self.character.local_image_path and os.path.exists(self.character.local_image_path):
            pixmap = QPixmap(self.character.local_image_path)
            pixmap = pixmap.scaled(250, 250, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        else:
            pixmap = QPixmap(250, 250)
            pixmap.fill(Qt.lightGray)

        image_label.setPixmap(pixmap)
        layout.addWidget(image_label)

        # Інформація
        info_widget = QWidget()
        info_layout = QVBoxLayout()

        # Ім'я
        name_label = QLabel(self.character.name)
        name_label.setFont(QFont('Arial', 18, QFont.Bold))
        name_label.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(name_label)

        # ID
        id_label = QLabel(f"ID: {self.character.id}")
        id_label.setStyleSheet("color: #666666;")
        id_label.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(id_label)

        # Розділювач
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        info_layout.addWidget(line)

        # Деталі
        details = [
            f"🎭 Тип: {self.character.type}",
            f"❤️ Здоров'я: {self.character.health}",
            f"⚔️ Атака: {self.character.attack}"
        ]

        for detail in details:
            label = QLabel(detail)
            label.setFont(QFont('Arial', 11))
            info_layout.addWidget(label)

        # URL
        if self.character.image_url:
            url_label = QLabel(f"🌐 URL: {self.character.image_url[:40]}...")
            url_label.setStyleSheet("color: #0275d8;")
            url_label.setWordWrap(True)
            info_layout.addWidget(url_label)

        # Статус зображення
        if self.character.local_image_path:
            status_label = QLabel("✅ Зображення збережено локально")
            status_label.setStyleSheet("color: #5cb85c;")
        else:
            status_label = QLabel("⚠️ Зображення не збережено")
            status_label.setStyleSheet("color: #f0ad4e;")

        info_layout.addWidget(status_label)

        info_widget.setLayout(info_layout)
        layout.addWidget(info_widget)

        # Кнопка закриття
        close_btn = QPushButton("Закрити")
        close_btn.clicked.connect(self.close)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #d9534f;
                color: white;
                padding: 8px;
                border: none;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #c9302c;
            }
        """)
        layout.addWidget(close_btn)

        self.setLayout(layout)

# === ІМПОРТ ПЕРСОНАЖІВ ===
class ImportDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Імпорт персонажів")
        self.setFixedSize(300, 150)
        self.count = 5
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Текст
        label = QLabel("Скільки персонажів завантажити?")
        label.setFont(QFont('Arial', 10))
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

        # Поле вводу
        self.spinbox = QSpinBox()
        self.spinbox.setMinimum(1)
        self.spinbox.setMaximum(50)
        self.spinbox.setValue(5)
        self.spinbox.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.spinbox)

        # Кнопки
        btn_layout = QHBoxLayout()

        ok_btn = QPushButton("Почати")
        ok_btn.clicked.connect(self.accept)
        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #0275d8;
                color: white;
                padding: 8px 20px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #025aa5;
            }
        """)
        btn_layout.addWidget(ok_btn)

        cancel_btn = QPushButton("Скасувати")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                padding: 8px 20px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def get_count(self):
        """Повертає вибрану кількість"""
        return self.spinbox.value()

# === ГОЛОВНЕ ВІКНО ===
class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Каталог персонажів Genshin Impact")
        self.setMinimumSize(950, 750)

        self.storage = DataStorage()
        self.api_client = GenshinAPIClient()
        self.parser = GenshinCharacterParser()
        self.img_manager = ImageManager()

        self.setup_ui()
        self.load_characters()

    def setup_ui(self):
        # Центральний віджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()

        # ЗАГОЛОВОК
        header = QWidget()
        header.setStyleSheet("background-color: #4a90e2; padding: 20px;")
        header_layout = QVBoxLayout()

        title = QLabel("🎮 Каталог персонажів Genshin Impact")
        title.setFont(QFont('Arial', 20, QFont.Bold))
        title.setStyleSheet("color: white;")
        title.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title)

        header.setLayout(header_layout)
        header.setFixedHeight(110)
        main_layout.addWidget(header)

        # ПАНЕЛЬ КНОПОК
        button_panel = QWidget()
        button_layout = QHBoxLayout()

        # Кнопка оновлення
        refresh_btn = QPushButton("🔄 Оновити")
        refresh_btn.clicked.connect(self.load_characters)
        refresh_btn.setStyleSheet(self.get_button_style('#5cb85c', '#449d44'))
        button_layout.addWidget(refresh_btn)

        # Кнопка додавання
        add_btn = QPushButton("➕ Додати персонажа")
        add_btn.clicked.connect(self.add_character)
        add_btn.setStyleSheet(self.get_button_style('#5cb85c', '#449d44'))
        button_layout.addWidget(add_btn)

        # Кнопка імпорту
        import_btn = QPushButton("⬇️ Імпорт з API")
        import_btn.clicked.connect(self.import_characters)
        import_btn.setStyleSheet(self.get_button_style('#0275d8', '#025aa5'))
        button_layout.addWidget(import_btn)

        # Кнопка статистики
        stats_btn = QPushButton("📊 Статистика")
        stats_btn.clicked.connect(self.show_stats)
        stats_btn.setStyleSheet(self.get_button_style('#f0ad4e', '#ec971f'))
        button_layout.addWidget(stats_btn)

        button_layout.addStretch()
        button_panel.setLayout(button_layout)
        main_layout.addWidget(button_panel)

        # ОБЛАСТЬ З КАРТКАМИ
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.cards_widget = QWidget()
        self.cards_layout = QGridLayout()
        self.cards_widget.setLayout(self.cards_layout)

        scroll_area.setWidget(self.cards_widget)
        main_layout.addWidget(scroll_area)

        # СТАТУС БАР
        self.status_label = QLabel("Готово до роботи")
        self.status_label.setStyleSheet("""
            background-color: #f8f9fa;
            padding: 8px;
            color: #666666;
        """)
        main_layout.addWidget(self.status_label)

        central_widget.setLayout(main_layout)

    def get_button_style(self, bg_color, hover_color):
        """Стиль для кнопок"""
        return f"""
            QPushButton {{
                background-color: {bg_color};
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            QPushButton:pressed {{
                background-color: {hover_color};
            }}
        """

    def clear_cards(self):
        """Очищення усіх карток"""
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def load_characters(self):
        """Завантаження персонажів"""
        self.clear_cards()

        characters = self.storage.get_all()

        if not characters:
            # Порожній список
            no_data = QLabel(
                "📭 Немає персонажів\n\nВикористайте:\n'➕ Додати персонажа' для ручного додавання\n'⬇️ Імпорт з API' для завантаження з інтернету")
            no_data.setFont(QFont('Arial', 13))
            no_data.setStyleSheet("color: #999999;")
            no_data.setAlignment(Qt.AlignCenter)
            self.cards_layout.addWidget(no_data, 0, 0, 1, 3)
            self.status_label.setText("Список порожній")
            return

        # Створюємо картки (3 колонки)
        row = 0
        col = 0
        max_cols = 3

        for char in characters:
            card = CharacterCard(char, on_delete=self.delete_character)
            self.cards_layout.addWidget(card, row, col)

            col += 1
            if col >= max_cols:
                col = 0
                row += 1

        self.status_label.setText(f"Завантажено {len(characters)} персонажів")

    def add_character(self):
        """Додавання персонажа"""
        dialog = AddCharacterDialog(self.storage, self)

        if dialog.exec_() == QDialog.Accepted and dialog.result:
            self.storage.add_character(dialog.result)
            QMessageBox.information(
                self,
                "Успіх",
                f"Персонаж '{dialog.result.name}' успішно створено!"
            )
            self.load_characters()

    def delete_character(self, character):
        """Видалення персонажа"""
        reply = QMessageBox.question(
            self,
            "Підтвердження видалення",
            f"Ви впевнені, що хочете видалити персонажа '{character.name}'?\n\nЦю дію не можна скасувати!",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # Видаляємо
            self.storage.characters = [c for c in self.storage.characters if c.id != character.id]
            self.storage.save()

            # Оновлюємо
            self.load_characters()

            QMessageBox.information(self, "Успіх", f"Персонаж '{character.name}' видалено!")
            self.status_label.setText(f"Видалено: {character.name}")

    def import_characters(self):
        """Імпорт персонажів"""
        dialog = ImportDialog(self)

        if dialog.exec_() == QDialog.Accepted:
            count = dialog.get_count()
            self.perform_import(count)

    def perform_import(self, count):
        """Виконання імпорту"""
        self.status_label.setText("Завантаження персонажів...")
        QApplication.processEvents()

        # Отримуємо список
        character_names = self.api_client.get_all_character_names()

        if not character_names:
            QMessageBox.critical(self, "Помилка", "Не вдалося завантажити список персонажів")
            self.status_label.setText("Помилка завантаження")
            return

        count = min(count, len(character_names))
        current_max_id = max([c.id for c in self.storage.get_all()], default=0)

        imported = 0
        images_downloaded = 0

        # Завантажуємо персонажів
        for i, name in enumerate(character_names[:count]):
            self.status_label.setText(f"Завантаження {i + 1}/{count}: {name}")
            QApplication.processEvents()

            details = self.api_client.get_character_details(name)
            if details:
                char = self.parser.parse_to_character(details, current_max_id + i + 1, Character)

                # Завантажуємо зображення
                local_path = self.img_manager.download_image(char.image_url, char.name)
                if local_path:
                    char.local_image_path = local_path
                    images_downloaded += 1

                self.storage.add_character(char)
                imported += 1

        # Оновлюємо список
        self.load_characters()

        # Показуємо результат
        QMessageBox.information(
            self,
            "Імпорт завершено",
            f"Успішно імпортовано: {imported} персонажів\n"
            f"Завантажено зображень: {images_downloaded}"
        )

        self.status_label.setText(f"Імпортовано {imported} персонажів")

    def show_stats(self):
        """Показуємо статистику"""
        total_chars = len(self.storage.get_all())
        cached_images = self.img_manager.get_cached_image_count()

        QMessageBox.information(
            self,
            "Статистика",
            f"📊 Статистика каталогу\n\n"
            f"Всього персонажів: {total_chars}\n"
            f"Збережено зображень: {cached_images}\n"
            f"Папка кешу: {self.img_manager.cache_dir}/"
        )

# === ЗАПУСК ===
def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()