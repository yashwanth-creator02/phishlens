import textwrap, math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle, Circle
plt.rcParams["font.family"]="DejaVu Sans"
BLUE="#2F5597"; FILL="#EAF1FB"; DARK="#1F2937"; GREY="#44546A"

def snake(steps, ncols, fname, fig_w=6.8):
    n=len(steps); rows=math.ceil(n/ncols)
    mx=0.2; gap=0.32
    bw=(fig_w-2*mx-(ncols-1)*gap)/ncols
    cw=max(10,int((bw-0.22)/0.068))
    wrapped=[]
    for t,s in steps:
        tl=textwrap.wrap(t,int((bw-0.22)/0.08)) ; sl=textwrap.wrap(s,cw)
        wrapped.append((tl,sl))
    maxl=max(len(a)+len(b) for a,b in wrapped)
    bh=0.3+maxl*0.15+0.12
    vgap=0.5
    fig_h=2*0.12+rows*bh+(rows-1)*vgap
    fig,ax=plt.subplots(figsize=(fig_w,fig_h),dpi=300)
    ax.set_xlim(0,fig_w); ax.set_ylim(0,fig_h); ax.axis("off")
    pos=[]
    for i in range(n):
        r=i//ncols; c=i%ncols
        if r%2==1: c=ncols-1-c
        x=mx+c*(bw+gap); y=fig_h-0.12-(r+1)*bh-r*vgap
        pos.append((x,y))
    for i,((x,y),(tl,sl),(t,s)) in enumerate(zip(pos,wrapped,steps)):
        ax.add_patch(FancyBboxPatch((x,y),bw,bh,boxstyle="round,pad=0,rounding_size=0.08",fc=FILL,ec=BLUE,lw=1.1))
        ax.add_patch(Circle((x+0.02,y+bh-0.02),0.11,fc=BLUE,ec="white",lw=1.2,zorder=5))
        ax.text(x+0.02,y+bh-0.02,str(i+1),color="white",ha="center",va="center",fontsize=7.5,fontweight="bold",zorder=6)
        ty=y+bh-0.2
        for k,line in enumerate(tl):
            ax.text(x+0.11,ty-k*0.15,line,ha="left",va="center",fontsize=8.5,fontweight="bold",color=DARK)
        sy=ty-len(tl)*0.15-0.08
        for k,line in enumerate(sl):
            ax.text(x+0.11,sy-k*0.14,line,ha="left",va="center",fontsize=7.5,color=GREY)
    for i in range(n-1):
        (x1,y1),(x2,y2)=pos[i],pos[i+1]
        if abs(y1-y2)<1e-6:
            if x2>x1: a=(x1+bw,y1+bh/2); b=(x2,y2+bh/2)
            else: a=(x1,y1+bh/2); b=(x2+bw,y2+bh/2)
        else:
            a=(x1+bw/2,y1); b=(x2+bw/2,y2+bh)
        ax.add_patch(FancyArrowPatch(a,b,arrowstyle="-|>",mutation_scale=11,lw=1.3,color=GREY,shrinkA=1,shrinkB=1))
    fig.savefig(fname,bbox_inches="tight",pad_inches=0.05,facecolor="white"); plt.close(fig)

snake([("Literature study","gap analysis and objectives"),
       ("Data and features","cleaned dataset, feature dictionary"),
       ("Model development","LR, RF, XGBoost vs existing model"),
       ("Explainability","SHAP, templates, risk bands"),
       ("Integration","forwarding workflow, API, web UI"),
       ("Evaluation","metrics, error analysis, user study"),
       ("Documentation","report, demo, optional add-on")],4,"fig7_phases.png")

snake([("Feature vector","x built from the email"),
       ("Model output","phishing probability p(x)"),
       ("SHAP values","one contribution per feature"),
       ("Group scores","header, URL, text, action, attachment, behaviour"),
       ("Top-k selection","strongest risk-raising features"),
       ("Verification","each reason checked against extracted evidence"),
       ("Templates","filled with the actual detected values"),
       ("Risk card","score, band and ranked reasons")],4,"fig9_explain.png")

# Gantt
tasks=[("Literature survey and requirements",1,3),("Dataset collection and cleaning",2,5),("Feature engineering",4,7),
("Model training and comparison",6,9),("SHAP module and explanation templates",8,11),("Ingestion and backend API",7,11),
("Web interface",9,13),("Integration and testing",12,14),("User study and analysis",13,15),("Report and demonstration",14,16),
("Browser add-on (optional)",15,16)]
fig,ax=plt.subplots(figsize=(6.8,3.9),dpi=300)
for i,(t,s,e) in enumerate(tasks):
    opt = "optional" in t
    ax.barh(i,e-s+1,left=s-1,height=0.6,color="#FFFFFF" if opt else BLUE,edgecolor=BLUE,hatch="////" if opt else None,lw=1)
ax.set_yticks(range(len(tasks))); ax.set_yticklabels([t for t,_,_ in tasks],fontsize=8)
ax.invert_yaxis(); ax.set_xlim(0,16.3); ax.set_xticks([x+0.5 for x in range(16)]); ax.set_xticklabels([str(x+1) for x in range(16)],fontsize=8)
ax.set_xlabel("Project week (indicative plan)",fontsize=9); ax.grid(axis="x",color="#D9DEE7",lw=0.6); ax.set_axisbelow(True)
for s in ["top","right"]: ax.spines[s].set_visible(False)
fig.savefig("fig8_gantt.png",bbox_inches="tight",facecolor="white"); plt.close(fig)

# Risk card mock-up
fig,ax=plt.subplots(figsize=(6.4,3.6),dpi=300); ax.set_xlim(0,6.4); ax.set_ylim(0,3.6); ax.axis("off")
ax.add_patch(FancyBboxPatch((0.05,0.05),6.3,3.5,boxstyle="round,pad=0,rounding_size=0.12",fc="white",ec=BLUE,lw=1.4))
ax.text(0.3,3.25,"PhishLens analysis",fontsize=11,fontweight="bold",color=DARK,va="center")
ax.text(6.1,3.25,"Illustrative mock-up",fontsize=7.5,color=GREY,ha="right",va="center",style="italic")
ax.text(0.3,2.92,"From: security@paypa1-support.example     Subject: Your account will be suspended",fontsize=7.5,color=GREY,va="center")
ax.text(0.3,2.5,"Risk score: 91%",fontsize=14,fontweight="bold",color=DARK,va="center")
ax.text(3.05,2.5,"HIGH",fontsize=12,fontweight="bold",color="white",va="center",ha="center",bbox=dict(boxstyle="round,pad=0.3",fc="#C0392B",ec="#C0392B"))
x0,w=3.75,2.35
for i,(lab,col) in enumerate([("LOW","#2E8B57"),("MEDIUM","#E0A100"),("HIGH","#C0392B")]):
    ax.add_patch(Rectangle((x0+i*w/3,2.38),w/3,0.24,fc=col,ec="white",lw=1))
    ax.text(x0+i*w/3+w/6,2.5,lab,fontsize=6.5,color="white",ha="center",va="center",fontweight="bold")
mx=x0+0.91*w
ax.add_patch(FancyArrowPatch((mx,2.95-0.12),(mx,2.64),arrowstyle="-|>",mutation_scale=9,lw=1.2,color=DARK))
ax.plot([0.3,6.1],[2.2,2.2],color="#D9DEE7",lw=1)
ax.text(0.3,1.98,"Why this message looks suspicious",fontsize=9.5,fontweight="bold",color=DARK,va="center")
rs=["The visible link text does not match the website the link actually opens.",
    "The sender details do not match the server that delivered the message.",
    "The message pressures you to act immediately.",
    "This sender's domain was registered only a few days ago."]
for i,r in enumerate(rs):
    ax.text(0.35,1.62-i*0.33,"\u2022",fontsize=11,color=BLUE,va="center")
    ax.text(0.58,1.62-i*0.33,r,fontsize=8.5,color=DARK,va="center")
ax.text(0.3,0.2,"Model: xgboost-v3 (example). Reasons come from SHAP contributions.",fontsize=6.8,color=GREY,va="center")
fig.savefig("fig11_riskcard.png",bbox_inches="tight",facecolor="white"); plt.close(fig)
