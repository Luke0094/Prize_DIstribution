# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('locales', 'locales')],  # Include la cartella locales con i file it.json, en.json, fr.json, ru.json
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,                         # PyInstaller inserisce qui tutti i dati di 'a.datas' per il build --onefile
    [],
    name='PrizeDistribution',        # Nome del file eseguibile finale (.exe)
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,                        # Abilita la compressione UPX per ridurre ulteriormente il peso finale se installato nel sistema
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,                   # False equivale all'opzione --noconsole: nasconde il prompt dei comandi nero all'avvio
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)