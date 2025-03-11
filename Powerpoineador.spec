# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_data_files, collect_submodules, copy_metadata

replicate_datas = collect_data_files('replicate')
replicate_hidden_imports = collect_submodules('replicate')
replicate_metadata = copy_metadata('replicate')

a = Analysis(
    [
        'Powerpoineador.py',
        'Diseños_diapositivas.py',
        'apis/Replicate.py',
        'apis/xAI.py',
        'modelos/IA_dgmtnzflux.py',
        'modelos/IA_dolphin.py',
        'modelos/IA_haiku.py',
        'modelos/IA_sonnet_3_5.py',
        'modelos/IA_sonnet_3_7.py',
        'modelos/IA_flux8.py',
        'modelos/IA_flux16.py',
        'modelos/IA_fluxpulid.py',
        'modelos/IA_fluxschnell.py',
        'modelos/IA_grok.py',
        'modelos/IA_llama.py',
        'modelos/IA_photomaker.py',
        'modelos/IA_sdxl.py',
        'modelos/IA_deepseek.py',
        'modelos/IA_imagen3.py',
        'modelos/IA_imagen3fast.py',
        'modelos/IA_sana.py',
        'modelos/IA_model3_4.py',
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
    ] + replicate_hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

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
    icon='iconos/icon.ico',
)