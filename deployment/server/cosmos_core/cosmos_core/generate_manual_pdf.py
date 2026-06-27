import frappe
from frappe.utils.pdf import get_pdf
from frappe import _

def generate_user_manual_pdf():
    articles = frappe.get_all("Help Article",
        filters={"published": 1},
        fields=["title", "content", "category", "route"],
        order_by="category asc, title asc"
    )
    if not articles:
        frappe.throw("No published Help Articles found")
    
    chapters = {}
    for a in articles:
        cat = a.category or "General"
        if cat not in chapters:
            chapters[cat] = []
        chapters[cat].append(a)
    
    toc_html = ""
    article_map = {}
    toc_number = 1
    for cat in sorted(chapters.keys()):
        toc_html += f'<li><strong>{toc_number}. {cat}</strong></li>\n'
        art_num = 1
        for a in chapters[cat]:
            anchor = f"{cat}-{a.title}".replace(" ", "-").lower()
            article_map[a.route] = anchor
            toc_html += f'<li style="padding-left:20px;">{toc_number}.{art_num} <a href="#{anchor}">{a.title}</a></li>\n'
            art_num += 1
        toc_number += 1

    content_html = ""
    chapter_num = 1
    for cat in sorted(chapters.keys()):
        art_num = 1
        for a in chapters[cat]:
            anchor = article_map.get(a.route, f"{cat}-{a.title}".replace(" ", "-").lower())
            full_content = a.content or ""
            full_content = full_content.replace('href="/app/', 'href="https://cosmoserp.com/app/')
            content_html += f'<div id="{anchor}"><h1 style="page-break-before:always;font-size:20pt;color:#1a5276;border-bottom:3px solid #1a5276;padding-bottom:8px;">{chapter_num}.{art_num} {a.title}</h1>{full_content}</div>\n'
            art_num += 1
        chapter_num += 1

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>CosmOS User Manual</title>
<style>
@page {{ size:A4; margin:2cm 2.5cm;
  @top-center {{ content:"CosmOS User Manual"; font-size:9pt; color:#666; }}
  @bottom-center {{ content:"Page " counter(page) " of " counter(pages); font-size:8pt; color:#666; }}
}}
body {{ font-family:'Helvetica','Arial',sans-serif; font-size:10pt; line-height:1.6; color:#333; }}
.cover {{ text-align:center; padding-top:200px; page-break-after:always; }}
.cover h1 {{ font-size:36pt; color:#1a5276; margin-bottom:10px; }}
.cover .sub {{ font-size:16pt; color:#555; margin-bottom:50px; }}
.cover .meta {{ font-size:11pt; color:#888; }}
ul {{ margin:8px 0; padding-left:20px; }}
li {{ margin:4px 0; }}
strong {{ color:#1a5276; }}
a {{ color:#2980b9; }}
</style></head><body>
<div class="cover">
  <h1>CosmOS User Manual</h1>
  <div class="sub">Complete ERP System Guide</div>
  <div class="meta">{frappe.utils.today()}</div>
  <div class="meta">Version 16.23</div>
</div>
<div style="page-break-after:always;">
  <h2 style="font-size:18pt;color:#1a5276;border-bottom:2px solid #1a5276;padding-bottom:8px;">Table of Contents</h2>
  <ul>{toc_html}</ul>
</div>
{content_html}
<div style="page-break-before:always;">
  <h1 style="font-size:20pt;color:#1a5276;">Support</h1>
  <p>For assistance with CosmOS:</p>
  <ul>
    <li><strong>Email:</strong> support@cosmoserp.com</li>
    <li><strong>Issues:</strong> https://github.com/saleelhussain-design/cosmos_docker/issues</li>
    <li><strong>Manual:</strong> Available in CosmOS User Manual workspace</li>
  </ul>
</div>
</body></html>"""
    
    pdf = get_pdf(html)
    filename = f"CosmOS_User_Manual_{frappe.utils.today()}.pdf"
    
    existing = frappe.db.get_value("File", {"file_name": ("like", "CosmOS_User_Manual_%.pdf")})
    if existing:
        frappe.delete_doc("File", existing, ignore_permissions=True, force=True)
    
    file_doc = frappe.get_doc({
        "doctype": "File",
        "file_name": filename,
        "content": pdf,
        "is_private": 0,
    })
    file_doc.save(ignore_permissions=True)
    frappe.db.commit()
    print(f"SUCCESS: {filename}")
    print(f"URL: {file_doc.file_url}")
    return file_doc.file_url

if __name__ == "__main__":
    generate_user_manual_pdf()
