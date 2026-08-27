# CRM workshop

Hands-on documentation for testing the built-in **ERPNext CRM module** on
`erp.habibi-erp.com`. Both files are self-contained HTML — open them by
double-clicking, no server and no build step.

| File | What it is |
| --- | --- |
| `crm-shakedown-run.html` | Test card. 10 stages, 47 checks. Tick-box format for verifying the module works end to end. |
| `crm-role-playbook.html` | Procedure manual. 12 parts, 54 procedures with exact click paths and the ERPNext role each step requires. |

Both follow the same fictional scenario — **Al-Noor Academy**, a Riyadh school
group met at a trade show — through one deal that is won and one that is lost,
so the pipeline reports have both outcomes to read back.

Start with the playbook if you are doing the clicking. Use the shakedown run if
you are signing off that the module works.

## Notes

- Progress is stored per-browser in `localStorage`; the **Reset** button clears it.
- A theme toggle sits bottom-right (Auto / Light / Dark).
- Typefaces load from Google Fonts. Offline, they fall back to system fonts and
  the pages still read fine.
- Content is written against this instance specifically: company `Test (Demo)`,
  currency SAR, and the real permission matrix as read from the site. The
  playbook's appendix documents which role can touch which doctype.

## Two things worth knowing before you run it

1. **`Opportunity Lost Reason` is empty on this instance and nothing seeds it.**
   You cannot mark any opportunity as Lost until you create at least one record.
   Both documents handle this in their first section.

2. **No single ERPNext role can complete the CRM flow.** Sales Manager has
   read-only access to `Customer`; Sales User has read-only access to
   `Prospect`. A working sales seat needs both roles together.

## Horizon

The built-in CRM module carries a deprecation notice in its own workspace: it is
scheduled for removal in **ERPNext v17**, with [Frappe CRM](https://frappe.io/crm)
as the successor and a migration app available. Everything here is valid on
v15/v16.

---

Regenerated from source with `wrap_local.py` (not checked in) — edit the HTML
directly if you need changes.
