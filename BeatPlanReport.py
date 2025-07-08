import tableauserverclient as TSC 
import smtplib 
import os
from email.mime.multipart import MIMEMultipart 
from email.mime.application import MIMEApplication 
from email.mime.text import MIMEText 
from email.mime.image import MIMEImage
import shutil



# === CONFIG === 

TABLEAU_SERVER_URL = "https://prod-apsoutheast-b.online.tableau.com/"
USERNAME = "renu.sharma@dharmalifelabs.com"
PASSWORD = "Nammu11@2023"
SITE_ID = "Dharmalife"  
TARGET_VIEW_URLS = [
    "BeatPlanReportTB/sheets/Beatplanemployeewise(June)",
    "BeatPlanReportTB/sheets/DailyBeatplanemployeewise(June)",
    "BeatPlanReportTB/sheets/BeatplanbyRole(June)"
]

current_dir = os.path.abspath(__file__)
parent_dir = os.path.dirname(current_dir) 

# Define OUTPUT_DIR inside that parent
OUTPUT_DIR = os.path.join(parent_dir, "pdf_exports")

# Create it if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
# Clear the output directory
if os.path.exists(OUTPUT_DIR):
    shutil.rmtree(OUTPUT_DIR)  # Remove the entire directory
os.makedirs(OUTPUT_DIR)        # Recreate the empty directory

SMTP_SERVER = "smtp.office365.com"
EMAIL_FROM = "reports@dharmalifelabs.com"
EMAIL_TO = ["jatin.kumar@dharmalifelabs.com"]

# === AUTHENTICATE WITH TABLEAU === 
# tableau_auth = TSC.TableauAuth(USERNAME, PASSWORD, site_id="Dharmalife")
tableau_auth = TSC.PersonalAccessTokenAuth(
    token_name='Python Lib',
    personal_access_token = os.environ.get("TABLEAU_TOKEN"),
    site_id='Dharmalife'
)
target_view = None
server = TSC.Server(TABLEAU_SERVER_URL, use_server_version=True)
matched_views = {}



msg = MIMEMultipart()
msg['From'] = EMAIL_FROM
msg['To'] = ", ".join(EMAIL_TO)
msg['Subject'] = "Automated Tableau Report"

html_body = """
<html>
  <body>
    <p>Dear Team,<br><br>
       Please find attached daily Beat Plan report for the month of June-2025.<br><br>
       Regards,<br>
       Tableau
    </p>
  </body>
</html>
"""

with server.auth.sign_in(tableau_auth):
    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Fetch all workbooks
    request_options = TSC.RequestOptions()
    request_options.page_size = 1000
    all_workbooks, _ = server.workbooks.get(request_options)

    for workbook in all_workbooks:
        # Filter target views that match this workbook
        related_view_urls = [
            url for url in TARGET_VIEW_URLS if url.startswith(workbook.content_url)
        ]
        if not related_view_urls:
            continue
        
        # Populate views inside this workbook
        server.workbooks.populate_views(workbook)

        for view in workbook.views:
            # Construct view URL
            # print(view.name)
            constructed_view_url = f"{workbook.content_url}/sheets/{view.name.replace(' ', '')}"
            if constructed_view_url in TARGET_VIEW_URLS:
                matched_views[constructed_view_url] = view
                
                server.views.populate_image(view)
                image_data = view.image

                # === Embed image in email ===
                cid = constructed_view_url.replace("/", "_")  # unique ID for Content-ID
                img = MIMEImage(image_data)
                img.add_header('Content-ID', f"<{cid}>")
                msg.attach(img)

                # === Add to HTML body ===
                html_body += f"<b>{view.name}</b><br><img src='cid:{cid}'><br><br>"
                # === Export PDF ===
                server.views.populate_pdf(view)
                filename = f"{view.name.replace(' ', '_')}.pdf"
                filepath = os.path.join(OUTPUT_DIR, filename)

                with open(filepath, 'wb') as f:
                    f.write(view.pdf)

                print(f"✅ Exported PDF for: {constructed_view_url} → {filepath}")

# === Result Summary ===
for url in TARGET_VIEW_URLS:
    if url not in matched_views:
        print(f"❌ View not found or not exported: {url}")



msg.attach(MIMEText(html_body, 'html'))

# === Attach All PDFs in OUTPUT_DIR ===
OUTPUT_DIR = "./pdf_exports"  # same as used during PDF export
pdf_files = [f for f in os.listdir(OUTPUT_DIR) if f.lower().endswith(".pdf")]

for filename in pdf_files:
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, "rb") as f:
        part = MIMEApplication(f.read(), Name=filename)
        part['Content-Disposition'] = f'attachment; filename="{filename}"'
        msg.attach(part)

# === Send the Email ===
with smtplib.SMTP(SMTP_SERVER, 587) as server:
    server.starttls()
    server.login(EMAIL_FROM, "Dharma@#719!")
    server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())

print("✅ Email sent with all PDF attachments.")








