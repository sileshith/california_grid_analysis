# Report fonts

The unmodified OpenType files are vendored from TeX Live 2025: XCharter 1.26 and TeX Gyre Heros. XCharter's Bitstream license and copyright notices are reproduced in XCharter-LICENSE.txt; Heros is distributed under GUST-FONT-LICENSE.txt. Upstream packages: https://ctan.org/pkg/xcharter and https://ctan.org/pkg/tex-gyre.

`reports/layout.tex` loads these exact files with fontspec. Figure generation registers these same Heros files with Matplotlib; no system font installation or download is needed by CI. `manifest.json` records SHA-256 digests of the vendored font files.
