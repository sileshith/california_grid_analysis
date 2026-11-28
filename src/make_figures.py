"""Render publication figures from saved metric JSON."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]


def generate():
    metrics=ROOT/'outputs/metrics';out=ROOT/'assets/figures';out.mkdir(parents=True,exist_ok=True)
    stats=json.loads((metrics/'forecast_benchmark.json').read_text())
    diag=json.loads((metrics/'operator_diagnostics.json').read_text())
    plt.rcParams.update({'font.family':'DejaVu Sans','pdf.fonttype':42,'font.size':11,'axes.spines.top':False,'axes.spines.right':False,'text.color':'#777777','axes.labelcolor':'#777777','xtick.color':'#777777','ytick.color':'#777777','axes.edgecolor':'#777777','svg.fonttype':'path','svg.hashsalt':'california-grid-v1'})
    def save(fig,name):
        for ext in ['svg','png','pdf']:
            meta={'Creator':None,'Date':None} if ext=='svg' else {'Creator':None,'Producer':None,'CreationDate':None,'ModDate':None} if ext=='pdf' else {'Software':None}
            fig.savefig(out/f'{name}.{ext}',bbox_inches='tight',transparent=True,dpi=180,metadata=meta)
        svg=out/f'{name}.svg';svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n')
        p=out/f'{name}.png';im=Image.open(p);im.save(p)
        plt.close(fig)
    authorities=sorted({r['balancing_authority'] for r in stats['authority_metrics']})
    by={(r['balancing_authority'],r['method']):r['daily_mae_mw'] for r in stats['authority_metrics']}
    ratios=[by[ba,stats['candidate']]/by[ba,'authority'] for ba in authorities]
    fig,ax=plt.subplots(figsize=(7,3.7),layout='constrained')
    labels=authorities+['G'];values=ratios+[stats['g']]
    ax.scatter(values,range(len(labels)),color='#0072B2',s=55,zorder=3)
    upper=stats['upper95'][str(stats['block_days'])]
    ax.plot([stats['g'],upper],[len(authorities)]*2,color='#D55E00',linewidth=3)
    ax.plot([upper]*2,[len(authorities)-.12,len(authorities)+.12],color='#D55E00')
    ax.axvline(1,color='#777777',linestyle='--',linewidth=1)
    ax.set_xscale('log');ax.set_yticks(range(len(labels)),labels);ax.invert_yaxis()
    from matplotlib.ticker import NullFormatter
    ax.set_xticks([0.5,1,2,3],['0.5','1','2','3'])
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.text(1.02,0.04,'Parity',transform=ax.get_xaxis_transform(),color='#777777')
    ax.set_xlabel('Model / operator daily MAE ratio (log scale)');ax.set_ylabel('Authority')
    save(fig,'relative_mae')
    r=next(r for r in diag['diagnostics'] if r['authority']=='CISO' and r['target']=='adjusted' and r['shift_hours']==0)
    fig,ax=plt.subplots(figsize=(7,3.5),layout='constrained')
    h=[v['hour'] for v in r['by_local_hour']];b=[v['bias_mw'] for v in r['by_local_hour']]
    ax.bar(h,b,color=['#0072B2' if v<0 else '#D55E00' for v in b],width=.8)
    ax.axhline(0,color='#777777',linewidth=.8);ax.set_xticks(range(0,24,3));ax.set_xlabel('Pacific delivery interval start hour');ax.set_ylabel('Operator forecast minus adjusted demand (MW)')
    save(fig,'ciso_bias')
    fig,ax=plt.subplots(figsize=(7,2.5),layout='constrained');ax.set_axis_off()
    boxes=[(.03,.55,'EIA vintages\nSource manifest'),(.37,.55,'Contracts\nFlag and preserve'),(.71,.55,'Interval store\nRevision history'),(.37,.05,'Frozen predictions\nPaired evaluation'),(.71,.05,'Metrics JSON\nReport and monitoring')]
    for x,y,label in boxes:ax.text(x+.12,y+.12,label,ha='center',va='center',bbox=dict(boxstyle='round,pad=.6',facecolor='none',edgecolor='#0072B2'),transform=ax.transAxes)
    for a,b in [((.28,.67),(.36,.67)),((.62,.67),(.70,.67)),((.49,.5),(.49,.34)),((.62,.17),(.70,.17))]:ax.annotate('',xy=b,xytext=a,xycoords='axes fraction',arrowprops=dict(arrowstyle='->',color='#777777'))
    save(fig,'architecture')


if __name__=='__main__':generate()
