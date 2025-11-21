#image_manager.py
import os
import requests


# === УПРАВЛЯННЯ ЗАВАНТАЖЕННЯМИ ТА ЗБЕРЕЖЕННЯ ЗОБРАЖЕНЬ ===
class ImageManager:

    def __init__(self, cache_dir='character_images'):
        """ cache_dir: назва папки для зберігання зображень """
        self.cache_dir = cache_dir
        self._create_cache_directory()

    def _create_cache_directory(self):
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
            print(f"✓ Створено папку для зображень: {self.cache_dir}/")

    def get_local_image_path(self, character_name):
        safe_name = character_name.lower().replace(' ', '_')
        return os.path.join(self.cache_dir, f"{safe_name}.png")

    def image_exists_locally(self, character_name):
        """ Перевіряє, чи існує зображення локально """
        local_path = self.get_local_image_path(character_name)
        return os.path.exists(local_path)

    def download_image(self, image_url, character_name):
        """ Завантажує зображення з інтернету та зберігає локально """
        # Перевіряємо, чи вже є зображення
        if self.image_exists_locally(character_name):
            local_path = self.get_local_image_path(character_name)
            print(f"  ℹ️  Зображення вже існує: {local_path}")
            return local_path

        try:
            print(f"  ⬇️  Завантаження зображення з {image_url}...")
            response = requests.get(image_url, timeout=10)

            if response.status_code == 200:
                local_path = self.get_local_image_path(character_name)

                with open(local_path, 'wb') as f:
                    f.write(response.content)

                print(f"  ✓ Зображення збережено: {local_path}")
                return local_path
            else:
                print(f"  ❌ Помилка завантаження: HTTP {response.status_code}")
                return None

        except requests.exceptions.Timeout:
            print(f"  ❌ Час очікування вичерпано")
            return None
        except Exception as e:
            print(f"  ❌ Помилка: {e}")
            return None

    def get_cached_image_count(self):
        """ Повертає кількість збережених зображень """
        if not os.path.exists(self.cache_dir):
            return 0

        files = [f for f in os.listdir(self.cache_dir)
                 if f.endswith('.png') or f.endswith('.jpg')]
        return len(files)

    def clear_cache(self):
        """ Видаляє всі кешовані зображення """
        if not os.path.exists(self.cache_dir):
            print("Кеш порожній")
            return

        files = os.listdir(self.cache_dir)
        for file in files:
            file_path = os.path.join(self.cache_dir, file)
            os.remove(file_path)

        print(f"✓ Видалено {len(files)} файлів з кешу")