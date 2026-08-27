# Habibi Burger workshop

Workshop and PoC pack for **Habibi Burger** — WhatsApp-ordered burger delivery
running on vanilla ERPNext. Built and verified on `erp.habibi-erp.com`
(Frappe v16.31 / ERPNext v16.32), company **Habibi Burger**, currency KZT.

The three HTML files are self-contained — double-click to open, no server and
no build step.

| File | What it is |
| --- | --- |
| `burger-role-playbook.html` | The main document. 9 parts, 36 procedures with exact click paths, split across three seats: order desk, kitchen, courier. |
| `burger-ai-intake-pack.html` | The AI WhatsApp module's output contract — one order expressed twice: as a card a human keys in, and as a REST payload. Plus every supporting call, guardrail and failure mode. |
| `burger-shakedown-run.html` | Acceptance sheet. 11 stages, 61 checks, against the PoC success criteria. Stage 11 is what is honestly not done. |
| `BUILD-LOG.md` | Everything that was created on the live instance, and what to delete to undo it. |
| `habibi-burger-poc-scope_1.md` | The client input document this pack was built from. |

Start with the playbook if you are doing the clicking. Use the shakedown run if
you are signing off. Hand the intake pack to whoever builds the middleware.

## The scenario

One order — Aigerim Bekova, a signature burger, fries and a lemonade to Dostyk
Ave 132, ₸6,670 — carried end to end: WhatsApp conversation → REST-created
Sales Order → payment gate → kitchen board → courier → delivered → invoiced →
counted on the dashboard. It exists on the instance as `SAL-ORD-2026-00007`,
already through the whole pipeline.

Eight more orders sit across the board in every other state, including one
genuinely cancelled order with its payment reversed.

## Three findings worth knowing before you read anything

1. **The kitchen kanban is native.** No fork, no restaurant app, no custom
   code — a Kanban view over Sales Order grouped by one custom Select field.
   Drag-and-drop works on submitted documents because the field is marked
   allow-on-submit.

2. **Dragging a card is not a way around the rules.** Frappe's Kanban writes
   the field directly via `frappe.client.set_value`, but that save still runs
   workflow validation. An illegal drag is refused by the server with
   *Workflow State transition not allowed*. Role gates and payment gates hold
   on the board exactly as they hold on the form. This was tested, not assumed.

3. **"No cooking before payment" is enforced, not requested.** The
   Confirmed → In Kitchen transition carries the condition
   `advance_paid >= grand_total`. Until the money is recorded the action does
   not exist in any menu, and the API returns *Not a valid Workflow Action*.

## Two things that will bite you

- **VAT does not auto-expand over REST.** Posting `taxes_and_charges` without
  the `taxes` rows produces a syntactically valid order with zero VAT and a
  wrong total. The Intake Pack has the exact block to send. This is the single
  most likely integration mistake on this build.

- **Workflow actions live under `Actions ⌄`, not `Status ⌄`.** The neighbouring
  `Status` button is ERPNext's own Hold / Close and has nothing to do with the
  kitchen. Staff will click the wrong one on day one.

## Blocked, and why

- **Outbound WhatsApp messages.** The `habibi_whatsapp` app is installed but no
  WhatsApp Account is configured. Templates push to Meta for approval on save,
  so none can be created until credentials exist. Meta Business Verification has
  not been started and has a long lead time — begin it now; nothing else depends
  on it.
- **The middleware itself.** Not built. Every payload in the Intake Pack was
  verified by hand against the live REST API instead.
- **The ~1,000 customer import.** Waiting on the client file. Six demo guests
  stand in.

## Notes

- Progress in the playbook and shakedown run is stored per-browser in
  `localStorage`; the **Reset** button clears it.
- A theme toggle sits bottom-right (Auto / Light / Dark).
- Typefaces load from Google Fonts. Offline they fall back to system fonts and
  the pages still read fine.
- Regenerated from source with the scripts noted in `BUILD-LOG.md` (not checked
  in) — edit the HTML directly if you need changes.










## Claude summary

What you asked for, and where it is

habibi/burger-workshop/

┌────────────────────────────┬───────────────────────────────────────────────────────────────────┐
│            File            │                            What it is                             │
├────────────────────────────┼───────────────────────────────────────────────────────────────────┤
│ burger-role-playbook.html  │ 9 parts, 36 procedures, exact click paths, across the three seats │
├────────────────────────────┼───────────────────────────────────────────────────────────────────┤
│ burger-ai-intake-pack.html │ The AI module's input contract — order card and REST payload      │
├────────────────────────────┼───────────────────────────────────────────────────────────────────┤
│ burger-shakedown-run.html  │ 11 stages, 61 acceptance checks                                   │
├────────────────────────────┼───────────────────────────────────────────────────────────────────┤
│ BUILD-LOG.md               │ Everything created on the instance, plus how to undo it           │
├────────────────────────────┼───────────────────────────────────────────────────────────────────┤
│ README.md                  │ Index                                                             │
└────────────────────────────┴───────────────────────────────────────────────────────────────────┘

Roles map to your three tracks: Burger Order Desk (sales + escalation + analyst in one seat), Burger Kitchen, Burger Courier.

The AI input exists in both forms you asked for — a plain-text order card ready to key in by hand, and a verified POST /api/resource/Sales Order payload, plus customer lookup, menu reads, workflow transitions, escalation and failure modes.

Kitchen Kanban: yes, natively

No fork, no custom app. A Kanban view over Sales Order grouped by one custom Select field. The important part I tested rather than assumed: dragging a card is not a way around the rules. Frappe's Kanban writes the field directly, but that save still runs workflow validation — an illegal drag is refused server-side with Workflow State transition not allowed. So the board is both the kitchen UI and a properly gated one.

I also built the "no cooking before payment" rule as a workflow condition (advance_paid >= grand_total), so the Send to Kitchen action simply doesn't exist on an unpaid order — verified in the UI and over the API.

Things you should know

- A real bug in habibi_whatsapp: creating a WhatsApp Templates record with no WhatsApp Account configured fails with a raw NameError: name 'throw' is not defined instead of a readable message. Outbound status messages are therefore documented but not built — no Meta credentials exist.
- I changed a site-wide setting: Selling Settings.so_required → Yes, per scope §4. This affects Test (Demo) too.
- I briefly broke permissions and repaired them. Inserting a Custom DocPerm directly makes Frappe use custom perms exclusively for that doctype, silently dropping the shipped roles. It hit Item and Customer; I restored them via permission_manager. Noted in the build log so nobody repeats it.
- I misclicked and cancelled order 00011 mid-session. Rather than hide it, I left it as a genuine cancelled-with-payment-reversed example and recreated the order as 00015.
- Open items I did not decide for you: delivery fee model, agent order-value cap, out-of-hours behaviour, refund ownership, and the site timezone (still Asia/Riyadh on a Kazakhstan company). All flagged as decide in Stage 11.

Company is Habibi Burger / KZT / VAT 12% VAT-inclusive, with 17 menu items, 6 customers, 3 couriers, 4 zones and 9 demo orders spread across every board state.

✻ Churned for 39m 21s

※ recap: Goal was a Habibi Burger workshop pack plus a live ERPNext PoC. Both are done: three HTML docs and a build log are in habibi/burger-workshop, and the instance is configured and verified. Next, decide the open items flagged in Stage 11. (disable recaps in /config)

