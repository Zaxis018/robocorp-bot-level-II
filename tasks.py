import csv
import time

from robocorp.tasks import task
from robocorp import browser

from RPA.HTTP import HTTP
from RPA.PDF import PDF
from RPA.Archive import Archive

@task
def order_robots_from_Robotsparebin():
    """
    Orders robots from RobotSpareBin Industries Inc.
    Saves the order HTML receipt as a PDF file.
    Saves the screenshot of the ordered robot.
    Embeds the screenshot of the robot to the PDF receipt.
    Creates ZIP archive of the receipts and the images.
    """
    open_robot_order_website()
    orders = get_orders()
    close_annoying_modal()
    fill_the_form()
    archive_receipts()
    

def open_robot_order_website():
    browser.goto("https://robotsparebinindustries.com/#/robot-order")

def get_orders():
    http = HTTP()
    http.download(url="https://robotsparebinindustries.com/orders.csv", overwrite=True)
    return 'orders.csv'

def close_annoying_modal():
    page = browser.page()
    page.click("button:text('Yep')")


def fill_the_form():
    """Read data from CSV and fill in the sales form"""
    with open('orders.csv', 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            fill_and_submit_sales_form(row)

def fill_and_submit_sales_form(order_row):
    page = browser.page()
    page.select_option("#head",str(order_row["Head"])) # for select options
    page.check(f'#id-body-{order_row["Body"]}') # for checking radio buttons match number in csv to id field of html element of radio button

    # If the placeholder is unique and doesn't change, you can use XPath to locate the element
    leg_input_xpath = "//input[@placeholder='Enter the part number for the legs']"
    page.fill(leg_input_xpath, order_row["Legs"])

    page.fill("#address", str(order_row["Address"]))
    page.click("text=Preview")
    submit_order(order_row)

def submit_order(order_row):
    page = browser.page()
    max_attempts = 10 

    for attempt in range(max_attempts):
        page.click("button:text('Order')") # Click the Order  button

        # Wait for a short period to allow the page to process the submit
        time.sleep(0.5)

        # Check for the presence of the error message
        error_message = page.query_selector(".alert.alert-danger")

        if error_message is None:
            break
        elif attempt < max_attempts - 1: # retry
            continue
        else:
            # If the error message present and last attempt, raise an exception
            raise Exception(f"Failed to submit order after {max_attempts} attempts")
        
    order_number = order_row["Order number"]
    pdf_file = store_receipt_as_pdf(order_number)
    screenshot = screenshot_robot(order_number)
    embed_screenshot_to_receipt(screenshot, pdf_file)

    page.click("button:text('Order another robot')")
    close_annoying_modal()

def store_receipt_as_pdf(order_number):
    """
    Store the order receipt as a PDF file.
    """
    page = browser.page()
    pdf = PDF()
    output_dir = "output/receipts"
    robot_sale_html = page.locator("#receipt").inner_html()
    pdf_file = f"{output_dir}/receipt_{order_number}.pdf"
    pdf.html_to_pdf(robot_sale_html, pdf_file)
    return pdf_file

def screenshot_robot(order_number):
    """
    Take a screenshot of the robot.
    """
    page = browser.page()
    screenshot_path = f"output/screenshots/screenshot_{order_number}.png"
    element = page.query_selector("#robot-preview-image") 
    element.screenshot(path=screenshot_path)
    return screenshot_path

def embed_screenshot_to_receipt(screenshot, pdf_file):
    """
    Embed the robot screenshot to the receipt PDF file.
    """
    pdf = PDF()
    pdf.add_watermark_image_to_pdf(image_path=screenshot,source_path = pdf_file,output_path = pdf_file)

def archive_receipts():
    lib = Archive()
    lib.archive_folder_with_zip('output/receipts','output/receipt.zip')