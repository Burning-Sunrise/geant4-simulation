"""Integrate FE moments over recorded primary steps (small-angle slab geometry)."""
import csv
from pathlib import Path
import numpy as np
import uproot
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from analyze_momentum_scan import fermi_eyges_ratio_from_linear_energy_loss

BASE = Path(__file__).resolve().parent
SCAN = BASE / 'momentum_scan_step_energy_100000'
OUT = SCAN / 'output'
OUT.mkdir(exist_ok=True)
M = 105.6583755

def analyze(path):
    p = float(path.name.split('_p')[1].split('_')[0])
    with uproot.open(path) as f:
        e = f['Exit'].arrays(library='np')
        s = f['StepDebug'].arrays(library='np')
    good = (e['entered'] != 0) & (np.abs(e['entry_pos_z']+500)<1e-4) & (np.abs(e['exit_pos_z']-500)<1e-4)
    ids = e['Event_no'][good]
    take = np.isin(s['Event_no'], ids) & (s['pre_volume_code']==1)
    s = {k:v[take] for k,v in s.items()}
    # Reconstruct endpoint kinetic energies from the recorded momentum vectors.
    pre2 = sum(s['pre_p'+a]**2 for a in 'xyz')
    post2 = sum(s['post_p'+a]**2 for a in 'xyz')
    k0 = pre2 / (np.sqrt(pre2+M*M)+M)
    k1 = post2 / (np.sqrt(post2+M*M)+M)
    # Three-point Gauss integration within each actual Geant4 step; energy
    # is interpolated only across that step, not across the whole gas box.
    nodes, weights = np.polynomial.legendre.leggauss(3)
    a0 = np.zeros(len(k0)); a2 = np.zeros(len(k0))
    for t,w in zip((nodes+1)/2, weights/2):
        k = k0+(k1-k0)*t
        p2 = k*(k+2*M)
        power = (k+M)**2 / p2**2
        z = s['pre_z']+(s['post_z']-s['pre_z'])*t
        inc = w*s['step_length']*power
        a0 += inc
        a2 += inc*((500-z)/1000)**2
    # Ratio of ensemble second moments, not mean of eventwise ratios.
    step_ratio = np.sqrt(a0.sum()/a2.sum())
    linear = fermi_eyges_ratio_from_linear_energy_loss(e['entry_KE'][good].mean(), e['KE'][good].mean())
    event_ids, inv = np.unique(s['Event_no'], return_inverse=True)
    v0 = np.bincount(inv,weights=a0); v2=np.bincount(inv,weights=a2)
    groups=np.array_split(np.arange(len(event_ids)),100)
    estimates=np.array([np.sqrt(v0[g].sum()/v2[g].sum()) for g in groups])
    se=estimates.std(ddof=1)/np.sqrt(len(groups))
    return dict(momentum=p,accepted=len(ids),steps=len(k0),step_FE=step_ratio,step_SE=se,linear_FE=linear)

if __name__=='__main__':
    rows=sorted([analyze(p) for p in (SCAN/'root').glob('*.root')],key=lambda r:r['momentum'])
    with (OUT/'step_energy_comparison.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=rows[0].keys());writer.writeheader();writer.writerows(rows)
    with (BASE/'momentum_scan_1000000_events/output/momentum_scan.csv').open() as f:
        old=list(csv.DictReader(f))
    fig,ax=plt.subplots(figsize=(9,6))
    ax.errorbar([float(r['momentum_in_MeV_c']) for r in old],[float(r['theta_over_psi']) for r in old],yerr=[float(r['theta_over_psi_SE']) for r in old],fmt='o',capsize=3,label='Geant4 full RMS: original 1M events/point')
    x=[r['momentum'] for r in rows]
    ax.plot(x,[r['linear_FE'] for r in rows],'--',color='red',label='FE: linear mean endpoint energy (new sample)')
    ax.errorbar(x,[r['step_FE'] for r in rows],yerr=[r['step_SE'] for r in rows],fmt='s-',color='green',capsize=3,label='FE: recorded step energies, 100k events/point')
    ax.axhline(np.sqrt(3),ls=':',color='black',label=r'$\sqrt{3}$')
    ax.set(xscale='log',xlabel='Incident muon momentum [MeV/c]',ylabel=r'$\sigma_\theta/\sigma_\psi$')
    ax.grid(alpha=.2,which='both');ax.legend(fontsize=9);fig.tight_layout()
    fig.savefig(OUT/'step_energy_comparison.png',dpi=220)
    fig.savefig(OUT/'step_energy_comparison.pdf')
    for r in rows: print(r,flush=True)
