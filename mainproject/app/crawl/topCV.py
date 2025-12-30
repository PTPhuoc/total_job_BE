import time
from seleniumbase import Driver
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup
import ulid
from asgiref.sync import async_to_sync


class Job:
    def __init__(self, id, name, link, address, date_create):
        self.id = id
        self.name = name
        self.link = link
        self.address = address
        self.date_create = date_create


class Company:
    def __init__(self, id, name, link, image, scale, address, field, decryption):
        self.id = id
        self.name = name
        self.link = link
        self.image = image
        self.scale = scale
        self.address = address
        self.field = field
        self.decryption = decryption


class JobDecryption:
    def __init__(self, id, title, decryption):
        self.id = id
        self.title = title
        self.decryption = decryption


class JobRequire:
    def __init__(self, id, name, field):
        self.id = id
        self.name = name
        self.field = field


class FullJob:
    def __init__(self, job, company, job_desc, job_req):
        self.job = job
        self.company = company
        self.job_desc = job_desc
        self.job_req = job_req


def progress_report(layer, task_id, state, message):
    try:
        print(f"[REPORT] Sending to task_{task_id}: {state}, {message}")
        async_to_sync(layer.group_send)(
            f"task_{task_id}", {"type": "task_send", "state": state, "message": message}
        )
    except Exception as e:
        print("[ERROR] Không thể gửi WebSocket:", e)


def wait_and_check(driver, selector, timeout=5):
    print(f"Đang đợi thẻ {selector}")
    end_time = time.time() + timeout
    while time.time() < end_time:
        try:
            element = driver.find_element(selector)
            if element:
                print(f"Đã thấy thẻ {selector}")
                html = driver.page_source
                soup = BeautifulSoup(html, "html.parser")
                get_element = soup.select_one(selector)
                return get_element
        except NoSuchElementException:
            pass
        time.sleep(1)
    print(f"Không tìm thấy thẻ {selector}")
    return None


def wait_for_pseudo_content(driver, selector, timeout=5):
    print(f"Đang đợi pseudo-element của {selector}")
    end_time = time.time() + timeout
    while time.time() < end_time:
        content = driver.execute_script('''
            const el = document.querySelector(arguments[0]);
            if (!el) return null;
            return window.getComputedStyle(el, '::before').getPropertyValue('content');
        ''', selector)
        if content and content not in ('""', 'none', 'normal'):
            print(f"Đã thấy pseudo-element")
            return content.strip('"')
        time.sleep(0.2)
    print(f"Không thấy pseudo-element trong {timeout}s.")
    return None


def get_safe_value(soup, selector, attr=None, strip=True):
    element = soup.select_one(selector)
    if attr:
        return element.get(attr) if element else "noText"
    else:
        return element.get_text(strip=strip) if element else "noText"


def get_safe_passage(soup, selector):
    element = soup.select_one(selector)
    return "\n".join(element.stripped_strings) if element else "noText"


def scroll_to_button(driver, selector, step=50, delay=0.02):
    button = driver.find_element(selector)
    current_y = driver.execute_script("return window.scrollY") + driver.execute_script("return window.innerHeight;") / 2
    page_height = driver.execute_script("return document.body.scrollHeight")
    while current_y < page_height:
        if current_y > button.location['y']:
            return True
        driver.execute_script(f"window.scrollBy(0, {step});")
        time.sleep(delay)
        current_y += step

    return False


def get_links(driver, get_more=2):
    list_link = []
    for i in range(get_more):
        box_jobs = wait_and_check(driver, ".job-list-search-result", 5)
        if box_jobs:
            links = [a["href"] for a in box_jobs.select("div.avatar > a")]
            list_link.extend(links) if len(links) > 0 else None
            if i < get_more - 1:
                print("Đang cuộn tới nút chuyển trang!")
                if scroll_to_button(driver, "div.job-list-main > nav > ul > li:nth-child(3) > a"):
                    print("Đã cuộn tới nút chuyển trang!")
                    driver.click("div.job-list-main > nav > ul > li:nth-child(3) > a")
                else:
                    print("Không tìm thấy nút chuyển trang!")
            else:
                print("Ngừng chuyển trang!")
        else:
            print("Không tìm thấy danh sách link tuyển dụng!")

    return list_link


def get_job_infor(soup, lk):
    id = str(ulid.new())
    job_name = get_safe_value(soup, ".job-detail__info--title", None, False)
    job_link = lk
    job_address = get_safe_value(soup, "div.job-detail__info--section-content-value > a")
    job_date_create = get_safe_value(soup, "#header-job-info > div.job-detail__info--flex > div")
    job = Job(id, job_name, job_link, job_address, job_date_create)
    return job


def get_job_desc(soup):
    list_desc = soup.select(".job-description__item")
    list_job_desc = []
    if list_desc:
        for item in list_desc:
            id = str(ulid.new())
            title = get_safe_value(item, "h3")
            desc = get_safe_passage(item, ".job-description__item--content")
            job_desc = JobDecryption(id, title, desc)
            list_job_desc.append(job_desc)

    return list_job_desc


def get_job_req(soup):
    list_job_req = []
    first_req = soup.select(".job-detail__info--section")
    if first_req:
        for item in first_req:
            id = str(ulid.new())
            title = get_safe_value(item,
                                   "div.job-detail__info--section-content > div.job-detail__info--section-content-title")
            req = get_safe_value(item,
                                 "div.job-detail__info--section-content > div.job-detail__info--section-content-value")
            if "Địa điểm" in title:
                continue

            job_req = JobRequire(id, title, req)
            list_job_req.append(job_req)
    second_req = soup.select(".box-general-group")
    if second_req:
        for item in second_req:
            id = str(ulid.new())
            title = get_safe_value(item,
                                   "div.box-general-group-info > div.box-general-group-info-title")
            req = get_safe_value(item,
                                 "div.box-general-group-info > div.box-general-group-info-value")
            job_req = JobRequire(id, title, req)
            list_job_req.append(job_req)
    third_req = soup.select(".item.search-from-tag.link")
    if third_req:
        for item in third_req:
            id = str(ulid.new())
            title = "Nghề"
            req = item.get_text(strip=True)
            job_req = JobRequire(id, title, req)
            list_job_req.append(job_req)
    return list_job_req


def get_company_infor(driver, soup):
    field = get_safe_value(soup, "div.job-detail__company--information > div.job-detail__company--information-item.company-field > div.company-value")
    driver.get(get_safe_value(soup, "div.job-detail__box--right.job-detail__company > div.job-detail__company--link > a", "href"))
    check_infor = wait_for_pseudo_content(driver, "#main > div.company-cover > div")
    check_desc_first = wait_for_pseudo_content(driver, "#main > div:nth-child(4) > div")
    check_desc_second = wait_for_pseudo_content(driver, "#main > div:nth-child(4) > div > div")
    company = Company("", "Không tìm thấy", "Không tìm thấy", "Không tìm thấy", "Không tìm thấy", "Không tìm thấy",
                      "Không tìm thấy", "Không tìm thấy")
    if check_infor and check_desc_first and check_desc_second:
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        id = str(ulid.new())
        name = get_safe_value(soup, "div.company-cover > div > div > div.company-detail-overview > div.box-detail > h1")
        image = get_safe_value(soup, "div.company-cover > div > div > div.company-logo > div > img", "src")
        link = get_safe_value(soup, "div > div.company-subdetail-info.website > a", "href")
        check_scale = wait_for_pseudo_content(driver, "span.company-subdetail-info-icon > i")
        scale = get_safe_value(soup, "span.company-subdetail-info-text") if check_scale else "Không tìm thấy"
        address = get_safe_value(soup, "#section-contact > div > div:nth-child(1) > div.desc")
        decs = get_safe_passage(soup, "#section-introduce > div > div > div")
        company = Company(id, name, link, image, scale, address, field, decs)
    else:
        print("Không tìm thấy trang công ty!")
    return company


def get_detail_links(driver, links, layer, task_id):
    list_job_detail = []
    for lk in links:
        try:
            progress_report(layer, task_id, "on", f"Bắt đầu lấy dữ liệu từ: {lk}")
            driver.get(lk)
            soup_detail_page = wait_and_check(driver, ".job-detail__body", 5)
            if soup_detail_page:
                job = get_job_infor(soup_detail_page, lk)
                progress_report(layer, task_id, "on", "Lấy thông tin tuyển dụng thành công!")
                job_desc = get_job_desc(soup_detail_page)
                progress_report(layer, task_id, "on", "Lấy mô tả tuyển dụng thành công!")
                job_req = get_job_req(soup_detail_page)
                progress_report(layer, task_id, "on", "Lấy thông tin yêu cầu tuyển dụng thành công!")
                company = get_company_infor(driver, soup_detail_page)
                progress_report(layer, task_id, "on", "Lấy thông tin công ty thành công!")
                full_job = FullJob(job, company, job_desc, job_req)
                list_job_detail.append(full_job)
            else:
                progress_report(layer, task_id, "on", "Không tìm thấy element chứa thông tin. Chuyển sang link khác!")
        except Exception as ex:
            progress_report(layer, task_id, "on", f"Không thể lấy dữ liệu được từ link: {lk}. Lỗi: {str(ex)}")
            print(f"Không thể lấy dữ liệu được từ link: {lk}. Lỗi: {str(ex)}")
    return list_job_detail


def start_crawl(layer, task_id):
    driver = Driver(uc=True, headless=False)
    driver.maximize_window()
    detail_link = []
    try:
        driver.get("https://www.topcv.vn/tim-viec-lam-moi-nhat?sba=1")
        links = get_links(driver)
        if len(links) > 0:
            detail_link = get_detail_links(driver, links[:5], layer, task_id)
        #     if detail_link:
        #         for item in detail_link:
        #             print("\n-----Thông tin tuyển dụng-----\n")
        #             print(item.job.name.strip())
        #             print(item.job.link)
        #             print(item.job.address)
        #             print(item.job.date_create)
        #             print("\n-----Yêu cầu công việc-----\n")
        #             for req in item.job_req:
        #                 print(f"{req.name}: {req.field}")
        #             print("\n-----Mô tả công việc-----\n")
        #             for desc in item.job_desc:
        #                 print(f"{desc.title} -----\n{desc.decryption}")
        #             print("\n-----Mô tả công ty-----\n")
        #             print(item.company.name)
        #             print(item.company.link)
        #             print(item.company.image)
        #             print(item.company.address)
        #             print(item.company.scale)
        #             print(item.company.field)
        #             print(item.company.decryption)
        # else:
        #     print("Không có link nào cả!")
        return detail_link
    except Exception as ex:
        print(ex)
    finally:
        driver.quit()
