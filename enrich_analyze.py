"""
German airports, one day of air traffic — enrichment + analysis (Stage 2, v2).
Now includes Leipzig/Halle (EDDP), the 24/7 DHL cargo hub, as the foil to the
night-banned passenger hubs.
Input : flights_raw.csv, airports.csv, airlines.dat
Output: flights_enriched.csv, routes_for_kepler.csv, 3 PNG charts.
"""
import pandas as pd, numpy as np, re
from datetime import datetime
from zoneinfo import ZoneInfo
import matplotlib.pyplot as plt

TZ = ZoneInfo("Europe/Berlin")
NAMES = {"EDDF":"Frankfurt","EDDM":"Munich","EDDB":"Berlin","EDDP":"Leipzig"}
ORDER_ALL = ["EDDF","EDDM","EDDB","EDDP"]

ap = pd.read_csv("airports.csv", low_memory=False).set_index("ident")
al = pd.read_csv("airlines.dat", header=None,
                 names=["id","name","alias","iata","icao","callsign","country","active"],
                 na_values=["\\N",""]).dropna(subset=["icao"])
al = al[al["icao"].str.len()==3]
name_map = dict(zip(al["icao"], al["name"]))
OVERRIDE = {"OCN":"Discover Airlines","EJU":"easyJet","EZY":"easyJet","EZS":"easyJet Switzerland",
            "BEL":"Brussels Airlines","NJE":"NetJets","ITY":"ITA Airways","EWG":"Eurowings",
            "CLH":"Lufthansa CityLine","GEC":"Lufthansa Cargo","DLA":"Air Dolomiti",
            "SWR":"Swiss","AUA":"Austrian",
            "BCS":"DHL (EAT Leipzig)","BOX":"AeroLogic","DHK":"DHL Air UK","ABR":"ASL Airlines"}
name_map.update(OVERRIDE)
LH_GROUP = {"DLH","CLH","EWG","GEC","DLA","OCN","BEL","SWR","AUA"}
CARGO_OPS = {"GEC","BCS","BOX","DHK","ABR"}  # dedicated freight operators, for a cargo-vs-cargo night comparison

def coords(icao):
    if icao in ap.index:
        r = ap.loc[icao]
        return float(r["latitude_deg"]), float(r["longitude_deg"])
    return (np.nan, np.nan)

def haversine(a, b, c, d):
    if any(pd.isna(x) for x in (a,b,c,d)): return np.nan
    R=6371.0; p1,p2=np.radians(a),np.radians(c); dp=np.radians(c-a); dl=np.radians(d-b)
    x=np.sin(dp/2)**2+np.cos(p1)*np.cos(p2)*np.sin(dl/2)**2
    return 2*R*np.arcsin(np.sqrt(x))

df = pd.read_csv("flights_raw.csv").dropna(subset=["firstSeen"])
df["home"]  = df["queried_airport"]
ORDER = [a for a in ORDER_ALL if (df["home"]==a).any()]   # only airports present in the data
df["other"] = np.where(df["direction"]=="departure", df["arr_airport"], df["dep_airport"])
df["ts"]    = np.where(df["direction"]=="departure", df["firstSeen"], df["lastSeen"])
df["hour"]  = df["ts"].apply(lambda t: datetime.fromtimestamp(t, TZ).hour)

df["al_icao"] = df["callsign"].apply(lambda c: (re.match(r"^[A-Z]{3}", str(c)) or [None])[0]
                                     if re.match(r"^[A-Z]{3}", str(c)) else None)
df["airline"] = df["al_icao"].map(name_map).fillna("Other / unmatched")
df["lh_group"] = df["al_icao"].isin(LH_GROUP)

df["o_country"]   = df["other"].map(ap["iso_country"])
df["o_continent"] = df["other"].map(ap["continent"])
def reach(r):
    if pd.isna(r["o_country"]): return "unknown"
    if r["o_country"]=="DE": return "Domestic"
    if r["o_continent"]=="EU": return "Europe"
    return "Intercontinental"
df["reach"] = df.apply(reach, axis=1)

hc = {a: coords(a) for a in ORDER}
oc = df["other"].map(lambda x: coords(x) if isinstance(x,str) else (np.nan,np.nan))
df["o_lat"] = [c[0] for c in oc]; df["o_lon"] = [c[1] for c in oc]
df["home_lat"] = df["home"].map(lambda a: hc.get(a,(np.nan,np.nan))[0])
df["home_lon"] = df["home"].map(lambda a: hc.get(a,(np.nan,np.nan))[1])
df["dist_km"] = [haversine(*row) for row in zip(df["home_lat"],df["home_lon"],df["o_lat"],df["o_lon"])]

df.to_csv("flights_enriched.csv", index=False)

arc = (df.dropna(subset=["o_lat","o_lon"])
         .groupby(["home","home_lat","home_lon","other","o_lat","o_lon","reach"])
         .size().reset_index(name="flights"))
arc.to_csv("routes_for_kepler.csv", index=False)

plt.rcParams.update({"font.size":13,"axes.titlesize":15,"axes.titleweight":"bold",
                     "figure.dpi":130,"axes.spines.top":False,"axes.spines.right":False})
COL = {"EDDF":"#1f4e79","EDDM":"#2e8b57","EDDB":"#c0504d","EDDP":"#e69f00"}

# 1) hourly rhythm with night ban shaded — now the centerpiece
fig,ax=plt.subplots(figsize=(10,5.2))
for a in ORDER:
    s=df[df.home==a].groupby("hour").size().reindex(range(24),fill_value=0)
    lw = 3 if a=="EDDP" else 2
    ax.plot(s.index,s.values,marker="o",ms=4,lw=lw,color=COL[a],label=NAMES[a])
ax.axvspan(23,24,color="grey",alpha=.15); ax.axvspan(0,5,color="grey",alpha=.15)
ax.text(2.5,ax.get_ylim()[1]*.9,"night flight ban\n23:00-05:00\n(passenger hubs)",ha="center",fontsize=10,color="#444")
ax.set_xlabel("hour of day (local)"); ax.set_ylabel("aircraft movements")
ax.set_title("The night ban doesn't stop flying, it moves it to Leipzig")
ax.set_xticks(range(0,24,2)); ax.legend()
fig.tight_layout(); fig.savefig("chart1_rhythm.png")

# 2) reach split
fig,ax=plt.subplots(figsize=(9,4.8))
cats=["Domestic","Europe","Intercontinental"]; ccol=["#8fbcd4","#f0ad4e","#c0504d"]
left=np.zeros(len(ORDER))
for c,col in zip(cats,ccol):
    vals=np.array([ (df[(df.home==a)&(df.reach!="unknown")].reach==c).mean()*100 for a in ORDER ])
    ax.barh([NAMES[a] for a in ORDER],vals,left=left,color=col,label=c)
    left+=vals
ax.set_xlabel("% of geolocatable movements"); ax.set_xlim(0,100)
ax.set_title("Where the flights go")
ax.invert_yaxis(); ax.legend(ncol=3,loc="lower center",bbox_to_anchor=(.5,-.35))
fig.tight_layout(); fig.savefig("chart2_reach.png")

# 3) airline concentration — small multiples
fig,axes=plt.subplots(1,len(ORDER),figsize=(4.3*len(ORDER),4.6),sharex=False)
if len(ORDER)==1: axes=[axes]
for ax,a in zip(axes,ORDER):
    sub=df[df.home==a]; tot=len(sub)
    top=sub.airline.value_counts().head(6)[::-1]
    cols=["#1f4e79" if (sub[sub.airline==n]["lh_group"].any()) else "#b0b0b0" for n in top.index]
    ax.barh(range(len(top)),top.values/tot*100,color=cols)
    ax.set_yticks(range(len(top))); ax.set_yticklabels(top.index,fontsize=10)
    ax.set_title(f"{NAMES[a]}  (n={tot})"); ax.set_xlabel("% of movements"); ax.set_xlim(0,60)
    grp=sub['lh_group'].mean()*100
    ax.text(.97,.05,f"LH Group {grp:.0f}%",transform=ax.transAxes,ha="right",
            fontsize=10,color="#1f4e79",weight="bold")
fig.suptitle("Whose airport is it? Lufthansa (blue) owns its hubs; Berlin is low-cost; Leipzig is DHL",
             fontsize=15,fontweight="bold")
fig.tight_layout(rect=[0,0,1,.95]); fig.savefig("chart3_airlines.png")

# ---------- printed summary ----------
print("NIGHT SHARE (movements 23:00-04:59, the banned window at passenger hubs):")
for a in ORDER:
    sub=df[df.home==a]
    night=sub[(sub.hour>=23)|(sub.hour<5)]
    print(f"  {NAMES[a]:10s}: {len(night):4d}/{len(sub):4d} = {100*len(night)/len(sub):5.1f}%")

# Leipzig's overall night share is confounded by its cargo-heavy traffic mix, so
# isolate cargo carriers specifically and compare their night share head-to-head
# across airports (does the ban suppress cargo too, or only passenger flights?).
print("\nCARGO-ONLY night share (fair comparison, isolates traffic-mix confound):")
df["is_cargo"] = df["al_icao"].isin(CARGO_OPS)
df["is_night"] = (df.hour>=23)|(df.hour<5)
for a in ORDER:
    sub=df[df.home==a]
    cargo, noncargo = sub[sub.is_cargo], sub[~sub.is_cargo]
    cargo_share = f"{100*cargo.is_night.mean():5.1f}%" if len(cargo) else "  n/a"
    print(f"  {NAMES[a]:10s}: cargo n={len(cargo):3d}  cargo_night={cargo_share}  "
          f"non-cargo_night={100*noncargo.is_night.mean():5.1f}%")

print("\ntrue long-haul (>4000 km) share of movements:")
for a in ORDER:
    s=df[df.home==a]; lh=(s["dist_km"]>4000).sum()
    print(f"  {NAMES[a]:10s}: {100*lh/len(s):.1f}%   median dist {s['dist_km'].median():.0f} km")
print("\nfiles written: flights_enriched.csv, routes_for_kepler.csv, chart1_rhythm.png, chart2_reach.png, chart3_airlines.png")