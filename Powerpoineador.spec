# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, copy_metadata
import sys

# Recoger datos para replicate
replicate_datas = collect_data_files('replicate')
replicate_hidden_imports = collect_submodules('replicate')
replicate_metadata = copy_metadata('replicate')

# Determinar configuración específica de plataforma
is_mac = sys.platform == 'darwin'
icon_file = 'iconos/icon.icns' if is_mac else 'iconos/icon.ico'

a = Analysis(
    [
        'Powerpoineador.py',
        'Cifrado.py',
        'Plantillas.py',
        'Updater.py',
        'Temas.py',
        'Diseños_diapositivas.py',
        'apis/Google.py',
        'apis/Replicate.py',
        'apis/xAI.py',
        'modelos/IA_dgmtnzflux.py',
        'modelos/IA_dolphin.py',
        'modelos/IA_haiku.py',
        'modelos/IA_sonnet3_5.py',
        'modelos/IA_sonnet3_7.py',
        'modelos/IA_flux8.py',
        'modelos/IA_flux16.py',
        'modelos/IA_fluxpulid.py',
        'modelos/IA_fluxschnell.py',
        'modelos/IA_grok2.py',
        'modelos/IA_grok3.py',
        'modelos/IA_grok3_mini.py',
        'modelos/IA_grok3_mini_fast.py',
        'modelos/IA_grok2_image.py',
        'modelos/IA_gemini2_5_flash.py',
        'modelos/IA_gemini2_flash_thinking.py',
        'modelos/IA_gemini2_flash_image.py',
        'modelos/IA_o4_mini.py',
        'modelos/IA_gpt4o.py',
        'modelos/IA_gpt4o_mini.py',
        'modelos/IA_gpt4_1.py',
        'modelos/IA_gpt4_1_nano.py',
        'modelos/IA_llama3.py',
        'modelos/IA_llama4m.py',
        'modelos/IA_llama4s.py',
        'modelos/IA_photomaker.py',
        'modelos/IA_sdxl.py',
        'modelos/IA_deepseek.py',
        'modelos/IA_imagen3.py',
        'modelos/IA_imagen3fast.py',
        'modelos/IA_sana.py',
        'modelos/IA_model3_4.py',
        'Traducciones.py',
        'Logica_diapositivas.py',
        'Ventana_progreso.py',
        'Splash_carga.py',
        'Version_checker.py',
        'Vista_previa.py'
    ],
    pathex=[],
    binaries=[],
    datas=[
        ('iconos', 'iconos'),
        ('modelos/*.py', 'modelos/'),
    ] + replicate_datas + replicate_metadata,
    hiddenimports=[
        'replicate',
        'replicate.client',
        'replicate.exceptions',
        'replicate.prediction',
        'replicate.version',
        'replicate.files',
        'replicate.run',
        'replicate.stream',
        'deep_translator',
        'deep_translator.google_trans',
        'PySide6',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
    ] + replicate_hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

# Configuración común para EXE
exe_args = dict(
    pyz=pyz,
    a_scripts=a.scripts,
    exclude_binaries=True,
    name='Powerpoineador',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=icon_file,
)

# Configuración específica para cada plataforma
if is_mac:
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='Powerpoineador',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        console=False,
        icon=icon_file,
        target_arch=None,
    )
    
    # Añadir la configuración de BUNDLE para macOS
    app = BUNDLE(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        name='Powerpoineador.app',
        icon=icon_file,
        bundle_identifier='com.powerpoineador.app',
        info_plist={
            'NSHighResolutionCapable': 'True',
            'CFBundleShortVersionString': '0.2.0',
            'CFBundleVersion': '0.2.0',
            'NSHumanReadableCopyright': '© 2025 Powerpoineador',
            'NSPrincipalClass': 'NSApplication',
            'NSAppleScriptEnabled': False,
            'CFBundleDisplayName': 'Powerpoineador',
            'CFBundleName': 'Powerpoineador',
        },
    )
else:
    # Configuración para Windows
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        [],
        name='Powerpoineador',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=icon_file,
    )