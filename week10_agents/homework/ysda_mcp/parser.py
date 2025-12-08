import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv


def get_soup_from_lk(lk_url: str) -> BeautifulSoup:
    load_dotenv()
    lk_cookie = os.getenv("LK_SESSION_COOKIE")

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; parser/1.0)"
    }

    session = requests.Session()
    if lk_cookie:
        # session.cookies.set("sessionid", lk_cookie, domain="lk.dataschool.yandex.ru")
        session.cookies.set('Session_id', lk_cookie, domain='.yandex.ru')

    resp = session.get(lk_url, headers=headers, timeout=10)
    resp.raise_for_status()
    html = resp.text

    soup = BeautifulSoup(html, "html.parser")

    return soup

def parse_tasks() -> list[dict[str, str]]:
    soup = get_soup_from_lk("https://lk.dataschool.yandex.ru/learning/assignments/")

    try:
        open_tasks_table = soup.find("h3", string="Открытые задания").find_next("table")
    except AttributeError:
        raise RuntimeError("Could not find the open tasks table on the page. Check your cookie")

    tasks = []

    rows = open_tasks_table.find_all("tr")[1:]  # Skip the first header row

    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 5:  # Skip if not enough cells
            continue
        
        date_elem = cells[0].find("div", class_="assignment-date")
        date_text = date_elem.get_text(strip=True, separator=" ") if date_elem else ""
        
        assignment_elem = cells[1].find("a")
        assignment_name = assignment_elem.get_text(strip=True) if assignment_elem else ""
        
        course_elem = cells[2].find("a")
        course_name = course_elem.get_text(strip=True) if course_elem else ""
        
        status_elem = cells[3].find("span", class_="badge")
        status = status_elem.get_text(strip=True) if status_elem else ""
        
        format_type = cells[4].get_text(strip=True) if len(cells) > 4 else ""
        
        if assignment_name and course_name:
            tasks.append({
                "course": course_name,
                "assignment": assignment_name,
                "deadline": date_text,
                "status": status,
                "format": format_type
            })

    return tasks


def parse_lectures() -> list[dict[str, str]]:
    soup = get_soup_from_lk("https://lk.dataschool.yandex.ru/learning/timetable/")

    classes = []

    for table in soup.select("table.table.timetable"):
        date = table.find_previous("h4").get_text(strip=True)

        rows = table.find_all("tr")[1:]

        for tr in rows:
            tds = tr.find_all("td")

            if len(tds) < 5:
                continue

            time = tds[0].get_text(strip=True)

            title_link = tds[1].find("a")
            title = title_link.get_text(strip=True) if title_link else tds[1].get_text(strip=True)
            title_url = title_link["href"] if title_link and title_link.has_attr("href") else None

            course_link = tds[2].find("a")
            course = course_link.get_text(strip=True) if course_link else tds[2].get_text(strip=True)
            course_url = course_link["href"] if course_link and course_link.has_attr("href") else None

            place = tds[3].get_text(strip=True)

            badge = tds[4].find("span", class_="badge")
            cls_type = badge.get_text(strip=True) if badge else ""
            badge_classes = badge.get("class", []) if badge else []
            kind = next((c for c in badge_classes if c not in ("badge",)), None)

            classes.append(
                {
                    "date": date,            # e.g. "Четверг, 27 ноября 2025"
                    "time": time,            # e.g. "18:00–19:30"
                    "title": title,          # e.g. "Лекция"
                    "title_url": title_url,  # e.g. "/courses/.../classes/14202/"
                    "course": course,        # e.g. "Компьютерное зрение"
                    "course_url": course_url,
                    "place": place,          # e.g. "Онлайн, ШАД, Москва"
                    "type": cls_type,        # e.g. "Лекция" / "Семинар"
                    "kind": kind,            # e.g. "lecture" / "seminar"
                }
            )

    # for c in classes:
    #     print(c)
        
    return classes
