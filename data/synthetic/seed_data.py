"""Synthetic but realistic deal history for the DealMind demo.

Seller: Northwind Analytics (fictional) — data observability platform, Hyderabad.
Competitors: Stratify (cheaper, only SOC2 Type I) and LensIQ (enterprise, ~3-month onboarding).
All companies and people are fictional.

Storylines planted (never stated as "lessons" inside the interactions):
  * Meridian Payments — LOST to Stratify: rep discounted 20% on the first CFO call, kept moving the
    price, and delivered the SOC2 report three weeks late. The CISO disengaged.
  * Kestrel Health — WON vs Stratify: price answered with a TCO walkthrough + paid 90-day pilot;
    SOC2 sent proactively, and the CISO became a champion; discount traded only for a 2-year term.
  * Orbitra Logistics — WON vs LensIQ: the "enterprise-grade" objection was beaten with a 2-week POC
    and a scale reference; the budget freeze was handled with phased billing.
  * Tarang Payments — LIVE, before call 4: same pattern as Meridian (CFO price pressure, Stratify,
    an overdue SOC2 promise).
"""

REP = "Rahul Verma (AE, Northwind)"
SE = "Sneha Iyer (Solutions Engineer, Northwind)"

DEALS = [
    # ------------------------------------------------------------------ MERIDIAN (lost)
    {
        "id": "meridian",
        "name": "Meridian Payments — Data Observability",
        "company": "Meridian Payments",
        "industry": "Fintech",
        "amount": 4200000,
        "stage": "Negotiation",
        "primary_competitor": "Stratify",
        "persona": "CFO",
        "description": "Mumbai-based payment gateway, ~600 employees. Reconciliation pipeline incidents.",
        "stakeholders": [
            ("Vikram Desai", "CFO", "skeptic"),
            ("Anjali Rao", "VP Engineering", "champion"),
            ("Farhan Sheikh", "CISO", "neutral"),
            ("Meera Kulkarni", "Head of Procurement", "neutral"),
        ],
        "interactions": [
            {
                "id": "mer-1", "type": "call", "date": "2026-03-03T11:00:00+05:30",
                "title": "Discovery call with VP Engineering",
                "participants": [REP, "Anjali Rao (VP Engineering)"],
                "content": """Rahul (AE): Thanks for making time, Anjali. You mentioned on LinkedIn the settlements team had a rough quarter?
Anjali Rao (VP Engineering): Rough is polite. We had three incidents last quarter where the reconciliation pipeline silently dropped records. Merchants saw settlement mismatches before we did. One of them was a top-20 merchant, so it went up to the CEO.
Rahul (AE): How did you find out each time?
Anjali Rao (VP Engineering): Merchant support tickets. Which is the worst way. By the time we traced it, it was two days of backfill.
Rahul (AE): That's exactly the pattern we catch — freshness and volume anomalies on the pipeline itself, before the downstream report breaks. What are you using today?
Anjali Rao (VP Engineering): Some dbt tests and a Grafana board nobody looks at. We're also talking to Stratify, they came in through our AWS rep.
Rahul (AE): Fair. What would make this a priority budget-wise?
Anjali Rao (VP Engineering): Honestly the CFO, Vikram, has to sign. He'll want numbers. I'm sold on the problem, he's not sold on the spend.
Rahul (AE): Understood. Can we get thirty minutes with Vikram in the next two weeks? I'll bring pricing and our Solutions Engineer.
Anjali Rao (VP Engineering): I'll set it up. Keep it tight, he hates long decks.""",
            },
            {
                "id": "mer-2", "type": "call", "date": "2026-03-17T16:00:00+05:30",
                "title": "Pricing call with CFO",
                "participants": [REP, SE, "Vikram Desai (CFO)", "Anjali Rao (VP Engineering)"],
                "content": """Vikram Desai (CFO): Let me be direct. Your proposal says forty-two lakh a year. Stratify quoted us thirty. Why is this worth twelve lakh more?
Rahul (AE): I hear you, Vikram. Look, we really want Meridian as a logo in fintech. If price is the blocker, I can do twenty percent off — that brings it to about thirty-three point six.
Vikram Desai (CFO): (pause) Twenty percent on the first call. So what's the actual price?
Rahul (AE): That's our best number, honestly. I had to push internally.
Vikram Desai (CFO): Hmm. Anjali, is the product actually better or is this just a pricing game?
Anjali Rao (VP Engineering): The lineage view is better. Sneha showed us root cause in two clicks.
Sneha (SE): And we'd have the reconciliation monitors live in about a week.
Vikram Desai (CFO): Fine. Security has to clear any vendor touching settlement data. Farhan will want your compliance documents.
Rahul (AE): Of course. I'll get our SOC2 Type II report to Farhan by the 24th.
Vikram Desai (CFO): Send the revised quote to Meera in procurement. And I'll be honest, I'm going to show your number to Stratify.
Rahul (AE): Understood. We'll send it today.""",
            },
            {
                "id": "mer-3", "type": "email", "date": "2026-03-26T10:12:00+05:30",
                "title": "CISO: SOC2 report still pending",
                "participants": ["Farhan Sheikh (CISO)", REP],
                "content": """From: Farhan Sheikh (CISO, Meridian Payments)
To: Rahul Verma
Subject: Vendor security review — Northwind

Hi Rahul,

Vikram mentioned you would share your SOC2 Type II report by the 24th. I haven't received it yet. I can't start the vendor risk assessment without it, and our committee meets on the 9th of April.

Please also include your data residency details — settlement data cannot leave India.

Regards,
Farhan""",
            },
            {
                "id": "mer-4", "type": "call", "date": "2026-04-07T15:30:00+05:30",
                "title": "Negotiation with CFO and Procurement",
                "participants": [REP, "Vikram Desai (CFO)", "Meera Kulkarni (Head of Procurement)"],
                "content": """Meera Kulkarni (Procurement): We've reviewed the revised quote at thirty-three point six. Stratify has come back at twenty-nine with a two-year lock.
Vikram Desai (CFO): So, Rahul, you dropped twenty percent without us asking twice. What happens if we ask again?
Rahul (AE): I can go to thirty lakh flat. That's genuinely the floor, I'll need VP approval.
Vikram Desai (CFO): The number keeps moving, which makes me wonder what we're actually paying for.
Rahul (AE): The value is the reduction in incidents — Anjali's team lost two days per incident last quarter.
Vikram Desai (CFO): Stratify says they do the same thing.
Meera Kulkarni (Procurement): Also, Farhan tells me security review hasn't started on your side. Is there a blocker?
Rahul (AE): My apologies — the SOC2 report is with our compliance team, I'll chase it today.
Vikram Desai (CFO): Let's pause here. Send the thirty-lakh quote and the security documents, and we'll decide by end of month.""",
            },
            {
                "id": "mer-5", "type": "email", "date": "2026-04-14T18:40:00+05:30",
                "title": "SOC2 report sent (late)",
                "participants": [REP, "Farhan Sheikh (CISO)"],
                "content": """From: Rahul Verma
To: Farhan Sheikh
Subject: RE: Vendor security review — Northwind

Hi Farhan, apologies for the delay. Attaching our SOC2 Type II report and data residency note (Mumbai region, AWS ap-south-1).

---
From: Farhan Sheikh
Reply: Thanks. Our committee met on the 9th without it, so this goes to the May cycle. I've let Vikram know.""",
            },
            {
                "id": "mer-6", "type": "call", "date": "2026-04-28T12:00:00+05:30",
                "title": "Loss call with VP Engineering",
                "participants": [REP, "Anjali Rao (VP Engineering)"],
                "content": """Anjali Rao (VP Engineering): I wanted to tell you personally. We're going with Stratify.
Rahul (AE): I appreciate you telling me. Can I ask what tipped it?
Anjali Rao (VP Engineering): Two things. Vikram felt the pricing kept moving — once it dropped twenty percent on day one, he stopped believing the list price meant anything. He said Stratify at least felt consistent.
Rahul (AE): And the second?
Anjali Rao (VP Engineering): Farhan. The security review slipped a whole cycle because the SOC2 came three weeks late. He told the committee Northwind "didn't treat security as a priority." Stratify only has Type I but they turned documents around in two days.
Rahul (AE): That's fair feedback. Is there anything that would reopen this?
Anjali Rao (VP Engineering): Not this year. I still think your product is better, for what it's worth.""",
            },
        ],
        "tactic_outcomes": [
            {"category": "price", "persona": "CFO", "tactic": "Early discount (20% on first pricing call)",
             "objection": "Stratify quoted us ₹30L, why is this worth ₹12L more?", "worked": False,
             "note": "CFO read the instant discount as a sign that the list price was inflated and stopped trusting later numbers.",
             "date": "2026-03-17"},
            {"category": "competitor", "persona": "Procurement", "tactic": "Match competitor price",
             "objection": "Stratify is at ₹29L with a two-year lock", "worked": False,
             "note": "Matching Stratify turned the deal into a pure price contest; Stratify still won.",
             "date": "2026-04-07"},
            {"category": "security", "persona": "CISO", "tactic": "Send SOC2 report when asked (reactive)",
             "objection": "Can't start vendor risk review without your SOC2 report", "worked": False,
             "note": "The report arrived 3 weeks late; the security committee slipped a cycle and the CISO turned negative.",
             "date": "2026-04-14"},
        ],
        "close": {"result": "lost", "date": "2026-04-30T10:00:00+05:30",
                  "reason": "Lost to Stratify. Early 20% discount eroded price credibility with the CFO; the SOC2 report was 3 weeks late and the CISO disengaged."},
    },
    # ------------------------------------------------------------------ KESTREL (won)
    {
        "id": "kestrel",
        "name": "Kestrel Health — Claims Data Reliability",
        "company": "Kestrel Health",
        "industry": "Healthtech",
        "amount": 4800000,
        "stage": "Negotiation",
        "primary_competitor": "Stratify",
        "persona": "CFO",
        "description": "Bengaluru health-insurance TPA platform. Claims pipeline data-quality incidents; DPDP compliance pressure.",
        "stakeholders": [
            ("Neha Kapoor", "CFO", "skeptic"),
            ("Arjun Nair", "VP Engineering", "champion"),
            ("David Thomas", "CISO", "neutral"),
            ("Sameer Joshi", "Procurement Manager", "neutral"),
        ],
        "interactions": [
            {
                "id": "kes-1", "type": "call", "date": "2026-04-08T11:30:00+05:30",
                "title": "Discovery with VP Engineering",
                "participants": [REP, "Arjun Nair (VP Engineering)"],
                "content": """Arjun Nair (VP Engineering): Our claims pipeline processes about 90,000 claims a day. Twice this year a schema change upstream broke adjudication data and we paid out on incorrect amounts before anyone noticed.
Rahul (AE): What did that cost?
Arjun Nair (VP Engineering): The second one was around six lakh in overpayments plus a week of three engineers doing cleanup. And with DPDP coming in, compliance wants to know where every patient field flows.
Rahul (AE): That's lineage plus schema-change detection — core for us. Who else is looking at this?
Arjun Nair (VP Engineering): We got a quote from Stratify. Cheaper. But our CFO Neha will decide on numbers, not features.
Rahul (AE): Then let's make it about numbers. Can you share the incident timeline? I'll build a cost model before I meet Neha.
Arjun Nair (VP Engineering): Sure, I'll send it tomorrow.""",
            },
            {
                "id": "kes-2", "type": "call", "date": "2026-04-22T15:00:00+05:30",
                "title": "CFO pricing conversation",
                "participants": [REP, SE, "Neha Kapoor (CFO)", "Arjun Nair (VP Engineering)"],
                "content": """Neha Kapoor (CFO): Stratify is at thirty-four lakh. You're at forty-eight. I need a reason that isn't a feature list.
Rahul (AE): Completely fair. I'm not going to argue on list price — let me show you the cost side instead. Arjun shared two incidents this year: six lakh in overpayments on one, plus roughly 120 engineer-hours of cleanup each. At your loaded cost that's about eleven lakh a year in incidents we'd expect to catch before payout.
Neha Kapoor (CFO): Expect. That's the word I don't like.
Rahul (AE): Which is why I don't want you to take my word for it. Run a 90-day paid pilot on the claims pipeline — nine lakh, fully credited to the annual contract if you continue. If we don't catch real issues, you walk away.
Neha Kapoor (CFO): (pause) That's a more reasonable conversation than a discount. What does Stratify's pilot look like, Arjun?
Arjun Nair (VP Engineering): They offered a free trial on sample data. Not our production claims.
Neha Kapoor (CFO): Send me the TCO model and the pilot terms. And security needs to clear you first — David is strict.
Rahul (AE): I'll send David our SOC2 Type II and a DPDP data-flow mapping tomorrow, before he asks.""",
            },
            {
                "id": "kes-3", "type": "email", "date": "2026-04-23T09:05:00+05:30",
                "title": "Proactive security pack to CISO",
                "participants": [REP, "David Thomas (CISO)"],
                "content": """From: Rahul Verma
To: David Thomas (CISO, Kestrel Health)
Subject: Northwind security pack — ahead of your review

Hi David,
Neha mentioned you'd lead vendor security. To save you a round trip, attached: SOC2 Type II (Dec 2025), pen-test summary, DPDP data-flow mapping for claims fields, and our India data residency note (AWS Mumbai). Happy to do a 30-min call with our security lead.

---
From: David Thomas
Reply: This is the first vendor that sent this before I asked. Let's do the call on May 12.""",
            },
            {
                "id": "kes-4", "type": "call", "date": "2026-05-12T14:00:00+05:30",
                "title": "Security review with CISO",
                "participants": [REP, SE, "David Thomas (CISO)", "Arjun Nair (VP Engineering)"],
                "content": """David Thomas (CISO): I went through the pack. Two questions: does any PHI leave India, and can we restrict your agent to metadata only?
Sneha (SE): Nothing leaves ap-south-1, and yes — metadata-only mode means we read schemas, row counts and freshness, never values.
David Thomas (CISO): Good. For comparison, Stratify only has SOC2 Type I and said Type II is "in progress".
Arjun Nair (VP Engineering): David, can we start the pilot on the claims pipeline then?
David Thomas (CISO): From my side, yes. I'll tell Neha security is cleared. Honestly, the fact you came prepared made this easy.""",
            },
            {
                "id": "kes-5", "type": "call", "date": "2026-06-03T16:00:00+05:30",
                "title": "Pilot readout",
                "participants": [REP, SE, "Neha Kapoor (CFO)", "Arjun Nair (VP Engineering)", "David Thomas (CISO)"],
                "content": """Sneha (SE): Six weeks into the pilot: 14 anomalies flagged, two of them upstream schema changes that would have hit adjudication. Arjun's team fixed both before payout.
Arjun Nair (VP Engineering): One of those would've been the same failure as February.
Neha Kapoor (CFO): So that's one avoided incident, conservatively five to six lakh. The pilot already paid for most of itself.
David Thomas (CISO): And zero security findings during the pilot.
Neha Kapoor (CFO): Fine. Let's move to contract. Sameer from procurement will negotiate terms.""",
            },
            {
                "id": "kes-6", "type": "call", "date": "2026-06-24T11:00:00+05:30",
                "title": "Procurement negotiation",
                "participants": [REP, "Sameer Joshi (Procurement Manager)"],
                "content": """Sameer Joshi (Procurement): Standard ask — fifteen percent off, and net-60 payment terms.
Rahul (AE): I can't move fifteen on a one-year deal. If Kestrel commits to two years, I can do five percent, and we'd love to do a joint case study on the pilot results.
Sameer Joshi (Procurement): Five for two years plus a case study... Neha will like the multi-year predictability. Net-45?
Rahul (AE): Net-45 works.
Sameer Joshi (Procurement): Then send the paper. We'll sign this week.""",
            },
        ],
        "tactic_outcomes": [
            {"category": "price", "persona": "CFO", "tactic": "TCO reframe + 90-day paid pilot credited to annual",
             "objection": "Stratify is at ₹34L, you're at ₹48L", "worked": True,
             "note": "The CFO called it 'a more reasonable conversation than a discount'; the pilot proved ₹5-6L in avoided loss and the deal closed at near list price.",
             "date": "2026-04-22"},
            {"category": "security", "persona": "CISO", "tactic": "Proactive security pack (SOC2 Type II + data residency) before being asked",
             "objection": "Security needs to clear you first", "worked": True,
             "note": "The CISO said we were the first vendor to send it before asking, and became a champion. Stratify only has SOC2 Type I.",
             "date": "2026-05-12"},
            {"category": "price", "persona": "Procurement", "tactic": "Trade discount only for a multi-year commitment + case study",
             "objection": "Standard ask: 15% off", "worked": True,
             "note": "Gave 5% for a 2-year term instead of 15%; procurement accepted.",
             "date": "2026-06-24"},
        ],
        "close": {"result": "won", "date": "2026-06-26T17:00:00+05:30",
                  "reason": "Won vs Stratify at ₹45.6L/yr over 2 years. TCO + paid pilot beat the price objection; the proactive security pack won the CISO."},
    },
    # ------------------------------------------------------------------ ORBITRA (won)
    {
        "id": "orbitra",
        "name": "Orbitra Logistics — Shipment Data Platform",
        "company": "Orbitra Logistics",
        "industry": "Logistics",
        "amount": 3600000,
        "stage": "Negotiation",
        "primary_competitor": "LensIQ",
        "persona": "CTO",
        "description": "Chennai 3PL with a real-time shipment ETA platform; 2B events/day.",
        "stakeholders": [
            ("Karthik Subramanian", "CTO", "skeptic"),
            ("Rohan Mehta", "Head of Data", "champion"),
            ("Lakshmi Menon", "CFO", "neutral"),
        ],
        "interactions": [
            {
                "id": "orb-1", "type": "call", "date": "2026-05-05T10:00:00+05:30",
                "title": "Discovery with Head of Data",
                "participants": [REP, "Rohan Mehta (Head of Data)"],
                "content": """Rohan Mehta (Head of Data): Our ETA predictions feed customer SLAs. When GPS feeds go stale, ETAs drift and we pay SLA penalties — about four lakh last month alone.
Rahul (AE): How quickly do you detect a stale feed today?
Rohan Mehta (Head of Data): Hours. Sometimes a customer tells us.
Rahul (AE): We'd detect freshness drops within minutes per feed. Who else are you looking at?
Rohan Mehta (Head of Data): LensIQ. Our CTO Karthik likes them because they're "enterprise-grade". Their onboarding plan is three months though.
Rahul (AE): Let's get in front of Karthik. What does he care about most?
Rohan Mehta (Head of Data): Scale. We're at two billion events a day. He'll assume a smaller vendor falls over.""",
            },
            {
                "id": "orb-2", "type": "call", "date": "2026-05-20T15:00:00+05:30",
                "title": "CTO technical evaluation",
                "participants": [REP, SE, "Karthik Subramanian (CTO)", "Rohan Mehta (Head of Data)"],
                "content": """Karthik Subramanian (CTO): I'll be blunt. LensIQ is enterprise-grade. You're a startup. Why would I bet our SLA platform on you at two billion events a day?
Rahul (AE): Fair challenge. Two things. One of our customers, a large e-commerce marketplace, runs us on four billion events a day — I can get you their platform lead on a call. Two, don't trust slides: give us your biggest pipeline for a two-week proof of concept. If we're not live and catching real issues in two weeks, you have your answer.
Karthik Subramanian (CTO): Two weeks. LensIQ's plan is twelve weeks just to onboard.
Sneha (SE): We connect read-only to Kafka and your warehouse; no agents on your hosts.
Karthik Subramanian (CTO): Okay. Rohan, give them the GPS ingestion pipeline. And set up that reference call.""",
            },
            {
                "id": "orb-3", "type": "call", "date": "2026-06-10T16:30:00+05:30",
                "title": "POC readout",
                "participants": [REP, SE, "Karthik Subramanian (CTO)", "Rohan Mehta (Head of Data)"],
                "content": """Sneha (SE): We went live on day two. Over twelve days, 31 freshness incidents on GPS feeds, median detection time four minutes. Three would have breached customer SLAs.
Rohan Mehta (Head of Data): We fixed all three before the SLA window. That's real money.
Karthik Subramanian (CTO): And the reference call with the marketplace team was convincing. They've had you at double our volume for a year.
Karthik Subramanian (CTO): LensIQ still hasn't finished their architecture review. I'm comfortable. Talk to Lakshmi on commercials.""",
            },
            {
                "id": "orb-4", "type": "email", "date": "2026-06-18T12:20:00+05:30",
                "title": "CFO: budget freeze",
                "participants": ["Lakshmi Menon (CFO)", REP],
                "content": """From: Lakshmi Menon (CFO, Orbitra Logistics)
To: Rahul Verma
Subject: Northwind commercials

Rahul — Karthik is keen, but we have a discretionary spend freeze until Q3 (July). I can't sign thirty-six lakh upfront this quarter. Please advise.

---
From: Rahul Verma
Reply: Understood, Lakshmi. Proposal: contract start 1 July on your Q3 budget, billed quarterly (₹9L/quarter), with the POC environment kept live free until then so the team doesn't lose coverage. No change to the annual price.

---
From: Lakshmi Menon
Reply: That works. Send the order form dated July 1.""",
            },
            {
                "id": "orb-5", "type": "call", "date": "2026-07-15T11:00:00+05:30",
                "title": "Final alignment",
                "participants": [REP, "Karthik Subramanian (CTO)", "Lakshmi Menon (CFO)"],
                "content": """Lakshmi Menon (CFO): Order form is approved. Quarterly billing from July.
Karthik Subramanian (CTO): And we've informed LensIQ. Their three-month onboarding was the deal-breaker next to your two-week POC.
Rahul (AE): Thank you both. Sneha will run the production rollout starting Monday.""",
            },
        ],
        "tactic_outcomes": [
            {"category": "competitor", "persona": "CTO", "tactic": "2-week POC on their biggest pipeline",
             "objection": "LensIQ is enterprise-grade, you're a startup", "worked": True,
             "note": "Live on day 2 vs LensIQ's 12-week onboarding; the CTO cited it as the deal-breaker.",
             "date": "2026-05-20"},
            {"category": "technical_fit", "persona": "CTO", "tactic": "Customer reference at higher scale",
             "objection": "Will you fall over at 2B events/day?", "worked": True,
             "note": "The reference customer at 4B events/day removed the scale doubt.",
             "date": "2026-06-10"},
            {"category": "timing", "persona": "CFO", "tactic": "Phased/quarterly billing aligned to the budget cycle",
             "objection": "Spend freeze until Q3", "worked": True,
             "note": "Kept the annual price intact; the start date moved to Q3 with quarterly billing.",
             "date": "2026-06-18"},
        ],
        "close": {"result": "won", "date": "2026-07-22T15:00:00+05:30",
                  "reason": "Won vs LensIQ at list price. The 2-week POC beat the 'enterprise-grade' objection; quarterly billing solved the budget freeze."},
    },
    # ------------------------------------------------------------------ TARANG (live)
    {
        "id": "tarang",
        "name": "Tarang Payments — Reconciliation Observability",
        "company": "Tarang Payments",
        "industry": "Fintech",
        "amount": 4500000,
        "stage": "Evaluation",
        "primary_competitor": "Stratify",
        "persona": "CFO",
        "next_meeting": "2026-09-30T15:00:00+05:30",
        "description": "Hyderabad UPI and card payments processor, ~900 employees. RBI audit pressure on reconciliation.",
        "stakeholders": [
            ("Priya Menon", "CFO", "skeptic"),
            ("Aditya Reddy", "VP Engineering", "champion"),
            ("Kavya Srinivasan", "CISO", "neutral"),
            ("Imran Qureshi", "Procurement Lead", "neutral"),
        ],
        "interactions": [
            {
                "id": "tar-1", "type": "call", "date": "2026-08-18T11:00:00+05:30",
                "title": "Discovery with VP Engineering",
                "participants": [REP, "Aditya Reddy (VP Engineering)"],
                "content": """Aditya Reddy (VP Engineering): We process around 40 lakh UPI transactions a day. The reconciliation pipeline has broken four times since April. Each time finance found the mismatch at month-end close.
Rahul (AE): Four times. What happened after the last one?
Aditya Reddy (VP Engineering): RBI's inspection team asked for our data-quality controls on reconciliation. We didn't have a good answer. Our CEO wants this fixed before the December audit.
Rahul (AE): That's squarely what we do — freshness, volume and schema monitors on the reconciliation tables, with lineage back to the source. Anyone else in the mix?
Aditya Reddy (VP Engineering): Stratify reached out. They're cheaper, I hear. I'd rather go with whoever actually works, but I don't hold the budget.
Rahul (AE): Who does?
Aditya Reddy (VP Engineering): Priya Menon, our CFO. She's sharp and very price-disciplined. And Kavya, our CISO, has to approve any vendor touching transaction data.
Rahul (AE): Let's get Priya in the next two weeks. I'll bring numbers.""",
            },
            {
                "id": "tar-2", "type": "call", "date": "2026-09-02T16:00:00+05:30",
                "title": "First call with CFO",
                "participants": [REP, SE, "Priya Menon (CFO)", "Aditya Reddy (VP Engineering)"],
                "content": """Priya Menon (CFO): I've seen the proposal. Forty-five lakh a year is steep. Stratify quoted thirty-two.
Rahul (AE): Understood. We think the value is there, but let me see what I can do on price.
Priya Menon (CFO): I'll be honest, my ceiling this financial year is around thirty-eight. Anything above that needs board approval, and I won't take it to the board for a monitoring tool.
Aditya Reddy (VP Engineering): Priya, the December RBI audit is the real driver here.
Priya Menon (CFO): I know. That's why we're talking at all. What I need is confidence this actually reduces month-end breaks.
Sneha (SE): We'd have reconciliation monitors live within a week of connecting to your warehouse.
Priya Menon (CFO): Also, Kavya won't let anyone near transaction data without a security review. She needs your SOC2 and an RBI data-localisation note.
Rahul (AE): I'll send both to Kavya by the 9th.
Priya Menon (CFO): Fine. Let's reconvene after security has looked.""",
            },
            {
                "id": "tar-3", "type": "email", "date": "2026-09-10T09:45:00+05:30",
                "title": "CISO: SOC2 report not received",
                "participants": ["Kavya Srinivasan (CISO)", REP],
                "content": """From: Kavya Srinivasan (CISO, Tarang Payments)
To: Rahul Verma
Subject: Northwind — security documents

Hi Rahul,

Priya said you'd send the SOC2 report and the RBI data-localisation note by the 9th. I haven't received them. Our vendor risk committee meets on 25 September, and I need at least a week to review.

Thanks,
Kavya""",
            },
            {
                "id": "tar-4", "type": "call", "date": "2026-09-16T14:30:00+05:30",
                "title": "Technical deep dive",
                "participants": [REP, SE, "Aditya Reddy (VP Engineering)", "Kavya Srinivasan (CISO)"],
                "content": """Sneha (SE): Here's the lineage from the NPCI settlement files through to the reconciliation mart. A delayed file shows up as a freshness break here, within minutes.
Aditya Reddy (VP Engineering): This is exactly what we needed in July.
Kavya Srinivasan (CISO): I joined for ten minutes. Two things: I need SOC2 Type II specifically — Type I won't pass our committee — and confirmation that nothing leaves India. I still don't have your documents.
Rahul (AE): My apologies, Kavya. I'll get them to you right after this call.
Kavya Srinivasan (CISO): Please do. The committee is on the 25th.
Aditya Reddy (VP Engineering): One more thing, Rahul. Priya asked me directly whether you can "match Stratify." I told her the product isn't comparable, but she's going to push. Imran from procurement will join the next call too.""",
            },
            {
                "id": "tar-5", "type": "email", "date": "2026-09-23T19:10:00+05:30",
                "title": "CFO: come with your best price",
                "participants": ["Priya Menon (CFO)", REP],
                "content": """From: Priya Menon (CFO, Tarang Payments)
To: Rahul Verma
Cc: Imran Qureshi (Procurement), Aditya Reddy
Subject: Our call on 30 September

Rahul,

Before our call on the 30th, please come with your best price. Stratify has given us a final offer at ₹31L for year one. Imran will join to discuss terms.

Also, Kavya tells me she still hasn't received your SOC2 report, two weeks after it was promised, and her committee meets on the 25th. If security can't review in time, this slips to the November cycle. I'd like to understand what is happening there.

Regards,
Priya""",
            },
        ],
        "tactic_outcomes": [],
        "close": None,
    },
]

# Things the rep's own memory bank knows.
REP_MEMORIES = [
    ("2026-02-10", "Rahul prefers crisp briefs: the single biggest risk first, then at most 5 bullets per section. He skips long competitor background."),
    ("2026-05-06", "Coaching note from sales manager (after the Meridian Payments loss): under CFO price pressure Rahul tends to offer discounts too early. Coach him to reframe on total cost of ownership and offer a paid pilot instead."),
    ("2026-07-01", "Coaching note: Rahul sometimes lets security follow-ups slip. Security documents should go out proactively within 24 hours of any CISO being mentioned."),
]
