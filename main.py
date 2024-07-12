import tkinter as tk
from tkinter import filedialog, scrolledtext
import threading
import os
import zipfile
from deep_translator import GoogleTranslator
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import json
import time

class MinecraftTranslatorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Переводчик модов Minecraft")
        self.geometry("1000x600")

        self.translator = GoogleTranslator(source='en', target='ru')
        self.file_paths = []
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.translation_executor = ThreadPoolExecutor(max_workers=8)  # Пул потоков для перевода строк

        self.create_widgets()

    def create_widgets(self):
        frame = tk.Frame(self)
        frame.pack(pady=10, padx=10, fill=tk.X)

        self.load_button = tk.Button(frame, text="Загрузить моды", command=self.load_files)
        self.load_button.pack(side=tk.LEFT, padx=5)

        self.start_button = tk.Button(frame, text="Начать перевод", command=self.start_translation)
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.progress_label = tk.Label(frame, text="Прогресс: 0 / 0")
        self.progress_label.pack(side=tk.LEFT, padx=5)

        listbox_frame = tk.Frame(self)
        listbox_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        self.mod_listbox = tk.Listbox(listbox_frame, selectmode=tk.SINGLE)
        self.mod_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        self.translated_listbox = tk.Listbox(listbox_frame, selectmode=tk.SINGLE)
        self.translated_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        self.not_needed_listbox = tk.Listbox(listbox_frame, selectmode=tk.SINGLE)
        self.not_needed_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        self.console = scrolledtext.ScrolledText(self, state='disabled', height=10)
        self.console.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.listbox_labels = {
            "loaded": tk.Label(listbox_frame, text="Загруженные моды"),
            "translated": tk.Label(listbox_frame, text="Переведенные моды"),
            "not_needed": tk.Label(listbox_frame, text="Не нуждаются в переводе")
        }

        self.listbox_labels["loaded"].pack(side=tk.LEFT, padx=5, anchor='n')
        self.listbox_labels["translated"].pack(side=tk.LEFT, padx=5, anchor='n')
        self.listbox_labels["not_needed"].pack(side=tk.LEFT, padx=5, anchor='n')

    def load_files(self):
        paths = filedialog.askopenfilenames(filetypes=[("Jar files", "*.jar"), ("JSON files", "*.json")])
        self.file_paths.extend(paths)
        self.update_mod_list()
        self.log_to_console("Загружены файлы: " + ", ".join(paths))

    def update_mod_list(self):
        self.mod_listbox.delete(0, tk.END)
        for path in self.file_paths:
            self.mod_listbox.insert(tk.END, os.path.basename(path))

    def start_translation(self):
        threading.Thread(target=self.translate_files).start()

    def translate_files(self):
        total_files = len(self.file_paths)
        completed_files = 0
        self.update_progress(completed_files, total_files)

        futures = [self.executor.submit(self.translate_file, file_path) for file_path in self.file_paths]
        for future in as_completed(futures):
            result = future.result()
            self.log_to_console(result)
            completed_files += 1
            self.update_progress(completed_files, total_files)

    def translate_file(self, file_path):
        try:
            self.log_to_console(f"Начинаем обработку файла: {file_path}")
            if file_path.endswith(".jar"):
                self.process_jar_file(file_path)
            elif file_path.endswith(".json"):
                self.process_single_json_file(file_path)
            self.translated_listbox.insert(tk.END, os.path.basename(file_path))
            return f"Обработка файла завершена: {file_path}"
        except Exception as e:
            self.not_needed_listbox.insert(tk.END, os.path.basename(file_path))
            return f"Ошибка при обработке файла {file_path}: {str(e)}"

    def process_jar_file(self, file_path):
        has_english = False
        has_russian = False

        self.log_to_console("Открытие файла: " + file_path)
        with zipfile.ZipFile(file_path, 'r') as jar:
            lang_files = [f for f in jar.namelist() if
                          "assets" in f and "lang" in f and (f.endswith(".lang") or f.endswith(".json"))]

            self.log_to_console("Найденные файлы локализации: " + ", ".join(lang_files))

            # Check for English and Russian localization files
            for lang_file in lang_files:
                if "en_us.lang" in lang_file or "en_us.json" in lang_file:
                    has_english = True
                elif "ru_ru.lang" in lang_file or "ru_ru.json" in lang_file:
                    has_russian = True

            if has_russian:
                self.log_to_console(f"Русская локализация уже существует в моде: {file_path}")
                self.not_needed_listbox.insert(tk.END, os.path.basename(file_path))
                return

            if not has_english:
                self.log_to_console(f"Нет английского файла локализации в моде: {file_path}")
                self.not_needed_listbox.insert(tk.END, os.path.basename(file_path))
                return

            self.log_to_console("Начинаем перевод файлов")
            translated_files = {}
            for lang_file in lang_files:
                base_path = os.path.dirname(lang_file)
                if "en_us.lang" in lang_file:
                    with jar.open(lang_file) as f:
                        content = f.read().decode('utf-8')
                        self.log_to_console(f"Перевод файла: {lang_file}")
                        translated_content = self.translate_text(content)
                        self.log_to_console(f"Перевод завершен для файла: {lang_file}\n{translated_content[:500]}")
                        translated_files[os.path.join(base_path, "ru_ru.lang")] = translated_content
                        # Save translated lang file separately
                        self.save_translated_file(os.path.join(base_path, "ru_ru.lang"), translated_content)
                elif "en_us.json" in lang_file:
                    with jar.open(lang_file) as f:
                        content = f.read().decode('utf-8')
                        self.log_to_console(f"Перевод файла: {lang_file}")
                        data = json.loads(content)
                        translated_data = self.translate_json(data)
                        translated_content = json.dumps(translated_data, ensure_ascii=False, indent=4)
                        self.log_to_console(f"Перевод завершен для файла: {lang_file}\n{translated_content[:500]}")
                        translated_files[os.path.join(base_path, "ru_ru.json")] = translated_content
                        # Save translated json file separately
                        self.save_translated_file(os.path.join(base_path, "ru_ru.json"), translated_content)

            self.log_to_console("Создание переведенного JAR файла")
            translated_jar_path = os.path.join("Translated", os.path.basename(file_path))
            with zipfile.ZipFile(translated_jar_path, 'w') as new_jar:
                for file in jar.namelist():
                    if file in translated_files:
                        new_jar_file_path = os.path.join(os.path.dirname(file), "ru_ru" + os.path.splitext(file)[1])
                        self.log_to_console(f"Добавление файла в JAR: {new_jar_file_path}")
                        new_jar.writestr(new_jar_file_path, translated_files[os.path.join(os.path.dirname(file), "ru_ru" + os.path.splitext(file)[1])].encode('utf-8'))
                    else:
                        new_jar.writestr(file, jar.read(file))

                # Добавление новых русских файлов в JAR
                for translated_file_path, translated_content in translated_files.items():
                    self.log_to_console(f"Добавление файла в JAR: {translated_file_path}")
                    new_jar.writestr(translated_file_path, translated_content.encode('utf-8'))

            self.log_to_console("Список файлов локализации в новом JAR:")
            with zipfile.ZipFile(translated_jar_path, 'r') as new_jar:
                lang_files_in_new_jar = [f for f in new_jar.namelist() if "assets" in f and "lang" in f]
                self.log_to_console(", ".join(lang_files_in_new_jar))
            self.log_to_console(f"Сохранен переведенный файл: {translated_jar_path}")

    def save_translated_file(self, lang_file, content):
        output_dir = "Translated_Lang_Files"
        output_path = os.path.join(output_dir, lang_file)
        output_dirname = os.path.dirname(output_path)
        if not os.path.exists(output_dirname):
            os.makedirs(output_dirname)
        self.log_to_console(f"Сохранение переведенного файла отдельно: {output_path}")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        self.log_to_console(f"Файл сохранен отдельно: {output_path}")

    def translate_text(self, text, attempts=3, chunk_size=4500):
        def chunk_text_by_lines(text, size):
            lines = text.splitlines(keepends=True)
            chunks = []
            current_chunk = []
            current_length = 0

            for line in lines:
                if current_length + len(line) > size:
                    chunks.append(''.join(current_chunk))
                    current_chunk = []
                    current_length = 0
                current_chunk.append(line)
                current_length += len(line)

            if current_chunk:
                chunks.append(''.join(current_chunk))

            return chunks

        translated_chunks = []
        for chunk in chunk_text_by_lines(text, chunk_size):
            for attempt in range(attempts):
                try:
                    self.log_to_console(f"Попытка перевода текста (попытка {attempt+1}): {chunk[:30]}...")
                    translated_chunk = self.translator.translate(chunk)
                    translated_chunks.append(translated_chunk)
                    break
                except Exception as e:
                    self.log_to_console(f"Ошибка при переводе текста (попытка {attempt+1}): {chunk[:30]} -> {str(e)}")
                    if attempt < attempts - 1:
                        time.sleep(1)  # Задержка перед повторной попыткой
                    else:
                        translated_chunks.append(chunk)  # На случай ошибки оставить оригинальное значение
        return ''.join(translated_chunks)

    def translate_json(self, data, attempts=3, chunk_size=4500):
        text_data = json.dumps(data, ensure_ascii=False, indent=4)
        translated_text = self.translate_text(text_data, attempts=attempts, chunk_size=chunk_size)
        return json.loads(translated_text)

    def process_single_json_file(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        translated_data = self.translate_json(data)

        translated_file_path = os.path.join("Translated", os.path.basename(file_path).replace("en_us", "ru_ru"))
        self.log_to_console(f"Сохранение переведенного файла: {translated_file_path}")
        with open(translated_file_path, 'w', encoding='utf-8') as f:
            json.dump(translated_data, f, ensure_ascii=False, indent=4)

        self.log_to_console(f"Сохранен переведенный файл: {translated_file_path}")

    def log_to_console(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.console.configure(state='normal')
        self.console.insert(tk.END, f"[{timestamp}] {message}\n")
        self.console.configure(state='disabled')
        self.console.yview(tk.END)

    def update_progress(self, completed, total):
        self.progress_label.config(text=f"Прогресс: {completed} / {total}")

if __name__ == "__main__":
    if not os.path.exists("Translated"):
        os.makedirs("Translated")

    app = MinecraftTranslatorApp()
    app.mainloop()
