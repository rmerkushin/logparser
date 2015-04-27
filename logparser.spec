# -*- mode: python -*-
a = Analysis(['logparser.py'],
             pathex=['/LogParser'],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='logparser',
          debug=False,
          strip=True,
          upx=False,
          console=True )
