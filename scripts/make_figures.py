import json, collections
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle
import numpy as np

R="./"
YEARS=[2020,2022,2024,2026]
H={y:json.load(open(f"{R}submission/{y}/hierarchy.json"))["supernodes"] for y in YEARS}
M=json.load(open(R+"metrics.json"))

def short(lbl,n=2):
    return " / ".join((lbl or "?").split(" / ")[:n])

# lineage colours keyed by persistent id at level 0
pids=[]
for y in YEARS:
    for s in H[y]:
        if s["level"]==0 and s["persistent_id"] not in pids: pids.append(s["persistent_id"])
cmap=plt.get_cmap("tab20")
COL={p:cmap(i%20) for i,p in enumerate(pids)}

# ---------- Fig 1: icicle levels 0-2 per snapshot ----------
def order_tree(sn):
    by={s["id"]:s for s in sn}
    kids=collections.defaultdict(list)
    for s in sn:
        if s["parent_id"]: kids[s["parent_id"]].append(s)
    roots=sorted([s for s in sn if s["level"]==0],key=lambda s:-len(s["member_ids"]))
    rows={0:[],1:[],2:[]}
    def rec(s,anc):
        rows[s["level"]].append((s,anc))
        if s["level"]<2:
            for c in sorted(kids[s["id"]],key=lambda c:-len(c["member_ids"])): rec(c,anc)
    for r in roots: rec(r,r["persistent_id"])
    return rows

fig,axes=plt.subplots(4,1,figsize=(13,9.2))
for ax,y in zip(axes,YEARS):
    rows=order_tree(H[y]); tot=sum(len(s["member_ids"]) for s,_ in rows[0])
    for lv in (0,1,2):
        x=0
        for s,anc in rows[lv]:
            w=len(s["member_ids"])/tot
            ax.add_patch(Rectangle((x,2-lv),w,0.92,facecolor=COL[anc],edgecolor="white",lw=0.4 if lv else 1.0,alpha=1 if lv==0 else (0.75 if lv==1 else 0.55)))
            if lv==0 and w>0.045:
                ax.text(x+w/2,2.46,f"{short(s['label'],1 if w<0.085 else 2)}\n{len(s['member_ids'])}",ha="center",va="center",fontsize=6.6,color="black")
            x+=w
    ax.set_xlim(0,1); ax.set_ylim(0,3)
    ax.set_yticks([2.46,1.46,0.46]); ax.set_yticklabels([f"L0  ({len(rows[0])})",f"L1  ({len(rows[1])})",f"L2  ({len(rows[2])})"],fontsize=8)
    ax.set_xticks([]); ax.set_ylabel(f"{y}\n{tot:,} nodes",rotation=0,ha="right",va="center",fontsize=10,labelpad=52)
    for sp in ax.spines.values(): sp.set_visible(False)
fig.suptitle("Multi-resolution hierarchy, levels 0–2, at each snapshot\n(width ∝ member nodes; colour = persistent level-0 lineage, so a colour recurring across years is the same tracked super-node)",fontsize=11)
fig.tight_layout(rect=[0,0,1,0.95]); fig.savefig("/mnt/user-data/outputs/fig1_levels_0-2_across_snapshots.png",dpi=200); plt.close(fig)

# ---------- Fig 2: level-0 flow between snapshots ----------
L0={y:{s["id"]:s for s in H[y] if s["level"]==0} for y in YEARS}
fig,ax=plt.subplots(figsize=(13,6.6))
gap=0.012; colx={y:i for i,y in enumerate(YEARS)}
pos={}  # (year,id)->(y0,y1)
for y in YEARS:
    ss=sorted(L0[y].values(),key=lambda s:-len(s["member_ids"])); tot=sum(len(s["member_ids"]) for s in ss)
    scale=(1-gap*(len(ss)-1))/tot; yy=1.0
    for s in ss:
        h=len(s["member_ids"])*scale; pos[(y,s["id"])]=(yy-h,yy,s); yy-=h+gap
def flows(y0,y1):
    ot=json.load(open(f"{R}submission/{y1}/temporal_events.json"))["k12"]["overlap_table"]
    out=collections.defaultdict(float); inn=collections.defaultdict(float)
    for r in sorted(ot,key=lambda r:-r["intersection_size"]):
        a=(y0,r["previous_group_id"]); b=(y1,r["current_group_id"])
        if a not in pos or b not in pos: continue
        sa=(pos[a][1]-pos[a][0])/len(pos[a][2]["member_ids"]); sb=(pos[b][1]-pos[b][0])/len(pos[b][2]["member_ids"])
        n=r["intersection_size"]
        ya=pos[a][1]-out[a]; yb=pos[b][1]-inn[b]
        out[a]+=n*sa; inn[b]+=n*sb
        x0=colx[y0]+0.05; x1=colx[y1]-0.05
        t=np.linspace(0,1,40); s=3*t**2-2*t**3
        top=ya+(yb-ya)*s; bot=(ya-n*sa)+((yb-n*sb)-(ya-n*sa))*s
        xs=x0+(x1-x0)*t
        ax.add_patch(Polygon(np.r_[np.c_[xs,top],np.c_[xs[::-1],bot[::-1]]],closed=True,facecolor=COL[pos[a][2]["persistent_id"]],alpha=0.4,lw=0))
for y0,y1 in zip(YEARS[:-1],YEARS[1:]): flows(y0,y1)
for (y,i),(a,b,s) in pos.items():
    ax.add_patch(Rectangle((colx[y]-0.05,a),0.10,b-a,facecolor=COL[s["persistent_id"]],edgecolor="black",lw=0.5))
    if b-a>0.035:
        ax.text(colx[y]+(0.07 if y!=YEARS[-1] else 0.07),(a+b)/2,f"{short(s['label'])} ({len(s['member_ids'])})",fontsize=6.3,va="center")
ax.set_xlim(-0.35,3.75); ax.set_ylim(-0.02,1.02)
ax.set_xticks(range(4)); ax.set_xticklabels([f"{y}" for y in YEARS],fontsize=11); ax.set_yticks([])
for sp in ax.spines.values(): sp.set_visible(False)
ax.set_title("Level-0 super-node flow across snapshots (k=12)\nribbons = shared nodes between consecutive snapshots; block height ∝ size; labels = extractive keywords",fontsize=11)
fig.tight_layout(); fig.savefig("/mnt/user-data/outputs/fig2_level0_flow_across_snapshots.png",dpi=200); plt.close(fig)

# ---------- Fig 3: evidence ----------
fig,axs=plt.subplots(1,3,figsize=(14,4.3))
# (a) coherence vs null
ax=axs[0]; ks=["k12","k48","k120"]; c=M["coherence_type_preserving_null"]
act=[c[k]["actual"]["group_weighted_mean"] for k in ks]
nm=[c[k]["null_summary"]["group_weighted_mean"]["mean"] for k in ks]; ns=[c[k]["null_summary"]["group_weighted_mean"]["stdev"] for k in ks]
x=np.arange(3); ax.bar(x-0.18,act,0.36,label="method (2024, γ=0.1)",color="#2a6f97"); ax.bar(x+0.18,nm,0.36,yerr=ns,label="type-preserving null",color="#b0b0b0",capsize=3)
ax.set_xticks(x); ax.set_xticklabels(ks); ax.set_ylabel("char n-gram TF-IDF centroid cosine"); ax.set_title("(a) Coherence vs null\n(independent of clustering embedding)",fontsize=10); ax.legend(fontsize=8)
# (b) cross-snapshot ARI
ax=axs[1]; lab=[];i=0
for tr in ["2020_2022","2022_2024"]:
    for g,col in [("gamma0","#9c6644"),("gamma0p1","#2a6f97")]:
        d=M["cross_snapshot"][f"stability_bootstrap_{tr}_{g}"]
        for j,k in enumerate(ks):
            xx=(0 if tr=="2020_2022" else 4)+j+(0.0 if g=="gamma0" else 0.0)
        pass
w=0.36
for t,tr in enumerate(["2020_2022","2022_2024"]):
    for j,k in enumerate(ks):
        for gi,(g,col) in enumerate([("gamma0","#9c6644"),("gamma0p1","#2a6f97")]):
            d=M["cross_snapshot"][f"stability_bootstrap_{tr}_{g}"][k]
            xx=t*4+j+(gi-0.5)*w
            ax.errorbar(xx,d["ari"],yerr=[[d["ari"]-d["ci95"][0]],[d["ci95"][1]-d["ari"]]],fmt="o",color=col,capsize=3,label=("γ=0" if gi==0 else "γ=0.1") if (t==0 and j==0) else None)
ax.set_xticks([0,1,2,4,5,6]); ax.set_xticklabels(["k12","k48","k120"]*2,fontsize=8)
ax.text(1,-0.13,"2020→2022",ha="center",transform=ax.get_xaxis_transform()); ax.text(5,-0.13,"2022→2024",ha="center",transform=ax.get_xaxis_transform())
ax.set_ylim(0,0.8); ax.set_ylabel("ARI on shared nodes (95% bootstrap CI)"); ax.set_title("(b) Cross-snapshot stability",fontsize=10); ax.legend(fontsize=8)
# (c) perturbation ARI
ax=axs[2]
for t,yr in enumerate(["2022","2024"]):
    for j,k in enumerate(ks):
        for gi,(g,col) in enumerate([("gamma0","#9c6644"),("gamma0p1","#2a6f97")]):
            d=M["perturbation"][yr][k][g]; xx=t*4+j+(gi-0.5)*w
            ax.errorbar(xx,d["mean"],yerr=[[d["mean"]-d["approx_95_ci"][0]],[d["approx_95_ci"][1]-d["mean"]]],fmt="o",color=col,capsize=3)
ax.set_xticks([0,1,2,4,5,6]); ax.set_xticklabels(["k12","k48","k120"]*2,fontsize=8)
ax.text(1,-0.13,"2022",ha="center",transform=ax.get_xaxis_transform()); ax.text(5,-0.13,"2024",ha="center",transform=ax.get_xaxis_transform())
ax.set_ylim(0,1); ax.set_ylabel("ARI vs unperturbed (mean, t-interval, n=5)"); ax.set_title("(c) 10% hyperedge-removal perturbation",fontsize=10)
fig.tight_layout(); fig.savefig("/mnt/user-data/outputs/fig3_evidence_summary.png",dpi=200); plt.close(fig)
print("ok")
