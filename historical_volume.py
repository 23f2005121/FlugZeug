"""
Extension: does the night-ban introduction show up as a volume shock at all?

This is a SEPARATE data source from the rest of the project (annual official
airport statistics, not OpenSky ADS-B) because ADS-B coverage doesn't reach
back to FRA's 2011 ban or MUC's 2001 ban -- OpenSky's usable historical
coverage only starts around 2016-2017. So this can only test total ANNUAL
movement volume, not hourly/night-share, around each ban's introduction.

Sources (official, hand-transcribed, checked 2026-08-25):
- FRA 1999-2023: Fraport AG, "Frankfurt Airport Luftverkehrsstatistik 2023"
  (Statistischer Jahresbericht), p.6 "Entwicklung des Verkehrs seit 1999".
  https://www.fraport.com/.../23219_D_Statistischer_Jahresbericht_2023_Final.pdf
- MUC 1992-2025: Flughafen München GmbH annual statistical reports, as
  compiled in German Wikipedia "Verkehrszahlen des Flughafens München"
  (itself sourced from FMG's own Jahresberichte).
  https://de.wikipedia.org/wiki/Verkehrszahlen_des_Flughafens_München

Output: chart4_historical_volume.png
"""
import matplotlib.pyplot as plt

# annual aircraft movements (Flugbewegungen / Starts+Landungen)
FRA = {
    1999:439093,2000:458731,2001:456452,2002:458359,2003:458865,2004:477475,
    2005:490147,2006:489406,2007:492569,2008:485783,2009:463111,2010:464432,
    2011:487162,2012:482242,2013:472692,2014:469026,2015:468153,2016:462885,
    2017:475537,2018:512115,2019:513912,2020:212235,2021:261927,2022:382211,
    2023:430436,
}
MUC = {
    1992:192157,1993:192185,1994:199859,1995:213965,1996:233256,1997:267814,
    1998:278392,1999:299071,2000:319009,2001:337653,2002:344405,2003:355602,
    2004:383110,2005:398838,2006:411335,2007:431815,2008:432296,2009:396805,
    2010:389939,2011:409956,2012:398039,2013:381951,2014:376678,2015:379911,
    2016:394430,2017:404505,2018:413469,2019:417138,2020:146833,2021:153097,
    2022:285028,2023:302150,
}

fig, ax = plt.subplots(figsize=(11, 5.5))
ax.plot(*zip(*sorted(FRA.items())), marker="o", ms=3, lw=2, color="#1f4e79", label="Frankfurt")
ax.plot(*zip(*sorted(MUC.items())), marker="o", ms=3, lw=2, color="#2e8b57", label="Munich")

ax.axvline(2011, color="#c0504d", ls="--", lw=1.3)
ax.text(2011.15, ax.get_ylim()[1]*0.06, "FRA night ban\n(Oct 2011, permanent Apr 2012)\n+ new runway opened same year",
        fontsize=8.5, color="#c0504d")
ax.axvline(2001, color="#e69f00", ls="--", lw=1.3)
ax.text(2001.15, ax.get_ylim()[1]*0.30, "MUC core restriction\nformalised 2001", fontsize=8.5, color="#b3800a")

for yr, lbl in [(2001,"9/11"), (2009,"financial crisis"), (2020,"COVID-19")]:
    ax.axvspan(yr-0.15, yr+0.15, color="grey", alpha=0.12)

ax.set_xlabel("year"); ax.set_ylabel("annual aircraft movements")
ax.set_title("Total yearly volume shows no clean step-change at either ban date")
ax.legend(loc="lower right")
fig.tight_layout()
fig.savefig("chart4_historical_volume.png")
print("Saved chart4_historical_volume.png")

print("\nYear-over-year change around each ban:")
for name, data, yr in [("FRA", FRA, 2011), ("MUC", MUC, 2001)]:
    for y in range(yr-1, yr+3):
        if y in data and y-1 in data:
            pct = 100*(data[y]-data[y-1])/data[y-1]
            print(f"  {name} {y}: {data[y]:,} ({pct:+.1f}% vs {y-1})")
