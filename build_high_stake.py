import csv
# (date, stake, slip_type, payout, [ (fantasy leg, hit) ... ], non_fantasy_legs_desc, slip_result)
# Only slips with a VISIBLE stake >= $100. Boosted slips excluded. Tennis/other-sport fantasy legs excluded from counts.
SL=[
('2025-03-31',150,'2-pick','+200',[('Jung Hoo Lee under 8',0)],'C.Sanchez ER (W)','L'),
('2025-03-31',150,'2-pick','+200',[('Jung Hoo Lee under 8',0)],'T.Anderson 1st-inn Ks (L)','L'),
('2025-03-31',151.90,'2-pick','+200',[('Jung Hoo Lee under 8',0),('David Peterson over 25.5',1)],'','L'),
('2025-04-01',250,'2-pick','+200',[('Shohei Ohtani under 8.5',1)],'C.Mize Ks (W)','W'),
('2025-04-01',175,'2-pick','+200',[('Shohei Ohtani under 8.5',1)],'C.Mize Ks (W)','W'),
('2025-04-05',100,'2-pick','+200',[('Kyle Tucker under 9',1),('Reese Olson over 32.5',1)],'','W'),
('2025-04-05',100,'2-pick','+200',[('Kyle Tucker under 9',1)],'A.Nola Ks (W)','W'),
('2025-04-11',150,'2-pick','+217',[('Nick Pivetta over 39.5',1)],'J.deGrom outs (L)','L'),
('2025-04-11',150,'2-pick','+197',[('Nick Pivetta over 39.5',1)],'T.Bibee outs (L)','L'),
('2025-04-11',153,'2-pick','+200',[('Jacob deGrom over 37.5',0),('Nick Pivetta over 39.5',1)],'','L'),
('2025-04-11',200,'2-pick','+200',[('Nick Pivetta over 39.5',1)],'J.deGrom outs (L)','L'),
('2025-04-17',350,'2-pick','+200',[('Cristopher Sanchez over 34.5',1)],'A.Romagnoli passes (L)','L'),
('2025-04-21',302,'2-pick','+200',[('Bryce Harper under 7.5',1)],'E.Anderson passes (W)','W'),
('2025-04-23',100,'2-pick','+217',[('Paul Goldschmidt over 5.5',1),('Steven Kwan under 6',1)],'','W'),
('2025-04-27',100,'2-pick','+200',[('Oneil Cruz under 7',1)],'O.Bido outs (L)','L'),
('2025-04-27',217,'2-pick','+215',[('Oneil Cruz under 7',1)],'L.Doncic PRA (L)','L'),
('2025-04-28',304,'2-pick','+215',[('Elly De La Cruz under 9.5',1)],'R.Blanco 1st-inn runs (W)','W'),
('2025-04-28',200,'2-pick','+200',[('Elly De La Cruz under 9.5',1)],'R.Dickie passes (W)','W'),
('2025-05-04',150,'3-pick','+492',[('Aaron Judge under 9.5',1),('Ian Happ under 6',1),('Kyle Stowers under 6.5',1)],'','W'),
('2025-05-04',100,'3-pick','+492',[('Ian Happ under 6',1),('Kyle Stowers under 6.5',1)],'R.Suarez walks (L)','L'),
('2025-05-04',250,'2-pick','+217',[('Ian Happ under 6',1),('Kyle Stowers under 6.5',1)],'','W'),
('2025-05-07',100,'2-pick','+200',[('Manny Machado under 6',0)],'J.Cannon Ks (W)','L'),
('2025-05-08',112.50,'2-pick','+216',[('Spencer Schwellenbach over 34.5',1),('Byron Buxton under 7.5',0)],'','L'),
('2025-05-10',100,'2-pick','+200',[('Fernando Tatis Jr. over 9.5',1)],'J.Sinner tennis FS (W, excluded)','W'),
('2025-05-10',200,'2-pick','+217',[('Fernando Tatis Jr. over 9.5',1),('Vinnie Pasquantino under 4.5',0)],'','L'),
('2025-05-10',101,'2-pick','+217',[('Fernando Tatis Jr. over 9.5',1),('Vinnie Pasquantino under 4.5',0)],'','L'),
('2025-05-11',200,'2-pick','+224',[('Ronel Blanco over 31.5',1),('Sandy Alcantara over 30.5',0)],'','L'),
('2025-05-11',130,'2-pick','+224',[('Sandy Alcantara over 30.5',0),('Ronel Blanco over 31.5',1)],'','L'),
('2025-05-11',150,'2-pick','+216',[('Ronel Blanco over 31.5',1),('Jose Ramirez under 7.5',1)],'','W'),
('2025-05-11',158,'2-pick','+217',[('Jose Ramirez under 5.5',1),('Alec Bohm under 5',0)],'','L'),
('2025-05-19',150,'2-pick','+200',[('Will Benson under 4.5',0)],'E.Quinn tennis FS (W, excluded)','L'),
('2025-05-19',100,'2-pick','+200',[('Will Benson under 4.5',0)],'E.Quinn tennis FS (W, excluded)','L'),
('2025-05-19',100,'2-pick','+200',[('Chase Meidroth under 4.5',0)],'E.Quinn tennis FS (W, excluded)','L'),
('2025-05-20',150,'2-pick','+200',[('Geraldo Perdomo under 6.5',0)],'J.Polanco HRR (L)','L'),
('2025-05-23',150,'2-pick','+217',[('Matt Olson under 6.5',1),('James Wood under 7',1)],'','W'),
('2025-05-25',150,'2-pick','+206',[('Pete Alonso over 7',1)],'T.Skubal Ks (L)','L'),
('2025-05-25',200,'2-pick','+206',[('Lawrence Butler under 6.5',0)],'T.Skubal Ks (L)','L'),
('2025-05-27',100,'2-pick','+217',[('Trea Turner under 7',1),('Brandon Lowe under 6',0)],'','L'),
('2025-05-28',250,'2-pick','+217',[('Jose Altuve under 7.5',1),('Lawrence Butler under 6.5',1)],'','W'),
('2025-05-28',203,'2-pick','+192',[('Brandon Lowe under 5',0)],'M.Betts HRR (L)','L'),
('2025-05-28',250,'2-pick','+217',[('TJ Friedl under 7',1),('Yusei Kikuchi under 28.5',1)],'','W'),
('2025-05-28',293,'2-pick','+217',[('Tyler Mahle under 30',0),('TJ Friedl under 7',1)],'','L'),
]
EXCLUDED='5/12 Merrill slip (amount obscured); 5/7 Machado 2nd slip (amount cut off); 5/20 Perdomo 4th slip (amount cut off); 4/5 Tucker/Olson boosted slip (amount cut off, boosted)'
rows=[]
for d,st,typ,pay,legs,other,res in SL:
    n=len(legs); h=sum(x[1] for x in legs)
    rows.append(dict(date=d,stake_usd=st,slip_type=typ,payout=pay,fantasy_legs=' | '.join(l for l,_ in legs),
        fantasy_legs_n=n,fantasy_hits=h,fantasy_frac=round(h/n,2),other_legs=other,slip_result=res))
with open('data/high_stake_slips.csv','w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
N=sum(r['fantasy_legs_n'] for r in rows); H=sum(r['fantasy_hits'] for r in rows)
print(f'slips >=100 with visible stake: {len(rows)}  | slips won: {sum(r["slip_result"]=="W" for r in rows)}')
print(f'fantasy legs: {H}/{N} = {H/N:.1%}   (slip-level avg of fractions: {sum(r["fantasy_frac"] for r in rows)/len(rows):.1%})')
pure=[r for r in rows if not r['other_legs'] or 'excluded' in r['other_legs']]
mixed=[r for r in rows if r['other_legs'] and 'excluded' not in r['other_legs']]
print('all-fantasy slips:',len(pure),'won',sum(r['slip_result']=='W' for r in pure),'| mixed slips:',len(mixed),'won',sum(r['slip_result']=='W' for r in mixed),
      '| mixed slips where fantasy leg(s) all hit but slip lost:',sum(r['fantasy_hits']==r['fantasy_legs_n'] and r['slip_result']=='L' for r in mixed))
print('$ in mixed slips lost despite fantasy legs hitting:',sum(r['stake_usd'] for r in mixed if r['fantasy_hits']==r['fantasy_legs_n'] and r['slip_result']=='L'))
print('strictly >100:',sum(1 for r in rows if r['stake_usd']>100),'slips; legs',sum(r['fantasy_hits'] for r in rows if r['stake_usd']>100),'/',sum(r['fantasy_legs_n'] for r in rows if r['stake_usd']>100))
print('excluded:',EXCLUDED)
