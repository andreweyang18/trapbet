import re, csv, sys, unicodedata
sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # notes contain emoji; Windows console defaults to cp1252
# S3 star list lives in trapbet/engines/trap.py: STARS = {ohtani, judge} (v2, 2026-11-02);
# STARS_V1 = the nine-player v1 definition 2026-10-29; superseded 2026-11-02, see RESULTS.md.
from trapbet.engines.trap import STARS, STARS_V1, is_star  # noqa: F401  (run from the repo root)
PITCHERS={'yamamoto','peterson','eflin','wheeler','holmes','schwellenbach','olson','brown','steele','gilbert','wacha','williams','pivetta','nola','degrom','sanchez','lugo','gray','springs','senga','flaherty','alcantara','blanco','rodon','kikuchi','mahle','skubal','miller','bieber','peralta','woo','strider','bibee','cabrera','manaea','corbin','cantillo','patrick','warren','fried','gallen','meyer','may','burnes','ragans','roupp','ortiz','sale','ryan','quintana','misiorowski','keller','rodriguez','abbott','falter','canning','kirby','estes','gil','lodolo','parker','vasquez','ray','imanaga','glasnow','melton','rogers','littell','schmidt','castillo'}
# Matt Olson / Reese Olson, Hunter Brown / Ben Brown, Gavin Williams, Julio/Eduardo Rodriguez, Dustin May need first-name disambiguation
HITTER_OVERRIDES={'matt olson','julio rodriguez','ben brown'}  # ben brown IS a pitcher; handled below
def norm(s):
    s=unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower().replace("’","'").replace("'","")
    return re.sub(r'\s+',' ',s).strip()
def role(name):
    n=norm(name); last=n.split()[-1]
    if n in ('matt olson','julio rodriguez'): return 'hitter'
    if n=='hunter brown': return 'pitcher'
    if n=='ben brown': return 'pitcher'
    if last in PITCHERS: return 'pitcher'
    return 'hitter'
def star(name):
    return 1 if is_star(name, 'v2') else 0

# ---- screenshot rows: (date, player, side, line, platform, result, note) ----
# platform codes: prizepicks (Hitter/Pitcher Fantasy Score), underdog (Fantasy Points O/U Higher/Lower),
# app_A ("Fantasy Points — Full Game"), app_B ("Hitter/Pitcher Fantasy Points" shown with American odds)
S=[
# (date, player, side, line, platform, result, note, stake_usd, n_slips, stake_note)
('2025-03-28','Yoshinobu Yamamoto','over',31.5,'prizepicks',1,'3 slips (1 slip leg voided, prop still settled)',30,2,'$30 real + $20 free-bet slip'),
('2025-03-31','Jung Hoo Lee','under',8,'prizepicks',0,'3 slips',451.90,3,'150+150+151.90'),
('2025-03-31','David Peterson','over',25.5,'prizepicks',1,'',151.90,1,''),
('2025-04-01','Shohei Ohtani','under',8.5,'prizepicks',1,'2 slips',425,2,'250+175'),
('2025-04-02','Zach Eflin','over',27.5,'prizepicks',1,'LINE_MOVE_FLIP: also over 28.5 lost; counted win per rule',75,2,'25 (27.5 won) + 50 (28.5 lost)'),
('2025-04-02','Zack Wheeler','over',45.5,'prizepicks',1,'',25,1,''),
('2025-04-02','Clay Holmes','over',28.5,'prizepicks',1,'DATE_INFERRED from sibling leg (card cut off)',50,1,''),
('2025-04-04','Lawrence Butler','over',6.5,'prizepicks',1,'',50,1,''),
('2025-04-04','Spencer Schwellenbach','over',36.5,'prizepicks',1,'',50,1,''),
('2025-04-05','Kyle Tucker','under',9,'prizepicks',1,'6 slips; also app_A same line',325,6,'100+100+50+75+0(free)+boost slip amount cut off'),
('2025-04-05','Reese Olson','over',32.5,'prizepicks',1,'also app_A same line',175,4,'100+75+0(free)+boost slip amount cut off'),
('2025-04-05','Fernando Tatis Jr.','under',8,'prizepicks',1,'',50,1,''),
('2025-04-06','Ben Brown','under',27.5,'prizepicks',1,'2 slips',50,2,'25+25'),
('2025-04-07','Anthony Volpe','under',6.5,'underdog',1,'',30,2,'10+20'),
('2025-04-07','Justin Steele','over',34.5,'underdog',1,'',30,2,'10+20'),
('2025-04-07','Rafael Devers','under',7.5,'prizepicks',1,'2 slips',50,2,'25+25'),
('2025-04-07','Byron Buxton','under',6.5,'prizepicks',1,'',25,1,''),
('2025-04-07','Logan Gilbert','under',37.5,'prizepicks',1,'',50,1,''),
('2025-04-10','Michael Wacha','over',30.5,'prizepicks',0,'',50,1,''),
('2025-04-10','Gavin Williams','over',30.5,'prizepicks',1,'',50,1,''),
('2025-04-11','Nick Pivetta','over',39.5,'app_A',1,'also prizepicks same line; every slip lost on the paired leg',703,5,'150+50+150+153+200'),
('2025-04-11','Aaron Nola','over',33.5,'prizepicks',0,'',50,1,''),
('2025-04-11','Jacob deGrom','over',37.5,'prizepicks',0,'',153,1,''),
('2025-04-17','Cristopher Sanchez','over',34.5,'prizepicks',1,'',350,1,''),
('2025-04-21','Bryce Harper','under',7.5,'prizepicks',1,'',302,1,''),
('2025-04-23','Paul Goldschmidt','over',5.5,'app_A',1,'prizepicks leg same prop voided',100,1,''),
('2025-04-23','Steven Kwan','under',6,'app_A',1,'prizepicks leg same prop voided',100,1,''),
('2025-04-25','Seth Lugo','over',26.5,'app_B',1,'3 slips',100,3,'70+10+20'),
('2025-04-25','Logan Gilbert','over',41.5,'app_B',0,'',80,2,'70+10 (third slip cut off)'),
('2025-04-26','Sonny Gray','over',34.5,'app_B',0,'',20,1,''),
('2025-04-27','Oneil Cruz','under',7,'prizepicks',1,'also app_A same line',317,2,'100+217'),
('2025-04-28','Elly De La Cruz','under',9.5,'prizepicks',1,'also app_A same line',504,2,'304+200'),
('2025-05-01','Jeffrey Springs','under',24.5,'prizepicks',0,'',65,1,''),
('2025-05-04','Aaron Judge','under',9.5,'app_A',1,'',150,1,''),
('2025-05-04','Ian Happ','under',6,'app_A',1,'3 slips',500,3,'150+100+250'),
('2025-05-04','Kyle Stowers','under',6.5,'app_A',1,'3 slips',500,3,'150+100+250'),
('2025-05-05','Aaron Judge','under',9.5,'underdog',1,'also under 8.5 on app_A and prizepicks same day',125,4,'10+40+50+25'),
('2025-05-05','Manny Machado','under',6.5,'app_A',0,'also prizepicks same line',75,2,'50+25'),
('2025-05-07','Kodai Senga','under',26.5,'app_B',0,'3 slips',80,3,'10+10+60'),
('2025-05-07','Sonny Gray','over',31.5,'app_B',1,'3 slips',80,3,'10+10+60'),
('2025-05-07','Dansby Swanson','under',5.5,'prizepicks',1,'also app_A same line',82,2,'50+32'),
('2025-05-07','Manny Machado','under',6,'prizepicks',0,'second slip (2 losses) amount cut off',100,2,'100 + unknown'),
('2025-05-08','Byron Buxton','under',7.5,'app_B',0,'3 slips',132.50,3,'10+112.50+10'),
('2025-05-08','Spencer Schwellenbach','over',34.5,'app_B',1,'BOTH_SIDES: under 34.5 lost (3-pick), over 34.5 won (2 slips); notes say u34.5 won - CONFIRM',132.50,3,'10 (under) + 112.50 + 10 (over)'),
('2025-05-08','Zach Neto','under',5.5,'app_B',0,'',10,1,''),
('2025-05-10','Fernando Tatis Jr.','over',9.5,'prizepicks',1,'also app_A',501,5,'100+200+50+101+50'),
('2025-05-10','Byron Buxton','under',6.5,'prizepicks',1,'',150,3,'50+50+50'),
('2025-05-10','Jonathan India','under',5.5,'prizepicks',1,'also app_A',100,2,'50+50'),
('2025-05-10','Vinnie Pasquantino','under',4.5,'prizepicks',0,'also app_A',401,4,'200+50+101+50'),
('2025-05-10','Jack Flaherty','over',28.5,'prizepicks',0,'also app_A',100,2,'50+50'),
('2025-05-11','Sandy Alcantara','over',30.5,'underdog',0,'also app_B',470,7,'40+10+10+70+10+200+130'),
('2025-05-11','Ronel Blanco','over',31.5,'underdog',1,'also app_B',620,8,'40+10+10+70+10+200+130+150'),
('2025-05-11','Jose Ramirez','under',7.5,'underdog',1,'also app_B; also under 5.5 app_A won',428,5,'40+10+70+150+158'),
('2025-05-11','Alec Bohm','under',5,'app_A',0,'',158,1,''),
('2025-05-12','Jackson Merrill','under',5.5,'app_A',0,'',250,1,'amount partly obscured, read as 250 - verify'),
('2025-05-16','Carlos Rodon','under',35.5,'app_A',1,'',60,2,'10 (boosted 3-pick, stake inferred) + 50'),
('2025-05-16','Anthony Volpe','under',5.5,'app_A',1,'4 slips',100,4,'10+40+0(free)+50'),
('2025-05-18','Yainer Diaz','over',5,'prizepicks',1,'also app_A; one slip refunded (partner leg void)',80,3,'30+25+25 + refunded slip unknown'),
('2025-05-19','Will Benson','under',4.5,'prizepicks',0,'2 slips',250,2,'150+100'),
('2025-05-19','Chase Meidroth','under',4.5,'prizepicks',0,'',100,1,''),
('2025-05-20','Geraldo Perdomo','under',6.5,'app_B',0,'4 slips',210,3,'150+50+10 + one slip amount cut off'),
('2025-05-20','Daulton Varsho','under',5,'prizepicks',1,'',100,2,'50+50'),
('2025-05-20','Maikel Garcia','under',6.5,'prizepicks',1,'',50,1,''),
('2025-05-23','Matt Olson','under',7,'app_A',1,'also under 6.5 won',250,4,'20+50+150+30'),
('2025-05-23','Trent Grisham','over',9,'app_A',0,'',50,2,'20+30'),
('2025-05-23','Adolis Garcia','over',5,'app_A',0,'BOTH_SIDES: over 5 lost (3-pick), under 5 won (2-pick); notes record the over as a loss, so loss kept - CONFIRM',100,2,'50 (over) + 50 (under)'),
('2025-05-23','James Wood','under',7,'app_A',1,'',200,2,'50+150'),
('2025-05-24','Isaac Paredes','under',5.5,'app_A',1,'3 slips',135,3,'35+50+50'),
('2025-05-25','Pete Alonso','over',7,'app_A',1,'',200,2,'150+50'),
('2025-05-25','Lawrence Butler','under',6.5,'app_A',0,'',200,1,''),
('2025-05-27','Trea Turner','under',7,'app_A',1,'4 slips',195,4,'100+50+25+20'),
('2025-05-27','Brandon Lowe','under',7,'app_A',1,'LINE_MOVE_FLIP: under 6 lost on 4 slips (screenshot); notes record under 7 won; counted win per LINE_MOVE_FLIP rule (confirmed)',195,4,'100+25+20+50 (all on the under-6 slips)'),
('2025-05-27','Lawrence Butler','under',5,'app_A',0,'3 slips',100,3,'25+50+25'),
('2025-05-28','Jose Altuve','under',7.5,'app_A',1,'',250,1,''),
('2025-05-28','Lawrence Butler','under',6.5,'app_A',1,'',250,1,''),
('2025-05-28','Brandon Lowe','under',5,'app_A',0,'',203,1,''),
('2025-05-28','TJ Friedl','under',7,'app_A',1,'',543,2,'250+293'),
('2025-05-28','Yusei Kikuchi','under',28.5,'app_A',1,'',250,1,''),
('2025-05-28','Tyler Mahle','under',30,'app_A',0,'',293,1,''),
]
EXCLUDED_VOIDS=['2025-05-18 Chase Meidroth under 5 (void both platforms)','2025-05-27 Cade Horton over 34 (void)']

# ---- notes ----
lines=open('data/mlbbets.txt',encoding='utf-8').read().splitlines()
pat=re.compile(r'^(.*?)\s+(under|over|u|o|iver)\s*([0-9]+(?:\.[0-9])?)\s+(.*?)(fantasy|facts).*?(✅|❌)',re.I)
EXCLUDED_NOTE_LINES={199,200,201}  # excluded: not fantasy-score props
notes=[]
for i,l in enumerate(lines,1):
    if i in EXCLUDED_NOTE_LINES: continue
    if '✅' not in l and '❌' not in l: continue
    m=pat.search(l)
    if not m: continue
    name=norm(m.group(1)); side=m.group(2).lower(); side='under' if side=='u' else 'over' if side in('o','iver') else side
    line=float(m.group(3)); mid=m.group(4).strip(); res=1 if m.group(6)=='✅' else 0
    if 'inning' in mid.lower(): continue  # partial-game (1-3 inning) fantasy excluded by data rule
    market='fantasy_score'
    notes.append(dict(idx=i,name=name,side=side,line=line,res=res,market=market,raw=l.strip()))

def last(n):
    t=[x.replace('.','') for x in norm(n).split()]
    if t[-1]=='jr' and len(t)>1: t=t[:-1]
    return t[-1]
matched=set(); rows=[]
# pre-assign each note to the best screenshot row (exact name/side/line, prefer same result)
assign={}
for n in notes:
    c=[i for i,(d,pl,side,line,plat,res,note,*_) in enumerate(S) if last(n['name'])==last(pl) and n['side']==side and abs(n['line']-line)<0.01]
    if not c and n['side']=='under' and n['line']==8.5 and last(n['name'])=='judge':
        c=[i for i,(d,pl,*_) in enumerate(S) if d=='2025-05-05' and 'Judge' in pl]
    c=[i for i in c if i not in assign.values()]
    if c:
        c.sort(key=lambda i: S[i][5]!=n['res']); assign[n['idx']]=c[0]
for i,(d,pl,side,line,plat,res,note,stake,nsl,snote) in enumerate(S):
    hit=[k for k,v in assign.items() if v==i]
    if hit:
        n=next(x for x in notes if x['idx']==hit[0]); src=f'notes_match:line{n["idx"]}'
        if n['res']!=res: note+=f' RESULT_CONFLICT notes={n["res"]}'
    else: src='screenshot_only'
    rows.append(dict(date=d,sport='mlb',platform=plat,player=pl,market='fantasy_score',line=line,side=side,
        odds_or_payout=2.0,result=res,S1_streak='',S2_popular='',S3_star=star(pl),S4_xplatform='',S5_fairgap='',S6_matchup='',S7_revmove='',
        model_p='',closing_line='',stake_usd=stake,n_slips=nsl,high_conf=1 if stake>=100 else 0,notes='; '.join(x for x in [f'role={role(pl)}',src,note,('stake: '+snote) if snote else ''] if x)))
matched=set(assign.keys())
# ---- manual date/stake fills for notes-only rows (keyed by notes line number) ----
fills={}
try:
    for f in csv.DictReader(open('data/undated_fills.csv',encoding='utf-8')): fills[int(f['notes_line'])]=f
except FileNotFoundError: pass
merged_into_dated=[]
for n in notes:
    if n['idx'] in matched: continue
    f=fills.get(n['idx'])
    if f:
        # same player already dated from a screenshot on the same day -> merge, don't double count
        def same_person(a,b):
            a=norm(a).replace('.','').replace(' jr','').split(); b=norm(b).replace('.','').replace(' jr','').split()
            if a[-1]!=b[-1]: return False
            return len(a)==1 or len(b)==1 or a[0]==b[0]
        dup=[r for r in rows if r['date']==f['date'] and same_person(r['player'],n['name']) and 'screenshot' in r['notes'] or ('notes_match' in r['notes'] and r['date']==f['date'] and same_person(r['player'],n['name']))]
        dup=[r for r in dup if r['side']==n['side'] or n['idx'] in {134}]  # screenshot-dated rows are reliable; same player/day/side = same bet even if line moved (134 = Schwellenbach 5/8 'u34.5' typo, corrected to o34.5; same bet as screenshot row)
        if dup:
            r=dup[0]; r['notes']+=f"; MERGED notes line{n['idx']} ({n['raw']}) same player/day, stake_band={f['stake_band']}"
            if n['line']!=float(r['line']):
                r['notes']+=f" LINE_MOVE_FLIP (notes line {n['line']} result {n['res']})" if n['res']!=int(r['result']) else f" LINE_MOVE (notes line {n['line']}, same result)"
                if n['res']==1 and int(r['result'])==0: r['result']=1
            merged_into_dated.append((n['raw'],f['date'],r['player'])); continue
        rows.append(dict(date=f['date'],sport='mlb',platform='',player=n['name'].title(),market=n['market'],line=n['line'],side=n['side'],
            odds_or_payout=2.0,result=n['res'],S1_streak='',S2_popular='',S3_star=star(n['name']),S4_xplatform='',S5_fairgap='',S6_matchup='',S7_revmove='',
            model_p='',closing_line='',stake_usd='',n_slips='',high_conf=f['high_conf'],
            notes='; '.join(x for x in [f'role={role(n["name"])}',f'notes_only:line{n["idx"]}',f'date+stake_band from Pikkit lookup (stake_band={f["stake_band"]})',f['flag']] if x)))
        continue
    rows.append(dict(date='',sport='mlb',platform='',player=n['name'].title(),market=n['market'],line=n['line'],side=n['side'],
        odds_or_payout=2.0,result=n['res'],S1_streak='',S2_popular='',S3_star=star(n['name']),S4_xplatform='',S5_fairgap='',S6_matchup='',S7_revmove='',
        model_p='',closing_line='',stake_usd='',n_slips='',high_conf='',notes=f'role={role(n["name"])}; notes_only:line{n["idx"]}; UNDATED'))
hdr=['date','sport','platform','player','market','line','side','odds_or_payout','result','S1_streak','S2_popular','S3_star','S4_xplatform','S5_fairgap','S6_matchup','S7_revmove','model_p','closing_line','stake_usd','n_slips','high_conf','notes']
with open('data/bet_log.csv','w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=hdr); w.writeheader(); w.writerows(rows)
ss=[r for r in rows if r['date']]; no=[r for r in rows if not r['date']]
print('screenshot rows',len(ss),'matched to notes',sum('notes_match' in r['notes'] for r in ss),'screenshot_only',sum('screenshot_only' in r['notes'] for r in ss))
print('notes-only rows',len(no),'| total',len(rows))
print('screenshot hit rate',sum(r['result'] for r in ss),'/',len(ss))
print('all rows hit rate',sum(r['result'] for r in rows),'/',len(rows))
for r in ss:
    if 'screenshot_only' in r['notes'] or 'CONFLICT' in r['notes']: print('  ',r['date'],r['player'],r['side'],r['line'],r['result'],'|',r['notes'])
print('excluded voids:',EXCLUDED_VOIDS)
print('merged notes rows into dated rows:',merged_into_dated)
