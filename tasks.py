import time
from robocorp.tasks import task
from robocorp import browser, log
from RPA.HTTP import HTTP
from RPA.PDF import PDF
from RPA.Tables import Tables
from RPA.Archive import Archive

# Global instances
pdf = PDF()
tables = Tables()
archiver = Archive()

# Output folder
OUTPUT_DIR = "output/receipts"

@task
def order_robots_from_RobotSpareBin():
    """
    Orders robots from RobotSpareBin Industries Inc.
    Saves each receipt as PDF, with a screenshot embedded.
    Archives all receipts and screenshots into a ZIP file.
    """
    log.info("🚀 Robot started...")

    # Prepare environment
    HTTP().download("https://robotsparebinindustries.com/orders.csv", overwrite=True)
    orders = tables.read_table_from_csv("orders.csv")

    browser.configure(slowmo=100)
    browser.goto("https://robotsparebinindustries.com/#/robot-order")

    for order in orders:
        fill_the_form(order)
        order_number = str(order["Order number"])
        receipt_pdf = store_receipt_as_pdf(order_number)
        screenshot_robot(order_number)
        embed_screenshot_to_receipt(receipt_pdf, order_number)

    archive_receipts()
    log.info("✅ Robot completed successfully!")

def fill_the_form(order):
    page = browser.page()
    log.info(f"📝 Submitting order #{order['Order number']}")
    close_annoying_modal()
    page.select_option("select#head", str(order["Head"]))
    page.click(f"input[id='id-body-{order['Body']}']")
    page.fill("xpath=//div[3]/input", order["Legs"])
    page.fill("#address", order["Address"])

    for attempt in range(5):
        page.click("button:text('Order')")
        try:
            page.wait_for_selector("#receipt", timeout=500)
            return
        except:
            time.sleep(1)
    raise Exception("❌ Order submission failed after retries.")

def close_annoying_modal():
    page = browser.page()
    try:
        page.click("button:text('OK')", timeout=500)
    except:
        pass  # Modal not present

def store_receipt_as_pdf(order_number):
    page = browser.page()
    receipt_html = page.locator("#receipt").inner_html()
    pdf_file = f"{OUTPUT_DIR}/receipt-{order_number}.pdf"
    pdf.html_to_pdf(receipt_html, pdf_file)
    return pdf_file

def screenshot_robot(order_number):
    page = browser.page()
    image_file = f"{OUTPUT_DIR}/robot-{order_number}.png"
    page.locator("#robot-preview-image").screenshot(path=image_file)
    page.click("button:text('Order Another Robot')")
    #return image_file

def embed_screenshot_to_receipt(receipt_pdf, order_number):
    output_pdf = f"{receipt_pdf}_merged.pdf"
    image_file = f"{OUTPUT_DIR}/robot-{order_number}.png"
    pdf.add_files_to_pdf(
        files=[
            receipt_pdf,
            image_file
        ],
        target_document=output_pdf
    )

def archive_receipts():
    archiver.archive_folder_with_zip(
        folder=OUTPUT_DIR,
        archive_name="output/robot_orders.zip",
        recursive=True
    )
