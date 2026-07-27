import pytest
from playwright.sync_api import Page, expect

STREAMLIT_URL = "https://one-more-day-kke2zulaouzzarvjyhkrz6.streamlit.app"
TEST_EMAIL = "tami@example.com"
TEST_PASSWORD = "TempPass123!"

def test_login_page_loads(page: Page):
    page.goto(STREAMLIT_URL)
    page.wait_for_timeout(4000)
    expect(page).to_have_title('One More Day · Streamlit')
    

def test_login_succeeds(page: Page):
    page.goto(STREAMLIT_URL)
    page.wait_for_timeout(6000)
    frame = page.frame(url="https://one-more-day-kke2zulaouzzarvjyhkrz6.streamlit.app/~/+/")
    frame.get_by_role("textbox", name="Email").first.fill(TEST_EMAIL)
    frame.get_by_label("Password").first.fill(TEST_PASSWORD)
    frame.get_by_role("button", name="Log In").click()
    page.wait_for_timeout(4000)
    expect(frame.get_by_text("Logged in as:")).to_be_visible()
    
def test_habits_page_loads(page: Page):
    page.goto(STREAMLIT_URL)
    page.wait_for_timeout(6000)
    frame = page.frame(url="https://one-more-day-kke2zulaouzzarvjyhkrz6.streamlit.app/~/+/")
    frame.get_by_role("textbox", name="Email").first.fill(TEST_EMAIL)
    frame.get_by_label("Password").first.fill(TEST_PASSWORD)
    frame.get_by_role("button", name="Log In").click()
    page.wait_for_timeout(4000)
    expect(frame.get_by_text("Habit Management")).to_be_visible()
    
def test_checkin_page_loads(page: Page):
    page.goto(STREAMLIT_URL)
    page.wait_for_timeout(6000)
    frame = page.frame(url="https://one-more-day-kke2zulaouzzarvjyhkrz6.streamlit.app/~/+/")
    frame.get_by_role("textbox", name="Email").first.fill(TEST_EMAIL)
    frame.get_by_label("Password").first.fill(TEST_PASSWORD)
    frame.get_by_role("button", name="Log In").click()
    page.wait_for_timeout(4000)
    frame.get_by_role("combobox", name="Navigate").click()
    page.wait_for_timeout(1000)
    frame.get_by_text("Check-in", exact=True).click()