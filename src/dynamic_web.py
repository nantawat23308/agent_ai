from playwright.sync_api import sync_playwright
# import easyocr



def is_captcha_present(page):
    """Detects common CAPTCHA elements on the page."""
    # Check for Google reCAPTCHA
    if page.locator("iframe[src*='recaptcha']").count() > 0:
        print("reCAPTCHA detected!")
        return True

    # Check for hCaptcha
    if page.locator("iframe[src*='hcaptcha']").count() > 0:
        print("hCaptcha detected!")
        return True

    # Check for Cloudflare Turnstile
    if page.locator("iframe[src*='challenges.cloudflare']").count() > 0:
        print("Cloudflare Turnstile CAPTCHA detected!")
        return True

    return False



# reader = easyocr.Reader(['en'])
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    # Visit the dynamic website
    query = "example search"
    num_results = 10
    google_search = "https://www.google.com/search?q=" + query + "&num=" + str(num_results)
    tour_de_france = "https://www.letour.fr/en/"
    page.goto(tour_de_france, wait_until="networkidle")
    page.get_by_role("button", name="Teams").click()

    page.get_by_label("Alpecin-Deceuninck").click()


    if is_captcha_present(page):
        print("CAPTCHA detected, handle it!")
    else:
        print("No CAPTCHA detected.")
    page.pause()

    browser.close()