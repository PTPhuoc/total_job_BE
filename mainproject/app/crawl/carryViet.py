import random
from selenium.webdriver.common.by import By
from seleniumbase import Driver
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup
import time


def check_html(driver, tag, retries=5, delay=1, **attributes):
    for _ in range(retries):
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        box_job = soup.find(tag, **attributes)
        if box_job:
            return soup
        time.sleep(delay)
    return None


def check_html_by_selector(driver, attributes, retries=5, delay=1):
    for _ in range(retries):
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        box_job = soup.select_one(attributes)
        if box_job:
            return soup
        time.sleep(delay)
    return None


def handle_captcha(driver, click_captcha=False):
    page_captcha = check_html(driver, "body", 3, class_="no-js")
    if page_captcha:
        print("Phát hiện trang CAPTCHA!")
        box_captcha = check_html_by_selector(driver, "#cf-chl-widget-vpd5c_response", 3)
        if click_captcha:
            if box_captcha:
                print("CAPTCHA yêu cầu xác thực lại!")
                click_captcha = False
            else:
                print("Đã sử lý CAPTCHA. Đang đợi xác thực!")
        else:
            try:
                # driver.wait_for_element("#cf-chl-widget-nk9cv")
                driver.uc_gui_click_captcha(frame="iframe", retry=True, blind=False)
                click_captcha = True
                print("Đã click CAPTCHA!")
            except Exception as ex:
                print("Có lỗi thực hiện click CAPTCHA!. Error: ", str(ex))
                return False
        time.sleep(2)
        handle_captcha(driver, click_captcha)
    else:
        return True


def smooth_scroll_to_element(driver, element, step=70, delay=0.01):
    element_y = driver.execute_script("""
        return arguments[0].getBoundingClientRect().top + window.pageYOffset - (window.innerHeight / 2);
    """, element)
    current_y = driver.execute_script("return window.pageYOffset;")

    while current_y < element_y:
        random_step = random.randint(20, step)
        current_y += random_step
        driver.execute_script(f"window.scrollTo(0, {current_y});")
        time.sleep(delay)


def get_link_job(driver, count):
    all_job = []
    for i in range(count):
        soup = check_html(driver, "div", 5, 1, class_="jobs-side-list")
        if soup:
            all_box = soup.find_all("div", class_="job-item")
            all_job.extend(all_box)
            check_next = check_html_by_selector(driver, "body > main > section.search-result-list > div > div > div.col-lg-8.col-custom-xxl-9 > div.main-slide > div.pagination > ul > li.next-page > a", 5, 1)
            if check_next and i + 1 < count:
                actions = ActionChains(driver)
                link = driver.find_element(By.CSS_SELECTOR, 'body > main > section.search-result-list > div > div > div.col-lg-8.col-custom-xxl-9 > div.main-slide > div.pagination > ul > li.next-page > a')
                smooth_scroll_to_element(driver, link, 70)
                time.sleep(2)
                actions.move_to_element(link).perform()
                actions.click(link).perform()
                print("Đã qua trang mới!")
            else:
                time.sleep(2)
                if i + 1 == count:
                    print("Dừng qua trang!")
                else:
                    print("Không tìm thấy nút tiếp theo!")
                break
        else:
            print("Không tìm thấy nơi chứa danh sách tuyển dụng!")
            break
    return all_job


def get_detail_job(driver, all_link):
    jobs_detail = []
    for job_link in all_link:
        try:
            link = job_link.find("a", class_="job_link").get("href")
            if link:
                driver.get(link)
                job_body = check_html(driver, "div", 3, 1, class_="tabs")
                if job_body:
                    actions = ActionChains(driver)
                    button_infor_company = driver.find_element(By.CSS_SELECTOR, "#tabs-job-company")
                    actions.move_to_element(button_infor_company).perform()
                    actions.click(button_infor_company).perform()
                    page_company = check_html(driver, "div", 3, 1, class_="company-introduction")
                    if page_company:
                        button = driver.find_element(By.CLASS_NAME, "company-jobs-opening")
                        smooth_scroll_to_element(driver, button, 40)
                        html = driver.page_source
                        soup = BeautifulSoup(html, "html.parser")
                        # current_page = soup.find("div", id="tab-2")
                        # print(current_page)
                        get_page = soup.find("div", class_="tabs")
                        jobs_detail.append(get_page)
                    else:
                        print(f"Không phát hiện trang thông tin công ty. Tại:{link}")
                    time.sleep(2)
                else:
                    print(f"Không tìm thấy trang chi tiết tuyển dụng. Tại:{link}")
                    time.sleep(2)
            else:
                print(f"Không tìm thấy link tuyển dụng!")
        except Exception as ex:
            print(f"Có lỗi khi lấy dữ liệu trang. error: {str(ex)}")
    return jobs_detail


def start_craw_carryviet():
    driver = Driver(uc=True, headless=False)
    driver.maximize_window()
    driver.get("https://careerviet.vn/viec-lam/tat-ca-viec-lam-vi.html")
    soup = check_html(driver, "div", 5, 1, class_="jobs-side-list")

    if soup:
        all_link = get_link_job(driver, 1)
        detail_job = get_detail_job(driver, all_link)
        if all_link and detail_job:
            driver.quit()
            return all_link, detail_job
        else:
            print("Không tìm thấy tuyển dụng!")
            driver.quit()
            return [], []
    else:
        print("Không tìm thấy thẻ!")
        driver.quit()
        return [], []
