/* tlb-prompts.js — the prediction prompt pool and rotation shared by think-like-boyd.html,
   the morning brief (via forge_actions.py) and forge-evening-debrief.html.
   One source of truth so the pages cannot drift. No dependencies. */
(function(){
  var TYPES = { say:'What they’ll say', happen:'What will happen', howlong:'How long', who:'Who or which' };
  var GROUPS = ['family','traffic','strangers','self','work','students'];
  var GLABEL = { family:'Family and home', traffic:'Traffic and the drive', strangers:'Strangers and the public', self:'Yourself', work:'Work', students:'Students' };
  var DOMAIN = { family:'Family', students:'Work', work:'Work' };   // only where unambiguous
  var POOL = [
    // family and home
    {g:'family', t:'say',     q:'The first thing said to you when you walk in the door tonight — who says it, and is it a question, a request, or a report?'},
    {g:'family', t:'happen',  q:'At eight tonight, how many of you are in the same room?'},
    {g:'family', t:'who',     q:'Which of the three asks you for something tonight, and what?'},
    {g:'family', t:'howlong', q:'The first “time to go” tomorrow morning — how many minutes until the door actually closes?'},
    {g:'family', t:'who',     q:'Who’s in the best mood at dinner, and who’s in the worst?'},
    {g:'family', t:'say',     q:'The next disagreement in the house — what’s it about, and who backs down?'},
    {g:'family', t:'happen',  q:'At ringette this week: does the team win, by how much, and who on the bench is the loudest parent?'},
    {g:'family', t:'say',     q:'What does your partner mention first when you ask about their day?'},
    {g:'family', t:'who',     q:'Which chore gets done without being asked this week, and by whom?'},
    // traffic and the drive
    {g:'traffic', t:'howlong', q:'Minutes door to door this morning — write it before you leave.'},
    {g:'traffic', t:'who',     q:'Where’s the slowest point on the drive today, and is it the usual one?'},
    {g:'traffic', t:'happen',  q:'Someone cuts you off or runs the light today — where, and what kind of vehicle?'},
    {g:'traffic', t:'howlong', q:'The drive to the night class — faster or slower than last week, and by how much?'},
    {g:'traffic', t:'happen',  q:'First open spot in the lot when you arrive — same row as yesterday?'},
    // strangers and the public
    {g:'strangers', t:'howlong', q:'Next time you’re in a queue: how long, and does the person ahead of you have a problem at the counter?'},
    {g:'strangers', t:'say',     q:'The cashier or barista says one thing beyond the transaction — what is it?'},
    {g:'strangers', t:'happen',  q:'Someone asks you for directions, help, or money this week — where, and which?'},
    {g:'strangers', t:'who',     q:'In the next shop you walk into, who speaks first — you or them?'},
    {g:'strangers', t:'say',     q:'The next phone call from an unknown number — what is it actually about?'},
    {g:'strangers', t:'who',     q:'Who holds the door, and who doesn’t, at the next building you enter?'},
    // yourself
    {g:'self', t:'howlong', q:'What time do you actually fall asleep tonight?'},
    {g:'self', t:'who',     q:'Which category on Count the Week has the biggest gap when you close Sunday?'},
    {g:'self', t:'howlong', q:'Tonight’s marking — minutes, written now?'},
    {g:'self', t:'happen',  q:'Will the two hours happen this week, and which day?'},
    {g:'self', t:'happen',  q:'The thing you’ll be tempted to do instead of the primary today — what is it, and do you do it?'},
    // work, kept small
    {g:'work', t:'happen', q:'Which block runs short today, and by how much?'},
    {g:'work', t:'say',    q:'The next parent email — what’s it asking for?'},
    {g:'work', t:'who',    q:'In the night class, who speaks first and who not at all?'},
    {g:'work', t:'who',    q:'Which kid in Block B surprises you this week, and in which direction?'},
    // students
    {g:'students', t:'who',    q:'Who’s absent today from Block A — name one, before you take attendance.'},
    {g:'students', t:'who',    q:'Which student finishes the task first, and which one hasn’t started by the ten-minute mark?'},
    {g:'students', t:'say',    q:'The first question a student asks today — what is it, and is it about the work or about something else?'},
    {g:'students', t:'who',    q:'Who comes up to your desk at the end of the block, and why?'},
    {g:'students', t:'who',    q:'Which kid is in a visibly different mood from yesterday — better or worse?'},
    {g:'students', t:'who',    q:'When you hand the writing back, who reads the comment and who flips straight to the mark?'},
    {g:'students', t:'happen', q:'The pair you put together today — do they work, or does one carry the other?'},
    {g:'students', t:'who',    q:'Who in the supplemental block surprises you this week, and which direction?'},
    {g:'students', t:'who',    q:'Which student mentions something from home this week without being asked?'},
    {g:'students', t:'who',    q:'In the night class, who’s improved most since September — and does that match who thinks they have?'},
    {g:'students', t:'happen', q:'The one kid you’re worried about — what does he do today that tells you whether you’re right?'}
  ];
  var NO_REPEAT_DAYS = 21, LEAN_AFTER = 20;

  function dayIndex(ymd){ var p=ymd.split('-'); return Math.round(Date.UTC(+p[0],+p[1]-1,+p[2])/86400000); }
  function daysBetween(a,b){ return dayIndex(b)-dayIndex(a); }

  /* Hit rate per type from resolved predictions; returns the weakest type with n>=4, or null. */
  function weakestType(store){
    var preds=(store&&store.preds)||[]; var n={}, h={};
    preds.forEach(function(p){ if(!p||!p.type||!(p.res==='hit'||p.res==='miss')) return; n[p.type]=(n[p.type]||0)+1; if(p.res==='hit') h[p.type]=(h[p.type]||0)+1; });
    var total=0; Object.keys(n).forEach(function(k){ total+=n[k]; });
    if(total<LEAN_AFTER) return null;
    var worst=null, rate=2;
    Object.keys(n).forEach(function(k){ if(n[k]>=4){ var r=(h[k]||0)/n[k]; if(r<rate){ rate=r; worst=k; } } });
    return worst;
  }

  /* Deterministic for a given date + store. If the store already pins today's prompt, return it. */
  function pick(ymd, store){
    store=store||{}; var seen=store.pseen||{};
    for(var k in seen){ if(seen[k]===ymd && POOL[+k]) return {idx:+k, p:POOL[+k], pinned:true}; }
    var di=dayIndex(ymd);
    var fresh=function(i){ var s=seen[i]; return !s || daysBetween(s,ymd)>=NO_REPEAT_DAYS; };
    var weak=weakestType(store);
    var cands=null;
    if(weak && di%2===1){ cands=[]; POOL.forEach(function(p,i){ if(p.t===weak && fresh(i)) cands.push(i); }); if(!cands.length) cands=null; }
    if(!cands){
      for(var step=0; step<GROUPS.length && !cands; step++){
        var g=GROUPS[(di+step)%GROUPS.length]; var c=[]; POOL.forEach(function(p,i){ if(p.g===g && fresh(i)) c.push(i); });
        if(c.length) cands=c;
      }
    }
    if(!cands){ cands=[]; POOL.forEach(function(p,i){ cands.push(i); }); }   // everything seen recently: allow repeats
    var idx=cands[Math.floor(di/GROUPS.length)%cands.length];
    return {idx:idx, p:POOL[idx], pinned:false};
  }

  function pin(store, ymd, idx){ if(!store.pseen||typeof store.pseen!=='object') store.pseen={}; store.pseen[idx]=ymd; return store; }
  function loggedOn(store, ymd){ return ((store&&store.preds)||[]).filter(function(p){ return p && p.t===ymd; }).length; }
  function dueBy(store, ymd){ return ((store&&store.preds)||[]).filter(function(p){ return p && !p.res && p.due && p.due<=ymd; }); }

  window.TLB_PROMPTS = { POOL:POOL, TYPES:TYPES, GROUPS:GROUPS, GLABEL:GLABEL, DOMAIN:DOMAIN, KEY:'forge-think-like-boyd',
    pick:pick, pin:pin, loggedOn:loggedOn, dueBy:dueBy, weakestType:weakestType, dayIndex:dayIndex };
})();
