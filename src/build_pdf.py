"""Build the employer report and retain only the requested PDF metadata."""
import shutil
import subprocess
import matplotlib
from pathlib import Path
from pypdf import PdfReader,PdfWriter
from .publish_report import generate
ROOT=Path(__file__).resolve().parents[1]


def main():
    generate()
    staging=ROOT/'.artifacts/report';staging.mkdir(parents=True,exist_ok=True)
    # The pinned Matplotlib distribution supplies the same font files on both platforms.
    fonts = staging / "fonts"
    fonts.mkdir(exist_ok=True)
    source = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
    for family in ("DejaVuSans", "DejaVuSerif"):
        for font in source.glob(f"{family}*.ttf"):
            shutil.copyfile(font, fonts / font.name)
    raw=staging/'report.pdf'
    subprocess.run(['pandoc','reports/report_body.md','--standalone','--pdf-engine=xelatex','-V','papersize=letter','-V','geometry:margin=1in','-V','fontsize=11pt','-V','numbersections=false','-H','reports/layout.tex','--include-before-body=reports/cover.tex','-o',str(raw)],cwd=ROOT,check=True)
    writer=PdfWriter();writer.clone_document_from_reader(PdfReader(raw));writer.metadata=None
    writer.add_metadata({'/Title':'California Grid Analytics','/Author':'Sileshi Hirpa','/Subject':'Audited grid demand and forecast evaluation','/Keywords':'California, grid, forecasting, data quality'})
    with (ROOT/'reports/California_Grid_Analytics_Report_Sileshi_Hirpa.pdf').open('wb') as f:writer.write(f)
    print('PDF pages:',len(writer.pages))


if __name__=='__main__':main()
