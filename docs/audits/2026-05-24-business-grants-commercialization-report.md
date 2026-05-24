# CareSight Business, Grants, and Commercialization Report

Date: 2026-05-24

Scope: funding, business model, grant paths, and commercialization strategy for CareSight as a local-first caregiver awareness product.

Instruction boundary: this report is strategic and informational. It is not legal, medical, regulatory, accounting, or fundraising advice.

## Executive Summary

CareSight has a credible wedge because it combines several trends:

- Aging-in-place pressure.
- Family caregiver burden.
- Privacy concerns around cloud cameras.
- Apple Silicon local AI capability.
- Open-source trust and auditability.
- A bounded human-review loop instead of autonomous medical/emergency claims.

The strongest early business path is not "AI fall detector" and not "HIPAA-compliant facility platform." The strongest early path is:

> A local-first caregiver awareness appliance that creates auditable possible-event records and helps authorized humans coordinate care.

The best funding strategy is staged:

1. Use open-source/public-good grants for privacy-preserving local AI infrastructure.
2. Use AgeTech accelerators for customer discovery and partnerships.
3. Use NSF SBIR/STTR for deep-tech commercialization once the evaluation plan is strong.
4. Use NIH/NIA SBIR/STTR only if the product is framed around aging/caregiver outcomes with a credible study design.
5. Use paid pilots and service revenue before raising significant venture capital.

## Product Positioning

### Recommended Position

CareSight is a local-first caregiver awareness and review system.

It helps families and care teams:

- See possible care events.
- Preserve local evidence.
- Review and acknowledge events.
- Create care journals.
- Draft caregiver updates.
- Coordinate handoffs.

### Avoided Position

Do not position CareSight as:

- A medical device.
- A certified fall detector.
- HIPAA-compliant by default.
- Autonomous emergency dispatch.
- Medication-administration confirmation.
- Cloud surveillance.
- Biometric identity recognition.

### Buyer Personas

Primary early buyer:

- Adult child caring for an aging parent.
- Wants awareness without cloud surveillance.
- Will pay for setup and support if trustworthy.

Secondary early buyer:

- Family caregiver managing rotating helpers.
- Needs journal, alerts, and handoff continuity.

Later buyer:

- Small home-care agency.
- Wants local event records and shift summaries.

Future buyer:

- Assisted-living or care facility.
- Requires security, compliance, deployment, support, and legal review.

## Business Model Options

### Model A - Open-Source Core + Paid Support

Shape:

- AGPL community repo.
- Paid setup, support, updates, compatible hardware list, and hosted documentation.

Pros:

- Aligns with current AGPL posture.
- Builds trust.
- Good for grants.
- Avoids hiding core safety logic.

Cons:

- Support burden can grow quickly.
- Hardware/camera variability is expensive.
- Investors may ask about defensibility.

Recommended use:

- Best immediate path.

### Model B - Local Appliance Kit

Shape:

- Mac mini or approved Apple Silicon hub.
- Supported cameras.
- Local dashboard.
- Setup wizard.
- Optional support subscription.

Pros:

- Clear product.
- Easier customer experience.
- Revenue can start earlier.
- Supportable configuration matrix.

Cons:

- Hardware inventory risk.
- Installation complexity.
- Margin pressure.

Recommended use:

- Best first paid pilot product.

### Model C - Managed Local Appliance Subscription

Shape:

- Upfront hardware/install fee.
- Monthly support/update/monitoring subscription.
- Raw media stays local by default.

Pros:

- Recurring revenue.
- Funds ongoing support.
- Works for families and home-care agencies.

Cons:

- Must be careful with remote access and privacy.
- Higher compliance burden.

Recommended use:

- Strong after pilot validation.

### Model D - Home-Care Agency Workflow

Shape:

- Agency deploys CareSight in client homes.
- Agency uses review dashboard and shift summaries.

Pros:

- Higher willingness to pay.
- Clear operational value.
- Repeatable channel.

Cons:

- More legal/compliance review.
- Potential HIPAA/business-associate obligations.
- Requires robust admin/RBAC/audit.

Recommended use:

- 6-12 month target, not first sale.

### Model E - Facility Platform

Shape:

- Multi-room local deployment for assisted living/care homes.

Pros:

- Large budgets and urgent need.

Cons:

- Hardest compliance and liability path.
- Requires formal validation, IT/security, support, and facility workflow integration.

Recommended use:

- Future lane only.

## Pricing Hypotheses

These are planning assumptions, not validated pricing.

### Household Pilot Kit

- Hardware: customer-owned Mac or bundled Mac mini.
- Setup fee: $300-$1,500 depending on install complexity.
- Subscription: $20-$99/month for updates/support.
- Premium support: $150-$300/month for high-touch family/caregiver support.

### Home-Care Agency Pilot

- Setup: $1,000-$5,000 per site.
- Subscription: $100-$500/month per active home, depending on support and admin features.
- Professional services: billed separately.

### Facility Pilot

- Setup: $5,000-$25,000.
- Subscription: per room/camera/site.
- Requires legal/security review before pricing seriously.

## Grant and Funding Paths

### NSF SBIR/STTR - America's Seed Fund

Reference: https://seedfund.nsf.gov/

Relevant facts:

- NSF advertises up to $2 million in seed funding and no equity.
- NSF Digital Health covers technologies that improve wellbeing, independence, quality of life, healthcare delivery, assistive technologies, AI in healthcare, and aging/disabled populations.

Fit for CareSight:

- Strong if framed as privacy-preserving local AI for caregiver awareness and aging-in-place support.
- Strong if technical innovation is emphasized: local multimodal care-event engine, auditable privacy-preserving perception, edge AI evaluation, caregiver human-review loop.

Weaknesses:

- NSF expects deep technology and commercial potential.
- A simple app/dashboard alone is not enough.

Recommended NSF proposal theme:

> Privacy-preserving edge AI for auditable caregiver awareness in aging-in-place homes.

Phase I aims:

1. Build model evaluation harness across local vision variants and camera perspectives.
2. Develop privacy-preserving local event evidence store with media policy.
3. Validate caregiver comprehension and false-positive rates in controlled home scenarios.

Milestones:

- Model accuracy/latency benchmark.
- Local dashboard prototype.
- Privacy/security threat model.
- Caregiver usability study.

### NIH / NIA SBIR-STTR

Reference: NIH small business programs and NIA aging/caregiver research pages.

Fit for CareSight:

- Potentially strong if framed around aging, caregiver burden, aging in place, dementia/ADRD support, or home safety awareness.
- NIA is the most relevant NIH institute to explore first.

Weaknesses:

- Requires stronger study design.
- Clinical or health outcome claims increase review burden.
- If the product is positioned as diagnosis/fall detection, regulatory expectations rise.

Recommended NIH/NIA framing:

> A local-first caregiver support tool that improves continuity, review, and handoff documentation for family caregivers of older adults.

Possible specific aims:

1. Measure caregiver comprehension and trust in bounded possible-event records.
2. Measure alert fatigue and false-positive reduction through human-review design.
3. Evaluate whether local-first records improve handoff completeness and response coordination.

Study partners:

- Gerontology researchers.
- Human-computer interaction lab.
- Occupational therapy researchers.
- Caregiver support nonprofits.
- Home-care agency pilot partner.

### AHRQ / Health IT Research

Fit:

- Potential later path for care coordination, safety, workflow, and health IT evaluation.

Weaknesses:

- More likely after a working pilot and partner site.

Recommended use:

- Track but do not prioritize before NSF/NIA discovery.

### ACL / Aging Services Grants

Fit:

- Possible if partnering with aging services organizations.

Weaknesses:

- Often program/service oriented rather than product R&D.

Recommended use:

- Explore through Area Agencies on Aging, caregiver support programs, and state aging innovation programs.

### AARP AgeTech Collaborative

Reference: https://agetechcollaborative.org/startups/

Relevant facts:

- AARP AgeTech Collaborative offers an 8-week virtual accelerator at no cost and no equity.
- It targets startups improving life as people age.

Fit for CareSight:

- Very strong for customer discovery, AgeTech positioning, and partnership feedback.
- Especially useful before writing grant proposals.

Recommended application angle:

> A privacy-preserving local caregiver awareness hub that helps families coordinate help without turning the home into cloud surveillance.

### NLnet

Reference: https://nlnet.nl/funding.html

Relevant facts:

- NLnet supports open software, hardware, data, and standards.
- Grants are listed between 5,000 and 50,000 euro with support services such as security/accessibility audits and mentoring.

Fit for CareSight:

- Strong for open-source privacy/security infrastructure, not for a US caregiver business by itself.

Recommended proposal angle:

> Open local-first care-event audit infrastructure for privacy-preserving home AI.

Potential NLnet deliverables:

- Open media-sharing policy schema.
- Local-only event audit receipts.
- Privacy-preserving edge AI dashboard components.
- Accessibility review for caregiver event records.

### Open Technology Fund

Reference: https://www.opentech.fund/funds/internet-freedom-fund/

Fit:

- Possible only if framed as privacy/security infrastructure for sensitive local video/event data.

Weakness:

- OTF focuses on internet freedom, censorship circumvention, and digital security. CareSight is adjacent, not central.

Recommended use:

- Secondary path only if the privacy-preserving local AI/audit toolkit becomes reusable outside elder care.

### Mozilla Technology Fund / Open Source AI Programs

Reference: Mozilla Foundation open-source AI funding pages.

Fit:

- Potential for open-source local AI tooling, privacy-preserving edge inference, and auditability.

Weakness:

- Calls vary; eligibility and themes change.

Recommended use:

- Track for local AI/open-source infrastructure grants.

### Alzheimer's Association and Dementia Caregiving Grants

Fit:

- Possible if CareSight becomes a research tool for ADRD caregiver support, wandering/off-camera awareness, or handoff documentation.

Weakness:

- Many grants target academic researchers or clinical/translational research.
- Requires careful non-diagnostic framing.

Recommended use:

- Seek research partner first.

## Funding Strategy by Stage

### Stage 1 - 0 to 3 Months

Objective:

- Turn hackathon repo into a pilot-ready prototype.

Funding:

- Personal runway.
- Small open-source grants.
- AARP accelerator.
- GitHub Sponsors/OpenCollective for community support.
- Small angel checks only if terms are friendly.

Outputs:

- Demo release.
- Technical audit.
- Caregiver interviews.
- Prototype dashboard.
- Grant one-pager.

### Stage 2 - 3 to 6 Months

Objective:

- Validate household use and caregiver value.

Funding:

- NSF Project Pitch.
- NLnet proposal.
- AARP/HealthTech accelerator applications.
- Paid pilot deposits.

Outputs:

- Model evaluation report.
- Privacy/security threat model.
- Pilot protocol.
- 3-5 household pilot candidates.
- Advisory circle.

### Stage 3 - 6 to 12 Months

Objective:

- Run pilots and prepare non-dilutive funding.

Funding:

- NSF SBIR Phase I.
- NIH/NIA SBIR/STTR with partner if study design is strong.
- Paid home-care agency pilot.
- Strategic angel.

Outputs:

- Pilot evidence.
- Productized installer.
- Support process.
- Compliance roadmap.
- Commercial package.

### Stage 4 - 12 to 24 Months

Objective:

- Scale from pilot to business.

Funding:

- SBIR Phase II if Phase I succeeds.
- Seed round if customer demand and support economics are proven.
- Revenue from appliance/support.
- Strategic partnerships.

Outputs:

- Production appliance.
- Managed updates.
- Support team.
- HIPAA-ready architecture if facility/provider lane is pursued.
- Security audits.

## Business Formation and Operating Work

### Immediate Business Tasks

1. Choose entity structure.
2. Separate open-source project governance from commercial services.
3. Create a basic cap table.
4. Confirm AGPL/commercial strategy with counsel.
5. Create contributor license or DCO policy if outside contributors arrive.
6. Create privacy policy draft for pilots.
7. Create pilot consent form.
8. Create support disclaimer.
9. Create incident response plan.
10. Create vendor/security inventory.

### Legal Questions for Counsel

1. Does the current product positioning avoid medical-device claims?
2. Which features could trigger FDA device analysis?
3. When does HIPAA apply for direct-to-consumer vs provider/agency/facility sales?
4. What state privacy laws apply to home camera/event data?
5. What consent is needed for household visitors, caregivers, and residents?
6. How should local snapshots and event clips be treated?
7. How should AGPL dependencies affect commercial packaging?
8. What liability disclaimers are appropriate without weakening consumer trust?
9. What insurance is needed before paid pilots?
10. What breach notification obligations apply outside HIPAA?

### Insurance to Explore

- General liability.
- Technology errors and omissions.
- Cyber liability.
- Product liability.
- Professional liability if consulting/installing.

## HIPAA, FDA, and FTC Commercialization Boundary

### HIPAA

HHS guidance says HIPAA applies to covered entities and business associates. CareSight should assume:

- Direct-to-consumer family use may not automatically be HIPAA.
- Selling to covered providers or health plans can create business-associate obligations.
- Providing cloud support, remote monitoring, or maintenance involving PHI can increase obligations.

Practical steps:

1. Do not claim HIPAA compliance now.
2. Build HIPAA-ready controls before provider/facility pilots.
3. Keep raw home video local by default.
4. Prepare BAA templates only after legal review.
5. Use minimum necessary data for support.

### FDA

FDA digital health guidance should be reviewed feature-by-feature. CareSight should avoid claims that:

- It detects falls as a clinical fact.
- It diagnoses injury or health state.
- It recommends treatment.
- It autonomously escalates emergency care.

Practical steps:

1. Keep "possible event" language.
2. Treat clinical decision support as a future legal review lane.
3. Use FDA Digital Health Policy Navigator before adding clinical claims.
4. Separate wellness/caregiver-awareness features from clinical features.

### FTC and State Privacy

FTC Health Breach Notification Rule amendments emphasize many health apps and similar technologies outside HIPAA. CareSight should assume:

- Direct-to-consumer health/care data can carry breach-notification obligations.
- Unauthorized disclosure to analytics, cloud logs, or third-party services is risky.

Practical steps:

1. No tracking pixels in caregiver dashboards.
2. No default cloud upload.
3. Breach response plan.
4. Data inventory.
5. Encryption and access controls.

## Go-To-Market Strategy

### First Wedge

Families with an aging parent living alone who are technical enough to understand local-first privacy but stressed enough to pay for installation/support.

Message:

> CareSight helps families preserve local care context and coordinate help without sending raw home video to a cloud surveillance platform.

### First Community Channels

- Aging-in-place communities.
- Caregiver forums.
- Local eldercare meetups.
- Home Assistant / privacy tech communities.
- Apple Silicon local AI communities.
- Open-source local-first communities.

Important caution:

- Do not market in a fear-driven way.
- Do not imply medical safety.
- Do not claim emergency response.

### Discovery Questions

1. What care moments create the most uncertainty?
2. What would you want to know before calling or visiting?
3. What video/snapshot sharing feels acceptable?
4. What would make this feel creepy or unacceptable?
5. Would a local appliance be more trustworthy than cloud cameras?
6. Who would install and maintain it?
7. How often are false alerts tolerable?
8. What would you pay for setup and support?
9. Who needs access to the journal?
10. What would make you uninstall it?

## Partnership Targets

### Technical Partners

- Local AI/MLX community.
- Home Assistant/Frigate ecosystem contributors.
- Camera/restreaming experts.
- Privacy/security auditors.
- Apple/macOS automation developers.

### Care Domain Partners

- Family caregiver support groups.
- Occupational therapists.
- Gerontologists.
- Home-care agencies.
- Aging-in-place consultants.
- Dementia caregiver researchers.

### Commercial Partners

- Local home technology installers.
- Senior living technology consultants.
- Small home-care agencies.
- Apple-focused managed service providers.

## Grant Application Package Checklist

Create a reusable grant folder with:

1. One-page executive summary.
2. Product thesis.
3. Technical architecture.
4. Safety and boundary statement.
5. Current prototype evidence.
6. Bug/risk audit.
7. Model evaluation plan.
8. Privacy/security plan.
9. Caregiver discovery plan.
10. Commercialization plan.
11. Team bios.
12. Budget.
13. Milestones.
14. Letters of support.
15. Demo video.

## Suggested First Grant Drafts

### NSF Project Pitch

Title:

Privacy-Preserving Edge AI for Auditable Caregiver Awareness in Aging-in-Place Homes

Problem:

Families need context during possible care events, but cloud cameras and generic alerts create privacy and trust concerns.

Innovation:

Local Apple Silicon vision and language models convert camera observations into bounded, auditable care-event records without sending raw video to the cloud by default.

Commercial potential:

Home care, family caregiving, aging-in-place support, home-care agencies, and later facility workflow.

Phase I milestones:

- Model evaluation.
- Local dashboard.
- Privacy/security controls.
- Caregiver usability validation.

### NLnet Proposal

Title:

Open Local Care-Event Audit Infrastructure for Privacy-Preserving Edge AI

Deliverables:

- Open JSON schemas for event receipts and media-sharing policy.
- Local-only dashboard proof.
- Accessibility-reviewed human review packets.
- Security/privacy threat model.

### AARP AgeTech Application

Position:

CareSight is a local-first caregiver awareness hub for families who want peace of mind without cloud surveillance.

Ask:

- Customer discovery.
- AgeTech mentorship.
- Pilot introductions.
- Feedback on caregiver trust, accessibility, and packaging.

## Risks to Investors and Grant Reviewers

### Technical Risks

- False positives/negatives in real homes.
- Camera setup variability.
- Apple/macOS automation fragility.
- Model performance on low light and occlusion.
- Support burden.

Mitigation:

- Evaluation harness.
- Supported hardware matrix.
- Local dashboard.
- Conservative language.
- Human review.

### Regulatory Risks

- HIPAA applicability for provider/facility sales.
- FDA device-function analysis if claims drift.
- FTC/state privacy obligations.

Mitigation:

- Legal review before regulated pilots.
- Avoid medical claims.
- Privacy/security control matrix.

### Business Risks

- Families may resist cameras.
- Hardware install costs may be high.
- Home-care agencies may require integrations.
- Open-source competitors may copy features.

Mitigation:

- Local-first trust.
- Paid support and appliance packaging.
- Caregiver workflow focus.
- Strong evidence and auditability.

## Recommended Next 30 Days

1. Fix high-risk audit issues before live demos.
2. Create a one-page business summary.
3. Conduct 10 caregiver discovery interviews.
4. Create a model evaluation plan.
5. Create a privacy/security threat model outline.
6. Draft NSF Project Pitch.
7. Draft AARP accelerator application.
8. Draft NLnet open-source infrastructure proposal.
9. Identify one gerontology/HCI research advisor.
10. Identify one home-care agency discovery partner.

## Recommended Next 90 Days

1. Complete model evaluation harness.
2. Build local dashboard MVP.
3. Run internal multi-day pilot.
4. Build privacy/security control matrix.
5. Prepare household pilot consent and uninstall/delete workflow.
6. Submit AARP application.
7. Submit NSF Project Pitch.
8. Submit NLnet proposal if open-source deliverables are strong.
9. Package pilot kit budget.
10. Define paid pilot terms.

## Sources

- NSF America's Seed Fund: https://seedfund.nsf.gov/
- NSF Digital Health topic: https://seedfund.nsf.gov/topics/digital-health/
- NIH small business overview: https://www.grants.nih.gov/funding/funding-categories/small-business
- NIA NIH almanac and small-business context: https://www.nih.gov/about-nih/nih-almanac/national-institute-aging-nia
- AARP AgeTech Collaborative startups page: https://agetechcollaborative.org/startups/
- NLnet funding page: https://nlnet.nl/funding.html
- HHS Business Associates guidance: https://www.hhs.gov/hipaa/for-professionals/privacy/guidance/business-associates/index.html
- FTC Health Breach Notification Rule basics: https://www.ftc.gov/business-guidance/resources/health-breach-notification-rule-basics-business
- FDA CDS/Digital Health Policy Navigator FAQ: https://www.fda.gov/medical-devices/software-medical-device-samd/clinical-decision-support-software-frequently-asked-questions-faqs

