import os
import json
from playwright.sync_api import sync_playwright

HERE = os.path.abspath(os.path.dirname(__file__))

EMAIL_AND_PASSWORD_P = os.path.join(HERE, "email_and_password.json")
STREAMABLE_COOKIES_P = os.path.join(HERE, "streamable_cookies.json")

with open(EMAIL_AND_PASSWORD_P, "r") as f:
    data = json.loads(f.read())
    email_address = data["email_address"]
    password = data["password"]

    if email_address == "" and not os.path.isfile(STREAMABLE_COOKIES_P):
        print("You need to enter your e-mail address and password in email_and_password.json!")
        print("Feel free to open the file in something like Notepad++.")
        raise SystemExit

def run():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()
        # Open new page
        page = context.new_page()
        # Go to https://streamable.com/
        page.goto("https://streamable.com/")
        # Click text=Login
        page.locator("text=Login").click()
        # expect(page).to_have_url("https://streamable.com/login")
        # Click [placeholder="Email or username"]
        page.locator("[placeholder=\"Email or username\"]").click()
        # Fill [placeholder="Email or username"]
        page.locator("[placeholder=\"Email or username\"]").fill(email_address)
        # Press Tab
        page.locator("[placeholder=\"Email or username\"]").press("Tab")
        # Fill [placeholder="Password"]
        page.locator("[placeholder=\"Password\"]").fill(password)
        # Press Enter
        # with page.expect_navigation(url="https://streamable.com/"):
        with page.expect_navigation():
            page.locator("[placeholder=\"Password\"]").press("Enter")
        # ---------------------
        
        # Get the cookies
        cookies = context.cookies("https://streamable.com/")
        streamable_cookies = {}

        for cookie in cookies:
            streamable_cookies[cookie["name"]] = cookie["value"]

        streamable_cookies_p = os.path.join(HERE, "streamable_cookies.json")

        with open(streamable_cookies_p, "w+") as f:
            f.write(json.dumps(streamable_cookies))
        
        context.close()
        browser.close()

    
if __name__ == "__main__":
    run()
