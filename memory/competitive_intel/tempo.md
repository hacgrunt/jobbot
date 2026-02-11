# Tempo — Competitive Intel & Positioning Analysis

## 2026-02-11 — Pre-Screener Research

### What Tempo Is
Stripe + Paradigm L1 blockchain purpose-built for stablecoin payments. $500M Series A at $5B valuation (Oct 2025). Pre-mainnet — testnet launched Dec 2025, mainnet expected 2026. Team scaling from 15 to 40-50. No native token.

### Key Technical Claims
- **Payment lanes:** Dedicated blockspace for payment txns at protocol level. Fees ~$0.001 regardless of congestion.
- **100k TPS, sub-second finality** — theoretical; real sustained throughput unknown until mainnet.
- **Stablecoin gas:** Pay fees in any stablecoin, no need to hold a native token.
- **EVM compatible:** Built with Reth SDK. Custom tx type (0x76) with passkey auth, call batching, fee sponsorship.
- **Opt-in privacy** with compliance hooks for KYC/AML.

### Design Partners (not all confirmed builders)
Visa, Mastercard, Deutsche Bank, UBS, Shopify, Revolut, Nubank, Klarna, DoorDash, OpenAI, Anthropic, Mercury, Lead Bank, Standard Chartered. Klarna issued KlarnaUSD on testnet — most concrete partner commitment.

### Notable Hires
- Dan Romero + Varun Srinivasan (Farcaster founders) — community/ecosystem signal
- Dankrad Feist (ex-Ethereum Foundation researcher)
- Liam Horne (ex-Optimism CEO)

---

## Honest Positioning Analysis (Marketing vs. Reality)

### The real reason Tempo exists: vertical integration
Stripe processes $1T+ annually. Stablecoins threaten to commoditize card rails. Stripe's choice: own the settlement layer or become a thin integration layer on someone else's chain. Tempo is the "own the chain" play. Primary motivation is Stripe capturing fees at every layer, not "the world needs a new payments chain."

Circle doing the same thing with Arc for the same reason — they see tx fees flowing to Ethereum/Solana/Tron and want that revenue.

### Claim-by-Claim Breakdown

| Claim | Marketing Spin | Reality |
|---|---|---|
| **Payment lanes** | Revolutionary protocol innovation | Priority queue with guaranteed throughput. Conceptually similar to Solana's local fee markets. It's QoS at chain level — useful for enterprise SLAs, but not a paradigm shift. Could be solved with a well-designed L2. |
| **No native token** | Principled, not extractive | Smartest positioning move. Avoids SEC scrutiny, calms enterprise boards. But also means Stripe captures all economic value via tx fees. Centralization play dressed as simplicity. Key question: who runs validators? If "Stripe and partners" → this is closer to a private payment network on blockchain tech. |
| **100k TPS** | Fastest chain ever | Every new chain claims insane TPS. Solana claims 65k, sustains ~4k. Visa averages ~1,700 TPS. Building for 50x Visa volume is aspirational, not current need. Wait for mainnet numbers. |
| **Partner list** | World's biggest companies building on us | "Partner" and "design partner" doing heavy lifting. Could range from "building a product" to "had three meetings and signed an NDA." Treat as signal of interest, not commitment. Klarna's stablecoin is the most real. |
| **EVM compatible** | Easy dev onboarding | Genuine. Table stakes but smart. No complaints. |

### What's Genuinely Needed (not BS)
1. **Enterprise-grade SLAs for on-chain payments.** "Usually cheap and fast" ≠ "always cheap and fast, contractually." This is a real gap.
2. **Compliance infra at protocol level.** Opt-in privacy + KYC/AML at chain layer matters for enterprise adoption.
3. **Stablecoin-native UX.** Gas in stablecoins, no volatile token requirement, banking-standard memo fields. Small things that actually bridge TradFi → crypto.
4. **Distribution.** The real moat. Stripe's millions of merchant relationships. If they make stablecoin payments trivially easy through existing Stripe integrations, no crypto-native chain can replicate that GTM.

### Competitive Landscape

| Competitor | Positioning | Advantage | Weakness |
|---|---|---|---|
| **Circle Arc** | USDC-native L1, "money network" | $60B USDC market cap, regulatory moat (46 state licenses), BlackRock | No merchant distribution — issuer, not processor |
| **Tether Stable** | USDT-native L1 | Largest stablecoin by volume | Regulatory baggage, less enterprise credibility |
| **Solana** | General-purpose high-perf L1 | Solana Pay exists, Visa partnership, 50k+ TPS proven | Not purpose-built for payments. No enterprise SLAs. |
| **Tron** | De facto stablecoin settlement | $10B+ daily USDT volume | Reputation issues, not enterprise-friendly |
| **Codex / 1Money / Converge** | Various stablechain startups | Niche plays | No distribution, no brand |

**Primary competitor: Circle Arc.** Arc = compliance-first, institutional trust. Tempo = commerce-first, merchant distribution.

### The Honest Frame
Tempo is Stripe's bet that stablecoin payments = multi-trillion dollar market, and their play to own the infra layer rather than be commoditized. Tech is solid but not revolutionary — **distribution is the moat.** "Purpose-built for payments" is partially true (enterprise SLAs, compliance, stablecoin UX) and partially marketing cover for vertical integration.

---

## JD Breakdown — Product Marketing Manager

### Role Summary
PMM shaping positioning across partners, supporting GTM, driving awareness among builders/partners/institutions. Blends technical depth with storytelling. Reports into marketing, works cross-functionally with product, eng, partnerships.

### What They Actually Want (reading between the lines)

**The job is 3 jobs:**
1. **Enterprise/partner marketing** — decks, ROI models, fund flow diagrams, talking points that move enterprise deals. This is the revenue-driving work.
2. **Developer marketing** — technically credible docs, dev-focused content, helping builders go live. This is the ecosystem-building work.
3. **Growth/brand** — website, landing pages, digital surfaces, data-driven iteration. This is the awareness work.

They're hiring ONE person to do all three because they're early. Expect this to be scrappy, high-volume, and cross-functional. You're not specializing — you're building the function.

### JD Signals Worth Noting

- **"ROI models, fund flows, diagrams"** — They need someone who can sell to CFOs and payment ops teams, not just write blog posts. Enterprise PMM muscle matters here.
- **"Developer-focused documents which delve deep into our technical stack"** — They want someone who can credibly engage with eng. You need to speak Reth, EVM, tx types, not just hand-wave at "blockchain."
- **"Own digital growth surfaces... use data to measure"** — Growth marketing is explicitly in scope. They want a PMM who thinks in conversion metrics, not just narrative.
- **"Managing partner integrations and complex launches"** — Program management is called out. This role coordinates launch logistics across multiple partners going live.
- **"Blockchain or fintech infrastructure companies"** — They want someone who's done this before in adjacent spaces. Crypto-native or fintech-native, ideally both.

### Key Audience Segments (from JD)
1. **Enterprise payment teams** evaluating integrations (banks, fintechs, platforms)
2. **Developers** building on Tempo
3. **Partners** going live (Klarna, Shopify, etc.)
4. **Institutions** moving money on-chain

### What to Emphasize in Screener
- Experience translating technical products into enterprise narratives
- Comfort with developer audiences (docs, technical content)
- Data-driven approach to marketing (KPIs, measurement, iteration)
- Program management for multi-stakeholder launches
- Crypto/fintech infrastructure background
- Ability to context-switch between audiences (dev docs → board deck → CT post)

---

## Open Questions for Screener / Future Research
- Decentralization story: Who runs validators? What's governance without a token?
- Revenue model specifics: What cut of tx fees does Tempo take?
- How does Tempo handle cross-chain interop? Stablecoins exist on 10+ chains.
- What's the developer ecosystem strategy beyond EVM compat?
- How do they position against L2s that could add payment lanes as a feature?
- What does the marketing team look like today? Who does this role report to?
- What's the mainnet launch timeline and how does PMM fit into launch sequencing?
- Which partner integrations are closest to going live?
- How do they think about crypto-native community vs. enterprise audience priority?
