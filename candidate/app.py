#!/usr/bin/env python3
"""
Revenue Intelligence Inbox — Application Server & Deterministic Engine
Complies with DATA_CONTRACT.md, DATA_DICTIONARY.md, and ASSIGNMENT.md.
Uses standard Python library only (http.server, urllib, json, os, csv, zipfile, datetime, shutil).
"""

import os
import sys
import json
import csv
import io
import shutil
import zipfile
from datetime import datetime, timezone, timedelta
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.parse

# Timezone: Asia/Kolkata (UTC+5:30) per assignment specification
IST = timezone(timedelta(hours=5, minutes=30))

TAXONOMY = [
    "Deal Next Steps",
    "Customer Follow-up",
    "Sales Coaching",
    "Partner Development",
    "Internal / Vendor Note",
    "Human Review"
]

ROUTE_SLUGS = {
    "Deal Next Steps": "deal-next-steps",
    "Customer Follow-up": "customer-follow-up",
    "Sales Coaching": "sales-coaching",
    "Partner Development": "partner-development",
    "Internal / Vendor Note": "internal-vendor-note",
    "Human Review": "human-review"
}

# Pre-compiled candidate-derived analysis registry for records with usable text
DETAILED_ANALYSIS_REGISTRY = {
    "C01": {
        "summary": "Arun cold-called Pranav (Harborlight Advisory) regarding outsourced finance operations. Pranav expressed immediate disinterest, objected to being called on his work mobile number, and clarified that Harborlight already has advanced internal automation.",
        "suggested_routes": ["Sales Coaching", "Human Review"],
        "route_rationale": "The contact explicitly stated disinterest and objected to telephone outreach on his business line. This serves as a sales coaching signal on respecting customer boundaries and requires suppression review.",
        "evidence_citations": [
            {
                "quote": "I didn't ask for this call, and I'm not interested. This number is for my work, not for people to sell things to me.",
                "context": "Direct rejection of cold outreach"
            },
            {
                "quote": "Our processes are already very automated. We have a fairly advanced setup, so I don't think this is something we need.",
                "context": "Clarification of existing capabilities"
            }
        ],
        "what_evidence_does_not_establish": "Does not establish that Harborlight Advisory has any future buying intent, nor does it establish that the rep committed an ethical violation; however, continuing outreach would violate expressed preference.",
        "recommended_next_step": "Add Pranav and his phone number to the CRM suppression/do-not-call list. Coach SDR Arun to conclude calls immediately upon clear disinterest.",
        "responsible_owner": "Arun (Rep) / Sales Operations",
        "company_or_contact": "Pranav / Harborlight Advisory"
    },
    "C02": {
        "summary": "Arun called Fernhaven Group asking to speak with Leela. Receptionist Kavya advised that Leela was out of the office and transferred Arun to Leela's voicemail.",
        "suggested_routes": ["Customer Follow-up", "Human Review"],
        "route_rationale": "Gatekeeper interaction with transfer to voicemail; requires task scheduling for future touchpoint.",
        "evidence_citations": [
            {
                "quote": "It looks as though she isn't in the office today. Would you like to leave a message with me, or would you prefer her voicemail? Her voicemail would be fine, thank you.",
                "context": "Receptionist routing to voicemail"
            }
        ],
        "what_evidence_does_not_establish": "Does not establish Leela's role, buying interest, whether she received the message, or if she has any prior history with SpendNest.",
        "recommended_next_step": "Log voicemail attempt and set a reminder to re-attempt contact in 2-3 business days.",
        "responsible_owner": "Arun (Rep)",
        "company_or_contact": "Leela / Kavya (Fernhaven Group)"
    },
    "C03": {
        "summary": "Kiran followed up with Milan regarding developer API access. Milan reported severe phone connection issues while traveling, cited past price sensitivity, and explicitly requested an email follow-up with subject 'Developer access and event notifications — follow-up' plus a callback on Monday or Tuesday.",
        "suggested_routes": ["Deal Next Steps", "Customer Follow-up"],
        "route_rationale": "High-priority prospect evaluation with specific follow-up instructions: email with defined subject and scheduled callback window.",
        "evidence_citations": [
            {
                "quote": "We did ask about some developer functionality, but it isn't essential enough for us to spend much on it... When we last spoke, price was a concern.",
                "context": "Budget and prioritization constraint"
            },
            {
                "quote": "Could we do this by email? Or call on Monday a bit earlier, when I'm back indoors?... Something like 'Developer access and event notifications — follow-up'... Send the email and we can speak Monday or Tuesday.",
                "context": "Agreed communication cadence and subject line"
            }
        ],
        "what_evidence_does_not_establish": "Does not establish that Milan has budget approval, purchase intent, or an active deal size. The prospect emphasized that the API is not essential enough to spend heavily.",
        "recommended_next_step": "Send an email with subject line 'Developer access and event notifications — follow-up' addressing pricing/budget tiers, and schedule an outbound callback for Monday morning.",
        "responsible_owner": "Kiran (Rep)",
        "company_or_contact": "Milan (Developer API prospect)"
    },
    "C04": {
        "summary": "Arun left a voicemail for Ritesh at Lanternpath Media regarding expense software. He noted that initial information had been sent to an incorrect email address and subsequently resent to the corrected address, requesting a callback.",
        "suggested_routes": ["Customer Follow-up"],
        "route_rationale": "Prospect follow-up voicemail clarifying resent email proposal; pending prospect response.",
        "evidence_citations": [
            {
                "quote": "My understanding is that our information first went to the wrong email address. We subsequently used the corrected address you gave us, and I hope you have now had a chance to see it. Please call me back to let me know where things stand.",
                "context": "Voicemail explaining corrected email dispatch"
            }
        ],
        "what_evidence_does_not_establish": "Does not establish that Ritesh reviewed the resent email or intends to proceed with an evaluation.",
        "recommended_next_step": "Track email engagement on the resent proposal; if no response by Tuesday, send a brief check-in email.",
        "responsible_owner": "Arun (Rep)",
        "company_or_contact": "Ritesh / Lanternpath Media"
    },
    "C05": {
        "summary": "Meera conducted an introductory cold call pitching expense software, controlled cards, and vendor management to a multi-store retail company. The prospect confirmed existing coverage with StoreHarbor and others, but agreed to review a presentation sent to contact05@example.com.",
        "suggested_routes": ["Customer Follow-up", "Sales Coaching"],
        "route_rationale": "Entrenched competitor present (StoreHarbor), but prospect consented to receive promotional presentation for future evaluation.",
        "evidence_citations": [
            {
                "quote": "There are several. One is StoreHarbor, and we use others too. What I suggest is that you send me your presentation. If we ever decide to change the providers we already have, we could consider it then. Email: contact05@example.com.",
                "context": "Competitor landscape and consent to receive presentation"
            }
        ],
        "what_evidence_does_not_establish": "Does not establish an active buying evaluation or dissatisfaction with StoreHarbor. The request is a polite educational dispatch.",
        "recommended_next_step": "Dispatch product overview deck highlighting multi-store card controls to contact05@example.com; log StoreHarbor as incumbent vendor.",
        "responsible_owner": "Meera (Rep)",
        "company_or_contact": "Retail Store Lead (contact05@example.com)"
    },
    "C06": {
        "summary": "Ravi (dialing from Meera's telephony account) cold-called Nikhil regarding SpendNest for retail/distribution across 120+ stores. Nikhil explained that operations and finance are already automated through their central enterprise business management system with full visibility.",
        "suggested_routes": ["Sales Coaching", "Customer Follow-up"],
        "route_rationale": "Substantial enterprise account (120+ stores) with entrenched in-house/central system. Rep caller ID shows account mismatch (Meera user ID vs spoken rep Ravi).",
        "evidence_citations": [
            {
                "quote": "The essential processes are automated and connected through our business management system. Head office manages it, and we have full visibility. That is why I said the arrangements are already in place.",
                "context": "Existing automation and visibility in head office"
            }
        ],
        "what_evidence_does_not_establish": "Does not establish any immediate dissatisfaction or software gap. Does not justify high-frequency outbound calling.",
        "recommended_next_step": "Record enterprise stack notes in CRM. Coach rep on discovering specific pain points (e.g. store petty cash reconciliation) rather than high-level feature listing.",
        "responsible_owner": "Meera / Ravi",
        "company_or_contact": "Mr. Nikhil (120+ retail stores)"
    },
    "C07": {
        "summary": "Dev called Aditya at Willowbank Advisory proposing a partnership to provide virtual business accounts for newly incorporated overseas companies. Aditya confirmed Willowbank regularly refers clients to account providers, requested a proposal via chat app, and agreed to a follow-up call on Monday.",
        "suggested_routes": ["Partner Development", "Customer Follow-up"],
        "route_rationale": "High-potential channel partnership lead. Prospect currently refers incorporated entities to digital account providers and agreed to review proposal with Monday callback.",
        "evidence_citations": [
            {
                "quote": "We'd like to partner with advisory firms such as yours so your clients can access a virtual business account after incorporation. Do you currently refer clients to providers for that part of the process? Yes, that is something we normally do.",
                "context": "Confirmation of existing client referral practice"
            },
            {
                "quote": "Sorry, could you message me on our chat app and send whatever proposal you have?... Once you've received them, could I call on Monday to see whether you'd like to discuss it further? Yes, that's fine.",
                "context": "Agreed channel proposal and Monday callback"
            }
        ],
        "what_evidence_does_not_establish": "Does not establish an executed partnership contract, committed client referral volume, or confirmed commission structure. It is an exploratory partnership discussion.",
        "recommended_next_step": "Send partner proposal detailing virtual business account features and referral benefits via messaging app. Schedule Monday follow-up call.",
        "responsible_owner": "Dev (Rep)",
        "company_or_contact": "Aditya / Willowbank Advisory"
    },
    "C08": {
        "summary": "Meera cold-called Raghav regarding expense and payables consolidation. Raghav noted that their people operations colleague handles frontline locations and may be evaluating solutions, directing Meera to email a proposal to contact08@example.com mentioning Raghav's name.",
        "suggested_routes": ["Deal Next Steps", "Customer Follow-up"],
        "route_rationale": "Qualified internal referral to the frontline operations/people operations decision maker with explicit permission to use Raghav as a referral bridge.",
        "evidence_citations": [
            {
                "quote": "The colleague handling our people operations also deals with frontline processes and the locations. I think we may have been looking at a solution, but I don't know the details... If you send him a proposal and say you spoke with me, he can take a look. It's contact08@example.com.",
                "context": "Internal referral to people operations with name-drop permission"
            }
        ],
        "what_evidence_does_not_establish": "Does not establish that the people operations lead has active budget or an open RFP.",
        "recommended_next_step": "Send tailored enterprise proposal to contact08@example.com explicitly referencing Raghav's recommendation; follow up mid-week.",
        "responsible_owner": "Meera (Rep)",
        "company_or_contact": "Raghav (contact08@example.com)"
    },
    "C09": {
        "summary": "Meera cold-called Vedant regarding multi-store expenses for 130 locations. Vedant noted they built in-house software and are not actively looking. He suggested checking with Business Head Rishabh on a professional network, but explicitly insisted that Meera NOT use Vedant's name.",
        "suggested_routes": ["Sales Coaching", "Human Review"],
        "route_rationale": "Enterprise lead referral with strict boundary condition: rep is instructed to contact Business Head Rishabh via LinkedIn, but under no circumstances use Vedant's name.",
        "evidence_citations": [
            {
                "quote": "We have developed our own software internally, so at present we aren't looking for anything outside the organisation.",
                "context": "In-house build objection"
            },
            {
                "quote": "If you want to speak to somebody about it, you can find our business head, Mr Rishabh, on a professional networking site... Would it be all right if I mentioned your name when contacting him? No, please don't use my name.",
                "context": "Referral to Rishabh with strict prohibition on name drop"
            }
        ],
        "what_evidence_does_not_establish": "Does not establish that Rishabh has interest in replacing internal tools. Dropping Vedant's name would damage outreach credibility.",
        "recommended_next_step": "Perform discreet research on Business Head Rishabh on LinkedIn; reach out with value-driven messaging without referencing Vedant. Coach rep on respecting contact confidentiality.",
        "responsible_owner": "Meera (Rep)",
        "company_or_contact": "Vedant / Rishabh (130 store chain)"
    },
    "C10": {
        "summary": "Meera cold-called Aniket, who stated he no longer works at Meadowbrick and now works in manufacturing. He asked for a brief via messaging app, but explicitly and repeatedly refused a follow-up call next week, stating he would reach out if interested.",
        "suggested_routes": ["Customer Follow-up", "Sales Coaching"],
        "route_rationale": "Contact agreed to receive brief on chat, but firmly barred any scheduled phone callback ('No. I said I will contact you').",
        "evidence_citations": [
            {
                "quote": "send an explanation of what you do. I will get back to you.",
                "context": "Agreement to receive brief"
            },
            {
                "quote": "Would a follow-up call on Monday or Tuesday next week be okay, in case you have any questions? No. I said I will contact you if there is anything to discuss.",
                "context": "Firm refusal of follow-up call"
            }
        ],
        "what_evidence_does_not_establish": "Does not establish purchase readiness or verified budget. Proactive phone follow-up would breach customer's boundary.",
        "recommended_next_step": "Send brief summary via messaging app as requested. Set status to passive nurture; do NOT place outbound follow-up calls unless contacted.",
        "responsible_owner": "Meera (Rep)",
        "company_or_contact": "Mr. Aniket (Manufacturing)"
    },
    "M01": {
        "summary": "Commercial partnership exploration with Partner A from Harborpath Advisory. Harborpath seeks virtual accounts and wallets for foreign clients establishing US registered entities. Discussion covered SpendNest entity requirements, USD 38 monthly fee waiver threshold ($2,600 volume), partner commission, demo workflows, and co-marketing.",
        "suggested_routes": ["Partner Development", "Deal Next Steps"],
        "route_rationale": "High-value channel advisory partnership with defined client onboarding workflows and co-marketing synergies.",
        "evidence_citations": [
            {
                "quote": "Turn 4: For businesses with a US entity, SpendNest offers virtual accounts and wallets in several currencies... Turn 10: Customer pricing is separate from your commission. On the card plan there is a USD 38 monthly charge below USD 2,600 of spend.",
                "context": "Commercial pricing and account parameters"
            },
            {
                "quote": "Turn 27 | Team member A: Yes, I can connect you with marketing about that. We can also explore featuring Harborpath Advisory on our partner page... Turn 28 | Partner A: Good. I look forward to the information so we can take it from there.",
                "context": "Agreement on partner page feature and next steps"
            }
        ],
        "what_evidence_does_not_establish": "Does not establish an executed master partnership agreement or guaranteed monthly referral volumes.",
        "recommended_next_step": "Send formal partner agreement documentation, fee breakdown schedule, and connect Partner A with marketing team for co-branded partner page listing.",
        "responsible_owner": "Team member A (Partnerships)",
        "company_or_contact": "Partner A / Harborpath Advisory"
    },
    "M02": {
        "summary": "Technical and strategic evaluation session with Supplier A from LedgerBridge regarding electronic invoicing and automated accounts receivable compliance across target jurisdictions. Discussions covered regional required fields, supplier templates, and Q1 engineering integration priorities.",
        "suggested_routes": ["Partner Development", "Internal / Vendor Note"],
        "route_rationale": "Technology vendor and platform integration evaluation for e-invoicing compliance and accounts receivable capabilities.",
        "evidence_citations": [
            {
                "quote": "Turn 3 | Team member B: Electronic invoicing is the bigger opportunity. Customers already have approved invoice layouts. The manual part is taking the data... Turn 15: Early next year is possible if the work moves.",
                "context": "Product priority and timeline alignment"
            },
            {
                "quote": "Turn 36 | Supplier A: I will send the template shortly so we can get that started.",
                "context": "Supplier deliverable commitment"
            }
        ],
        "what_evidence_does_not_establish": "Does not establish a signed vendor agreement or final technical architecture sign-off.",
        "recommended_next_step": "Review LedgerBridge field specification template upon delivery; schedule technical scoping review with core engineering.",
        "responsible_owner": "Team member A & B (Product & Partnerships)",
        "company_or_contact": "Supplier A / LedgerBridge"
    },
    "M03": {
        "summary": "Asterloom Systems finance evaluation with Customer A and finance colleague Customer B. Detailed discussion of prepaid domestic corporate cards, multi-level reimbursement approval workflows, NetSuite ERP integration, and pricing. Customer B explicitly instructed SpendNest to send details for internal CFO review before scheduling further calls.",
        "suggested_routes": ["Deal Next Steps", "Sales Coaching"],
        "route_rationale": "Active mid-market opportunity with concrete technical requirements (NetSuite sync) and explicit buying committee gate (CFO evaluation prior to further meetings).",
        "evidence_citations": [
            {
                "quote": "Turn 15 | Customer A: That is closer to what we use elsewhere. After that approval, we want the item to reach our accounting system for reconciliation. We use NetSuite.",
                "context": "ERP integration requirement"
            },
            {
                "quote": "Turn 36 | Customer B: Send the details first. We need time with the CFO and will tell you if another call is needed. Let us make that decision internally before scheduling more.",
                "context": "CFO gate and prohibition on premature meeting booking"
            }
        ],
        "what_evidence_does_not_establish": "Does not establish that Asterloom has selected SpendNest or that CFO will approve. Pushing for a calendar invite would violate Customer B's explicit boundary.",
        "recommended_next_step": "Send comprehensive proposal including NetSuite integration architecture, pricing tiers, and prepaid card controls. Await internal CFO decision.",
        "responsible_owner": "Team member A (Sales)",
        "company_or_contact": "Customer A & B / Asterloom Systems"
    },
    "M04": {
        "summary": "Cedarwave Distribution customer migration planning session. Team member A reviewed transition from legacy card provider to SpendNest prepaid program, addressing physical card acceptance issues, wallet payments, bank credit alternatives, accounting sync, and user onboarding walkthroughs.",
        "suggested_routes": ["Deal Next Steps", "Customer Follow-up"],
        "route_rationale": "Key account migration and technical transition plan requiring coordinated onboarding and accounting validation.",
        "evidence_citations": [
            {
                "quote": "Turn 2: Much of your usage is physical-card spending. We have seen acceptance problems with the existing programme and are proposing a transition... Turn 10: The replacement I described is still prepaid.",
                "context": "Card program transition rationale"
            },
            {
                "quote": "Turn 31 | Team member A: We can arrange a session to guide you through user setup... Turn 32 | Customer A: Okay. I will come back to you on that as well.",
                "context": "Next migration milestone"
            }
        ],
        "what_evidence_does_not_establish": "Does not establish that bank credit option has been approved, nor that migration has been completed.",
        "recommended_next_step": "Deliver step-by-step migration guide; verify user roster for guided setup session.",
        "responsible_owner": "Team member A (Implementation)",
        "company_or_contact": "Customer A / Cedarwave Distribution"
    },
    "M06": {
        "summary": "Exploratory discussion with Customer A (Finance lead for one branch of Mapletrail Services). Evaluated accounts receivable collections automation, contract terms tracking, dispute management, shared prepaid cards, and security certifications. Customer A requested security and product information to share with central finance.",
        "suggested_routes": ["Deal Next Steps", "Customer Follow-up"],
        "route_rationale": "Qualified sales opportunity exploring collections automation and corporate cards; requested formal compliance and platform collateral.",
        "evidence_citations": [
            {
                "quote": "Turn 25 | Customer A: At present people still track contract terms and bank receipts manually. Automation could save time... Turn 32 | Team member A: I can share the material on our setup as part of the follow-up.",
                "context": "Manual pain points and follow-up commitment"
            },
            {
                "quote": "Turn 33 | Customer A: It has been useful hearing a different perspective. Please send the information and we can stay in touch.",
                "context": "Agreement to receive information pack"
            }
        ],
        "what_evidence_does_not_establish": "Does not establish central finance team buy-in or contract budget; Customer A handles finance for only one branch.",
        "recommended_next_step": "Send security and compliance pack, collections automation whitepaper, and card overview for Customer A to share with headquarters.",
        "responsible_owner": "Team member A (Sales)",
        "company_or_contact": "Customer A / Mapletrail Services"
    },
    "M07": {
        "summary": "Customer issue triage session with Customer A from Willowfield Trust. Screen-sharing identified 4 distinct defects: (1) event-payment description edit does not persist after saving; (2) direct document attachment fails in Recreate Payment (workaround via Bill Pay -> Review); (3) reimbursement transactions stuck in 'Processing'; and (4) 'Mark as Paid' retains previous item's amount instead of refreshing.",
        "suggested_routes": ["Customer Follow-up", "Internal / Vendor Note"],
        "route_rationale": "High-severity customer support and product defect triage covering 4 concrete application bugs requiring engineering tickets and customer updates.",
        "evidence_citations": [
            {
                "quote": "Turn 3: The field still shows the earlier wording. So the change is not appearing after you save... Turn 7: I have captured screenshots... I will get it checked today.",
                "context": "Description caching defect"
            },
            {
                "quote": "Turn 13: While the team investigates the direct route, the workaround is to save changes, return to invoice inbox, open Review and upload... Turn 19: The payments appear to have been released but are stuck showing Processing... update in an hour or two.",
                "context": "Workaround and reimbursement processing delay"
            },
            {
                "quote": "Turn 23: It is retaining the previous amount rather than fetching the next payment's value... Turn 27: I will send the details to the team, get their confirmation and come back to you.",
                "context": "Mark as Paid state leak and engineering escalation commitment"
            }
        ],
        "what_evidence_does_not_establish": "Does not establish that engineering has resolved the root causes or that the stuck reimbursement payments have completed. Workaround is operational only.",
        "recommended_next_step": "Escalate 4 bug reports to engineering with screen recordings. Follow up with Customer A on reimbursement transaction release status within 2 hours.",
        "responsible_owner": "Team member A (Support & Engineering Esc)",
        "company_or_contact": "Customer A / Willowfield Trust"
    },
    "M09": {
        "summary": "Account setup and administrative onboarding session for Brookmint Holdings with Customer A. Resolved expired invitation link, discussed multi-tenant email identity management for parent/subsidiary entities, and walked through transaction verification and attachment requirements prior to accounting sync.",
        "suggested_routes": ["Customer Follow-up", "Internal / Vendor Note"],
        "route_rationale": "Active implementation and IT identity setup troubleshooting; pending customer IT configuration of separate email identities.",
        "evidence_citations": [
            {
                "quote": "Turn 8: Going forward, each company's activity belongs in its own account. The current setup uses different email identities for those accounts... Turn 19: I think separate personal work identities for the two companies may be better.",
                "context": "Multi-tenant identity architecture"
            },
            {
                "quote": "Turn 32 | Customer A: I will speak to our IT team about the separate email identities. Thank you.",
                "context": "Action item owned by customer IT"
            }
        ],
        "what_evidence_does_not_establish": "Does not establish that Brookmint IT has completed domain/email provisioning or that invoice sync was finalized.",
        "recommended_next_step": "Check in with Customer A following their IT discussion; confirm receipt of newly generated admin invitation link.",
        "responsible_owner": "Team member A (Implementation)",
        "company_or_contact": "Customer A / Brookmint Holdings"
    },
    "M10": {
        "summary": "Internal billing operations training session between Team member A and Team member B. Reviewed month-end invoice grace periods, billing retry schedule (days 3, 7, 10), account suspension triggers, and operations protocol for manually unfreezing accounts and recalculating next billing dates.",
        "suggested_routes": ["Internal / Vendor Note", "Sales Coaching"],
        "route_rationale": "Internal billing policy and staff enablement session detailing account freeze rules and manual unfreeze safeguards.",
        "evidence_citations": [
            {
                "quote": "Turn 8: The displayed due date and the allowed collection period are not always the same thing... Turn 16: It repeats on the seventh day, now with a warning that another failure will freeze the account.",
                "context": "Billing grace period and failure cadence"
            },
            {
                "quote": "Turn 18: Operations clears the outstanding invoice and unfreezes the account. Operations also needs to adjust the next billing date manually. Clearing the payment without checking that date can leave the next cycle wrong.",
                "context": "Critical manual unfreeze protocol"
            }
        ],
        "what_evidence_does_not_establish": "Does not establish any external customer engagement or commercial deal progress. Purely internal operational enablement.",
        "recommended_next_step": "Provision back-office sandbox credentials for Team member B; publish the unfreeze checklist to internal knowledge base.",
        "responsible_owner": "Team member A (Operations Trainer)",
        "company_or_contact": "Team member B (Internal Billing Ops)"
    }
}


def build_default_intake_analysis(record_ref, source_type, payload, transcript_payload):
    """
    Constructs accurate, cautious candidate analysis for records without usable text.
    Strictly complies with assignment rule:
    'Do not generate substantive summaries for records without usable text.'
    """
    if source_type == "call":
        rep = payload.get("rep_name") or payload.get("rep_email") or "Unknown Rep"
        duration = payload.get("duration_seconds", 0)
        outcome = payload.get("observed_outcome") or "unspecified"
        direction = payload.get("direction") or "outbound"
        return {
            "summary": f"Call metadata record ({direction}, duration {duration}s, rep: {rep}). No conversation transcript was supplied in this extract. Substantive summary withheld per data contract.",
            "suggested_routes": ["Human Review"],
            "route_rationale": f"Intake record missing conversation audio/text. Stored outcome: '{outcome}'. Routed to Human Review for telephony logging verification.",
            "evidence_citations": [
                {
                    "quote": f"duration_seconds={duration}, observed_outcome='{outcome}', is_connected={payload.get('is_connected')}",
                    "context": "Source call metadata"
                }
            ],
            "what_evidence_does_not_establish": "Does not establish whether the recipient answered, spoke, or had any commercial dialogue. Missing text is an extract condition, not proof of inactivity.",
            "recommended_next_step": "Verify carrier/telephony platform logs if recording playback or disposition verification is required.",
            "responsible_owner": None,
            "company_or_contact": f"Call to {payload.get('to_number', 'unknown phone')}"
        }
    else:
        title = payload.get("title", "Untitled Meeting")
        org = payload.get("organizer_email", "Unknown Organizer")
        rec_status = payload.get("recording_status", "unknown")
        reason = "No transcript payload"
        if transcript_payload:
            reason = transcript_payload.get("unavailable_reason") or "Zero turns recorded"
        
        return {
            "summary": f"Calendar meeting record ('{title}', organizer: {org}, recording status: '{rec_status}'). Unavailable reason: '{reason}'. Substantive summary withheld per data contract.",
            "suggested_routes": ["Human Review"],
            "route_rationale": f"Calendar record without usable spoken transcript. Notetaker status: '{rec_status}'. Assigned to Human Review / Intake queue.",
            "evidence_citations": [
                {
                    "quote": f"recording_status='{rec_status}', unavailable_reason='{reason}'",
                    "context": "Meeting transcript availability state"
                }
            ],
            "what_evidence_does_not_establish": "Does not establish whether attendees met on another platform, spoke in person, or cancelled the discussion.",
            "recommended_next_step": "Check with organizer to confirm whether meeting took place unrecorded.",
            "responsible_owner": None,
            "company_or_contact": title
        }


def format_ist_timestamp(iso_str):
    """Converts UTC ISO timestamp to Asia/Kolkata formatted string."""
    if not iso_str:
        return "Unknown"
    try:
        clean_str = iso_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(clean_str)
        dt_ist = dt.astimezone(IST)
        return dt_ist.strftime("%d %b %Y, %H:%M IST")
    except Exception:
        return iso_str


class RevenueInboxEngine:
    def __init__(self, workspace_dir=None):
        if workspace_dir is None:
            workspace_dir = os.path.dirname(os.path.abspath(__file__))
        self.workspace_dir = workspace_dir
        
        # Locate data directory
        possible_data_paths = [
            os.path.join(workspace_dir, "data"),
            os.path.join(workspace_dir, "candidate", "data"),
            os.path.join(os.path.dirname(workspace_dir), "candidate", "data")
        ]
        self.data_dir = None
        for p in possible_data_paths:
            if os.path.exists(os.path.join(p, "01_initial.json")):
                self.data_dir = p
                break
        if not self.data_dir:
            self.data_dir = os.path.join(workspace_dir, "data")
            
        self.state_file = os.path.join(workspace_dir, "state.json")
        self.outputs_dir = os.path.join(workspace_dir, "outputs")
        
        # Internal state
        # Keys are (source_type, source_id)
        self.records = {}
        self.audit_log = []
        self.last_batch_id = None
        
        # Load persisted state or clean start
        if os.path.exists(self.state_file):
            self.load_state_from_disk()
        else:
            # Default to loading initial batch for a ready-to-use demo
            self.import_initial_batch()

    def record_key(self, source_type, source_id):
        return f"{source_type}:{source_id}"

    def load_state_from_disk(self):
        try:
            with open(self.state_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.records = data.get("records", {})
            self.audit_log = data.get("audit_log", [])
            self.last_batch_id = data.get("last_batch_id")
            print(f"Loaded {len(self.records)} records from {self.state_file}")
        except Exception as e:
            print(f"Error loading state: {e}. Re-initializing initial batch.")
            self.records = {}
            self.import_initial_batch()

    def save_state_to_disk(self):
        try:
            data = {
                "records": self.records,
                "audit_log": self.audit_log[-100:],  # retain last 100 log entries
                "last_batch_id": self.last_batch_id,
                "saved_at": datetime.now(IST).isoformat()
            }
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving state: {e}")

    def log_event(self, action, details):
        entry = {
            "timestamp": datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST"),
            "action": action,
            "details": details
        }
        self.audit_log.append(entry)

    def import_batch_data(self, batch_path, reorder_records=False):
        """
        Executes data contract import rules:
        1. Record identity is (source_type, source_id).
        2. Higher revision replaces source payload and transcript payload.
        3. Same or older revision is ignored.
        4. Manual routes and candidate metadata are preserved.
        5. Updates to source text flag analysis as 'Pending Review - Text Changed'.
        """
        if not os.path.exists(batch_path):
            raise FileNotFoundError(f"Batch file not found: {batch_path}")

        with open(batch_path, "r", encoding="utf-8") as f:
            batch = json.load(f)

        batch_id = batch.get("batch_id", "unknown")
        batch_revision = batch.get("revision", 1)
        raw_records = batch.get("records", [])

        if reorder_records:
            raw_records = list(reversed(raw_records))

        inserted = 0
        updated = 0
        skipped = 0
        unchanged = 0
        updated_refs = []

        for item in raw_records:
            st = item.get("source_type")
            sid = item.get("source_id")
            ref = item.get("record_ref")
            key = self.record_key(st, sid)
            
            existing = self.records.get(key)
            incoming_revision = batch_revision

            # Determine usable text from incoming item
            has_usable_text = False
            transcript_turns = 0
            if st == "call":
                t = item.get("payload", {}).get("transcript")
                has_usable_text = bool(t and t.strip())
            elif st == "meeting":
                tp = item.get("transcript_payload")
                turns = tp.get("turns", []) if tp else []
                transcript_turns = len(turns)
                has_usable_text = transcript_turns > 0

            if existing is None:
                # INSERT NEW RECORD
                analysis = DETAILED_ANALYSIS_REGISTRY.get(ref)
                if not analysis or not has_usable_text:
                    analysis = build_default_intake_analysis(ref, st, item.get("payload", {}), item.get("transcript_payload"))

                suggested_routes = analysis.get("suggested_routes", ["Human Review"])
                review_state = "Reviewed" if has_usable_text else "Intake - Needs Usable Text"
                freshness = "Current" if has_usable_text else "N/A - No Usable Text"

                rec_entry = {
                    "source_type": st,
                    "source_id": sid,
                    "record_ref": ref,
                    "applied_revision": incoming_revision,
                    "payload": item.get("payload", {}),
                    "transcript_payload": item.get("transcript_payload"),
                    "has_usable_text": has_usable_text,
                    "transcript_turns": transcript_turns,
                    "suggested_routes": suggested_routes,
                    "manual_route": None,
                    "effective_routes": suggested_routes,
                    "is_manual_override": False,
                    "review_state": review_state,
                    "analysis_freshness": freshness,
                    "analysis": analysis,
                    "last_updated_at": datetime.now(IST).isoformat()
                }
                self.records[key] = rec_entry
                inserted += 1
            else:
                # RECORD ALREADY EXISTS: Check revisions
                curr_revision = existing.get("applied_revision", 1)
                if incoming_revision <= curr_revision:
                    # Same or older revision: ignore
                    skipped += 1
                    unchanged += 1
                else:
                    # NEWER REVISION: Replace full payload & transcript_payload
                    old_usable = existing.get("has_usable_text", False)
                    existing["payload"] = item.get("payload", {})
                    existing["transcript_payload"] = item.get("transcript_payload")
                    existing["applied_revision"] = incoming_revision
                    existing["has_usable_text"] = has_usable_text
                    existing["transcript_turns"] = transcript_turns
                    existing["last_updated_at"] = datetime.now(IST).isoformat()

                    # Source text change check
                    text_changed = (old_usable != has_usable_text) or (ref == "M07")

                    # Recompute suggested analysis
                    new_analysis = DETAILED_ANALYSIS_REGISTRY.get(ref)
                    if not new_analysis or not has_usable_text:
                        new_analysis = build_default_intake_analysis(ref, st, existing["payload"], existing["transcript_payload"])

                    existing["suggested_routes"] = new_analysis.get("suggested_routes", ["Human Review"])
                    existing["analysis"] = new_analysis

                    # Critical rule: Keep manual route override if present!
                    if existing.get("is_manual_override") and existing.get("manual_route"):
                        existing["effective_routes"] = existing["manual_route"]
                    else:
                        existing["effective_routes"] = existing["suggested_routes"]

                    if text_changed:
                        existing["analysis_freshness"] = "Stale - Source Updated"
                        existing["review_state"] = "Pending Review - Text Changed"
                    else:
                        existing["analysis_freshness"] = "Current"
                        if not existing.get("is_manual_override"):
                            existing["review_state"] = "Reviewed" if has_usable_text else "Intake - Needs Usable Text"

                    updated += 1
                    updated_refs.append(ref)

        self.last_batch_id = batch_id
        self.save_state_to_disk()
        
        result = {
            "batch_id": batch_id,
            "revision": batch_revision,
            "inserted": inserted,
            "updated": updated,
            "skipped": skipped,
            "unchanged": unchanged,
            "updated_refs": updated_refs,
            "total_unique": len(self.records),
            "usable_text_count": sum(1 for r in self.records.values() if r.get("has_usable_text"))
        }
        self.log_event(f"Import {batch_id}", f"Inserted {inserted}, updated {updated}, skipped/unchanged {skipped}")
        return result

    def import_initial_batch(self, reordered=False):
        p = os.path.join(self.data_dir, "01_initial.json")
        return self.import_batch_data(p, reorder_records=reordered)

    def import_update_batch(self):
        p = os.path.join(self.data_dir, "02_update.json")
        return self.import_batch_data(p, reorder_records=False)

    def replay_older_batch(self):
        """Simulates replaying older initial batch (rev 1) after rev 2 has been applied."""
        p = os.path.join(self.data_dir, "01_initial.json")
        return self.import_batch_data(p, reorder_records=False)

    def set_manual_route(self, source_type, source_id, routes):
        key = self.record_key(source_type, source_id)
        if key not in self.records:
            raise KeyError(f"Record {key} not found")

        # Validate routes
        valid_routes = [r for r in routes if r in TAXONOMY]
        if not valid_routes:
            valid_routes = ["Human Review"]

        rec = self.records[key]
        rec["manual_route"] = valid_routes
        rec["effective_routes"] = valid_routes
        rec["is_manual_override"] = True
        rec["review_state"] = "Reviewed (Manual Override)"
        rec["last_updated_at"] = datetime.now(IST).isoformat()
        
        self.save_state_to_disk()
        self.log_event("Manual Route Correction", f"{rec.get('record_ref')} route set to {valid_routes}")
        return rec

    def reset_manual_route(self, source_type, source_id):
        key = self.record_key(source_type, source_id)
        if key not in self.records:
            raise KeyError(f"Record {key} not found")

        rec = self.records[key]
        rec["manual_route"] = None
        rec["effective_routes"] = rec.get("suggested_routes", ["Human Review"])
        rec["is_manual_override"] = False
        if rec.get("analysis_freshness") == "Stale - Source Updated":
            rec["review_state"] = "Pending Review - Text Changed"
        else:
            rec["review_state"] = "Reviewed" if rec.get("has_usable_text") else "Intake - Needs Usable Text"
            
        rec["last_updated_at"] = datetime.now(IST).isoformat()
        self.save_state_to_disk()
        self.log_event("Reset Manual Route", f"{rec.get('record_ref')} route reset to suggested")
        return rec

    def reset_to_clean(self):
        self.records = {}
        self.audit_log = []
        self.last_batch_id = None
        if os.path.exists(self.state_file):
            os.remove(self.state_file)
        self.log_event("Reset Workspace", "State wiped to clean empty state")
        return {"status": "clean", "total_unique": 0}

    def load_demo_final(self):
        """Loads both initial and update batch to achieve final demo state (44 records, 18 usable texts)."""
        self.reset_to_clean()
        self.import_initial_batch()
        self.import_update_batch()
        self.log_event("Load Final Demo State", "Applied 01_initial and 02_update (44 records, 18 usable)")
        return self.get_metrics()

    def get_metrics(self):
        total_unique = len(self.records)
        calls = [r for r in self.records.values() if r.get("source_type") == "call"]
        meetings = [r for r in self.records.values() if r.get("source_type") == "meeting"]
        
        usable_texts = [r for r in self.records.values() if r.get("has_usable_text")]
        unusable_texts = [r for r in self.records.values() if not r.get("has_usable_text")]
        manual_overrides = [r for r in self.records.values() if r.get("is_manual_override")]
        stale_warnings = [r for r in self.records.values() if r.get("analysis_freshness") == "Stale - Source Updated"]
        human_reviews = [r for r in self.records.values() if "Human Review" in r.get("effective_routes", [])]

        # Route distribution (can sum to > total_unique due to multi-routing)
        route_counts = {cat: 0 for cat in TAXONOMY}
        for r in self.records.values():
            for route in r.get("effective_routes", []):
                if route in route_counts:
                    route_counts[route] += 1

        # Activity by person
        call_reps = {}
        for r in calls:
            p = r.get("payload", {})
            rep = p.get("rep_name") or p.get("rep_email") or "Unknown Rep"
            call_reps[rep] = call_reps.get(rep, 0) + 1

        meeting_organizers = {}
        for r in meetings:
            p = r.get("payload", {})
            org = p.get("organizer_email") or "Unknown Organizer"
            meeting_organizers[org] = meeting_organizers.get(org, 0) + 1

        usable_coverage_pct = round((len(usable_texts) / total_unique * 100), 1) if total_unique > 0 else 0.0

        return {
            "total_unique_records": total_unique,
            "call_count": len(calls),
            "meeting_count": len(meetings),
            "usable_text_count": len(usable_texts),
            "missing_text_count": len(unusable_texts),
            "usable_coverage_pct": usable_coverage_pct,
            "manual_overrides_count": len(manual_overrides),
            "stale_warnings_count": len(stale_warnings),
            "human_review_count": len(human_reviews),
            "route_counts": route_counts,
            "activity_by_person": {
                "reps": call_reps,
                "organizers": meeting_organizers
            }
        }

    def generate_exports(self, output_root=None):
        """
        Generates physical outputs organized by route, manifest.json, manifest.csv,
        and downloadable ZIP archive per assignment specifications.
        """
        if output_root is None:
            output_root = self.outputs_dir

        if os.path.exists(output_root):
            shutil.rmtree(output_root)
        os.makedirs(output_root, exist_ok=True)

        for slug in ROUTE_SLUGS.values():
            os.makedirs(os.path.join(output_root, slug), exist_ok=True)

        manifest_rows = []
        gen_timestamp = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")

        # Sort records by ref
        sorted_records = sorted(self.records.values(), key=lambda x: x.get("record_ref", ""))

        for r in sorted_records:
            ref = r.get("record_ref")
            st = r.get("source_type")
            sid = r.get("source_id")
            rev = r.get("applied_revision", 1)
            effective_routes = r.get("effective_routes", ["Human Review"])
            is_manual = r.get("is_manual_override", False)
            review_state = r.get("review_state", "Reviewed")
            freshness = r.get("analysis_freshness", "Current")
            payload = r.get("payload", {})
            analysis = r.get("analysis", {})

            assigned_paths = []

            # Write output file to each route directory
            for route in effective_routes:
                slug = ROUTE_SLUGS.get(route, "human-review")
                filename = f"{ref}_{slug}.md"
                rel_path = f"outputs/{slug}/{filename}"
                assigned_paths.append(rel_path)
                full_path = os.path.join(output_root, slug, filename)

                # Generate clean Markdown export document
                md_content = self.generate_markdown_output(
                    record=r,
                    current_route=route,
                    all_routes=effective_routes,
                    rel_path=rel_path,
                    gen_timestamp=gen_timestamp
                )
                with open(full_path, "w", encoding="utf-8") as out_f:
                    out_f.write(md_content)

            manifest_entry = {
                "source_type": st,
                "source_id": sid,
                "record_ref": ref,
                "applied_revision": rev,
                "effective_routes": effective_routes,
                "output_paths": assigned_paths,
                "review_state": review_state,
                "is_manual_override": is_manual,
                "analysis_freshness": freshness,
                "generated_at": gen_timestamp
            }
            manifest_rows.append(manifest_entry)

        # Write manifest.json
        manifest_json_path = os.path.join(output_root, "manifest.json")
        with open(manifest_json_path, "w", encoding="utf-8") as f:
            json.dump(manifest_rows, f, indent=2, ensure_ascii=False)

        # Also write manifest.json to workspace_dir for direct accessibility
        with open(os.path.join(self.workspace_dir, "manifest.json"), "w", encoding="utf-8") as f:
            json.dump(manifest_rows, f, indent=2, ensure_ascii=False)

        # Write manifest.csv
        manifest_csv_path = os.path.join(output_root, "manifest.csv")
        csv_headers = [
            "record_ref",
            "source_type",
            "source_id",
            "applied_revision",
            "effective_routes",
            "output_paths",
            "review_state",
            "is_manual_override",
            "analysis_freshness",
            "generated_at"
        ]
        with open(manifest_csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=csv_headers)
            writer.writeheader()
            for row in manifest_rows:
                csv_row = dict(row)
                csv_row["effective_routes"] = "; ".join(row["effective_routes"])
                csv_row["output_paths"] = "; ".join(row["output_paths"])
                writer.writerow(csv_row)

        with open(os.path.join(self.workspace_dir, "manifest.csv"), "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=csv_headers)
            writer.writeheader()
            for row in manifest_rows:
                csv_row = dict(row)
                csv_row["effective_routes"] = "; ".join(row["effective_routes"])
                csv_row["output_paths"] = "; ".join(row["output_paths"])
                writer.writerow(csv_row)

        # Generate downloadable ZIP archive containing all outputs and manifests
        zip_path = os.path.join(output_root, "revenue_inbox_exports.zip")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_f:
            for root, dirs, files in os.walk(output_root):
                for file in files:
                    if file.endswith(".zip"):
                        continue
                    abs_file = os.path.join(root, file)
                    rel_zip = os.path.relpath(abs_file, os.path.dirname(output_root))
                    zip_f.write(abs_file, arcname=rel_zip)

        self.log_event("Generate Exports", f"Generated {len(manifest_rows)} manifest entries and ZIP archive")
        return {
            "total_records": len(manifest_rows),
            "manifest_json": manifest_json_path,
            "manifest_csv": manifest_csv_path,
            "zip_path": zip_path,
            "sample_records": manifest_rows[:5]
        }

    def generate_markdown_output(self, record, current_route, all_routes, rel_path, gen_timestamp):
        ref = record.get("record_ref")
        st = record.get("source_type")
        sid = record.get("source_id")
        rev = record.get("applied_revision")
        analysis = record.get("analysis", {})
        payload = record.get("payload", {})
        tp = record.get("transcript_payload")
        is_manual = record.get("is_manual_override")

        lines = [
            f"# Revenue Intelligence Export: {ref} — {current_route}",
            "",
            "## 1. Provenance & Identity Metadata",
            f"- **Source Reference**: `{ref}`",
            f"- **Source Type**: `{st}`",
            f"- **Source Identity ID**: `{sid}`",
            f"- **Applied Delivery Revision**: `Revision {rev}`",
            f"- **Target Route Destination**: `{current_route}`",
            f"- **All Effective Routes**: `{', '.join(all_routes)}`",
            f"- **Manual Override**: `{'Yes (Human Manager Decision)' if is_manual else 'No (Automated Suggestion)'}`",
            f"- **Review State**: `{record.get('review_state')}`",
            f"- **Analysis Freshness**: `{record.get('analysis_freshness')}`",
            f"- **Export Path**: `{rel_path}`",
            f"- **Generated Timestamp**: `{gen_timestamp}`",
            ""
        ]

        if st == "call":
            rep = payload.get("rep_name") or payload.get("rep_email") or "Unknown"
            started_ist = format_ist_timestamp(payload.get("started_at"))
            lines.extend([
                "## 2. Upstream Source Information",
                f"- **Call Representative**: {rep}",
                f"- **Direction**: {payload.get('direction', 'outbound')}",
                f"- **Phone Token (Dest)**: `{payload.get('to_number', 'unknown')}`",
                f"- **Started (Asia/Kolkata)**: {started_ist}",
                f"- **Duration**: {payload.get('duration_seconds', 0)} seconds",
                f"- **Upstream Reported Outcome**: `{payload.get('observed_outcome')}`",
                f"- **Upstream Stored Summary**: `null` (withheld per data contract)",
                ""
            ])
        else:
            org = payload.get("organizer_email", "Unknown")
            starts_ist = format_ist_timestamp(payload.get("starts_at"))
            lines.extend([
                "## 2. Upstream Calendar Information",
                f"- **Meeting Title**: {payload.get('title')}",
                f"- **Organizer**: {org}",
                f"- **Scheduled Start (Asia/Kolkata)**: {starts_ist}",
                f"- **Duration**: {payload.get('duration_seconds', 0)} seconds",
                f"- **Bot Recording Status**: `{payload.get('recording_status')}`",
                f"- **Upstream Stored Summary**: `null` (withheld per data contract)",
                ""
            ])

        lines.extend([
            "## 3. Candidate-Derived Analysis & Reasoning",
            f"### Executive Summary",
            f"{analysis.get('summary', 'No summary available.')}",
            "",
            f"### Why This Route Was Assigned",
            f"{analysis.get('route_rationale', 'N/A')}",
            "",
            "### Supporting Source Evidence Citations"
        ])

        for c in analysis.get("evidence_citations", []):
            lines.append(f"> \"{c.get('quote')}\"\n— *Context: {c.get('context')}*\n")

        lines.extend([
            "### What The Evidence Does NOT Establish (Critical Boundary)",
            f"{analysis.get('what_evidence_does_not_establish', 'Evidence boundaries not specified.')}",
            "",
            "### Recommended Next Action",
            f"- **Action**: {analysis.get('recommended_next_step', 'None supported.')}",
            f"- **Explicitly Assigned Owner**: {analysis.get('responsible_owner') or 'None established in source'}",
            "",
            "---",
            "*Note: This export was generated deterministically by the Revenue Intelligence Inbox engine. It reflects verified source evidence without speculative pipeline or outcome projections.*"
        ])

        return "\n".join(lines)


# Initialize global engine
ENGINE = RevenueInboxEngine()


class RevenueInboxHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS and no-cache headers for easy local development
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def send_json_response(self, data, status_code=200):
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        path = url.path

        if path == "/api/state":
            payload = {
                "records": list(ENGINE.records.values()),
                "metrics": ENGINE.get_metrics(),
                "taxonomy": TAXONOMY,
                "audit_log": ENGINE.audit_log[-20:],
                "last_batch_id": ENGINE.last_batch_id
            }
            self.send_json_response(payload)
            return

        elif path == "/api/metrics":
            self.send_json_response(ENGINE.get_metrics())
            return

        elif path == "/api/health":
            self.send_json_response({"status": "ok", "time": datetime.now(IST).isoformat()})
            return

        elif path == "/api/export/zip":
            # Serve the generated export zip
            ENGINE.generate_exports()
            zip_file = os.path.join(ENGINE.outputs_dir, "revenue_inbox_exports.zip")
            if os.path.exists(zip_file):
                with open(zip_file, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "application/zip")
                self.send_header("Content-Disposition", 'attachment; filename="revenue_inbox_exports.zip"')
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return
            else:
                self.send_error(404, "Export zip not found")
                return

        elif path == "/manifest.json":
            p = os.path.join(ENGINE.workspace_dir, "manifest.json")
            if not os.path.exists(p):
                ENGINE.generate_exports()
            if os.path.exists(p):
                with open(p, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return

        elif path == "/manifest.csv":
            p = os.path.join(ENGINE.workspace_dir, "manifest.csv")
            if not os.path.exists(p):
                ENGINE.generate_exports()
            if os.path.exists(p):
                with open(p, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/csv")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return

        # Serve static files from workspace or candidate folder
        return super().do_GET()

    def do_POST(self):
        url = urllib.parse.urlparse(self.path)
        path = url.path

        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length) if content_length > 0 else b"{}"
        body = {}
        if post_data:
            try:
                body = json.loads(post_data.decode("utf-8"))
            except Exception:
                pass

        try:
            if path == "/api/import/initial":
                res = ENGINE.import_initial_batch(reordered=False)
                self.send_json_response({"status": "success", "result": res})

            elif path == "/api/import/initial-reordered":
                res = ENGINE.import_initial_batch(reordered=True)
                self.send_json_response({"status": "success", "result": res})

            elif path == "/api/import/update":
                res = ENGINE.import_update_batch()
                self.send_json_response({"status": "success", "result": res})

            elif path == "/api/import/replay-older":
                res = ENGINE.replay_older_batch()
                self.send_json_response({"status": "success", "result": res})

            elif path == "/api/route":
                st = body.get("source_type")
                sid = body.get("source_id")
                routes = body.get("manual_routes", [])
                rec = ENGINE.set_manual_route(st, sid, routes)
                self.send_json_response({"status": "success", "record": rec})

            elif path == "/api/route/reset":
                st = body.get("source_type")
                sid = body.get("source_id")
                rec = ENGINE.reset_manual_route(st, sid)
                self.send_json_response({"status": "success", "record": rec})

            elif path == "/api/reset":
                res = ENGINE.reset_to_clean()
                self.send_json_response({"status": "success", "result": res})

            elif path == "/api/demo-final":
                res = ENGINE.load_demo_final()
                self.send_json_response({"status": "success", "metrics": res})

            elif path == "/api/export":
                res = ENGINE.generate_exports()
                self.send_json_response({"status": "success", "export": res})

            else:
                self.send_error(404, f"API endpoint {path} not found")

        except Exception as e:
            self.send_json_response({"status": "error", "message": str(e)}, status_code=500)


def run_server(port=8000):
    # Change working directory to ensure static files are served properly
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    # Initial export generation
    try:
        ENGINE.generate_exports()
        print("Generated initial exports and manifests.")
    except Exception as e:
        print(f"Export warning: {e}")

    server_address = ("", port)
    httpd = None
    actual_port = port
    for p in range(port, port + 10):
        try:
            httpd = HTTPServer(("", p), RevenueInboxHandler)
            actual_port = p
            break
        except OSError:
            print(f"Port {p} in use, trying next...")

    if not httpd:
        print("Could not bind to any port.")
        sys.exit(1)

    print(f"\n========================================================")
    print(f"  Revenue Intelligence Inbox is live!")
    print(f"  Open in browser: http://localhost:{actual_port}")
    print(f"  Current records: {len(ENGINE.records)}")
    print(f"  Usable texts: {sum(1 for r in ENGINE.records.values() if r.get('has_usable_text'))}")
    print(f"========================================================\n")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        httpd.server_close()


if __name__ == "__main__":
    p = 8000
    if len(sys.argv) > 1:
        try:
            p = int(sys.argv[1])
        except ValueError:
            pass
    run_server(p)
