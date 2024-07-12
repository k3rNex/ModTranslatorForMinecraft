# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],  # Список исходных файлов скрипта
    pathex=[],  # Список дополнительных путей, в которых PyInstaller будет искать модули
    binaries=[],  # Список дополнительных двоичных файлов (например, DLL), которые нужно включить в сборку
    datas=[('Translated_Lang_Files', 'Translated_Lang_Files')],  # Список данных для включения
    hiddenimports=[],  # Список модулей, которые нужно явно импортировать
    hookspath=[],  # Список путей к пользовательским хукам PyInstaller
    runtime_hooks=[],  # Список путей к runtime-хукам
    excludes=[],  # Список модулей, которые нужно исключить
    win_no_prefer_redirects=False,  # Настройки для сборки под Windows (использование библиотеки с переадресацией)
    win_private_assemblies=False,  # Настройки для сборки под Windows (использование частных сборок)
    cipher=block_cipher,  # Шифрование кода
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,  # Список скриптов для включения в exe
    [],
    exclude_binaries=True,  # Исключение двоичных файлов
    name='ModTranslatorForMinecraft',  # Имя исполняемого файла
    debug=False,  # Режим отладки
    bootloader_ignore_signals=False,  # Игнорирование сигналов для bootloader
    strip=False,  # Удаление символов отладки
    upx=True,  # Использование UPX для сжатия
    console=False,  # Отображение консоли (True) или скрытие (False)
    windowed=True,  # Скрытие консоли, если приложение с GUI
    icon='icon.ico'  # Путь к иконке
)

coll = COLLECT(
    exe,
    a.binaries,  # Включение двоичных файлов
    a.zipfiles,  # Включение zip-архивов
    a.datas,  # Включение данных
    strip=False,  # Удаление символов отладки
    upx=True,  # Использование UPX для сжатия
    upx_exclude=[],  # Список исключений для UPX
    name='ModTranslatorForMinecraft',  # Имя папки для конечного исполняемого файла
)
