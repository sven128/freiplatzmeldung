import re
import json
from datetime import datetime

import requests
from bs4 import BeautifulSoup, Tag


BASE_URL = r"https://freiplatzmeldungen.de/kinder-jugendliche-und-familien.html"
URL_SCRAPE_NO_PAGE = r"https://freiplatzmeldungen.de/ajax.php?action=fmd&id=29&use=searchform_update&pageId=40"

ALL_REPORTS_PICKLE_PATH = r"/home/sven/git_repos/freiplatzmeldung/data/all_reports.pkl"


class RequestCookie:
    def __init__(self):
        self.csrf_token = None
        self.phpsessid = None

    def get(self, url: str):
        response = requests.get(url=url)
        cookies = response.cookies
        self.csrf_token = [cookie.value for cookie in cookies if cookie.name == "csrf_https-contao_csrf_token"][0]
        self.phpsessid = [cookie.value for cookie in cookies if cookie.name == "PHPSESSID"][0]


class Report:
    def __init__(self, freie_plaetze, freie_plaetze_ab, kommentarfeld, traeger, hilfeform, projektausrichtung, alter,
                 einsatzgebiet_standort, geschlecht, aktualisiert_am, href, angebotstitel):
        self.freie_plaetze = freie_plaetze
        self.freie_plaetze_ab = freie_plaetze_ab
        self.kommentarfeld = kommentarfeld
        self.traeger = traeger
        self.hilfeform = hilfeform
        self.projektausrichtung = projektausrichtung
        self.alter = alter
        self.einsatzgebiet_standort = einsatzgebiet_standort
        self.geschlecht = geschlecht
        self.aktualisiert_am = aktualisiert_am
        self.href = href
        self.angebotstitel = angebotstitel
        self.adresse = None
        self.betreuungsumfang = None
        self.gesamtkapazitaet = None
        self.geschlecht_allgemein = None
        self.kostensatz = None
        self.betriebserlaubnis = None
        self.projektleiter_in = None
        self.telefon = None
        self.telefon_mobil = None
        self.telefax = None
        self.email = None
        self.homepage = None
        self.standort = None
        self.kurzbeschreibung = None

    def add_details(self, cookie: RequestCookie):
        soup = get_soup_zusatzinfos(
            url=f"https://freiplatzmeldungen.de/{self.href}",
            path=self.href,
            cookie=cookie,
        )

        infoblock_zusatzinfos = soup.select(".infoblock.zusatzinfos")[0]
        self.betreuungsumfang = [elem.find_next("dd").text for elem in infoblock_zusatzinfos(text="Betreuungsumfang:")][0]
        self.geschlecht_allgemein = [elem.find_next("dd").text for elem in infoblock_zusatzinfos(text="Geschlecht allgemein:")][0]
        self.gesamtkapazitaet = [elem.find_next("dd").text for elem in infoblock_zusatzinfos(text="Gesamtkapazität:")][0]
        self.kostensatz = [elem.find_next("dd").text for elem in infoblock_zusatzinfos(text="Kostensatz:")][0]
        self.betriebserlaubnis = [elem.find_next("dd").text for elem in infoblock_zusatzinfos(text="Betriebserlaubnis:")][0]

        infoblock_kontaktdaten = soup.select(".infoblock.kontaktdaten")[0]
        self.projektleiter_in = [elem.find_next("dd").text for elem in infoblock_kontaktdaten(text="Projektleiter_in")][0]
        self.telefon = [elem.find_next("dd").text for elem in infoblock_kontaktdaten(text="Telefon")][0]
        self.telefon_mobil = [elem.find_next("dd").text for elem in infoblock_kontaktdaten(text="Mobile Nummer")][0]
        try:
            self.telefax = [elem.find_next("dd").text for elem in infoblock_kontaktdaten(text="Telefax")][0]
        except IndexError:
            self.telefax = ""
        self.email = [elem.find_next("dd").text for elem in infoblock_kontaktdaten(text="E-Mail")][0]

        infoblock_map = soup.select(".infoblock.map")[0]
        self.standort = infoblock_map.find_next("div", class_="margin_10_bottom").text

        infoblock_kurzbeschreibung = soup.select(".infoblock.kurzbeschreibung")[0]
        self.kurzbeschreibung = infoblock_kurzbeschreibung.find_next("dd", class_="margin_10_bottom").text

        footericons_wrapper = soup.select(".footericons_wrapper")[0]
        self.homepage = footericons_wrapper.find_next("a", class_="icon_link")["href"]

        return self


def get_cookie(url: str) -> RequestCookie:
    cookie = RequestCookie()
    cookie.get(url=url)

    return cookie


def get_soup_zusatzinfos(url: str, path: str, cookie: RequestCookie) -> BeautifulSoup:
    headers_zusatzinfos = {
        "authority": "freiplatzmeldungen.de",
        "path": path,
        "scheme": "https",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "de-DE,de;q=0.8",
        "Cookie": f"csrf_https-contao_csrf_token={cookie.csrf_token}; PHPSESSID={cookie.phpsessid}",
        "Referer": "https://freiplatzmeldungen.de/kinder-jugendliche-und-familien.html",
        "Sec-Ch-Ua": '"Chromium";v="116", "Not)A;Brand";v="24", "Brave";v="116"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": 'Linux',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Sec-Gpc": "1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"
    }

    response = requests.get(url=url, headers=headers_zusatzinfos)
    soup = BeautifulSoup(response.content)

    return soup


def get_soup_liste(url: str, cookie: RequestCookie) -> BeautifulSoup:
    headers = {
        "authority": "freiplatzmeldungen.de",
        "accept": "application/json, text/javascript, */*; q=0.01",
        "accept-language": "de-DE,de;q=0.6",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "cookie": f"csrf_https-contao_csrf_token={cookie.csrf_token}; PHPSESSID={cookie.phpsessid}",
        "origin": "https://freiplatzmeldungen.de/kinder-jugendliche-und-familien.html",
        "path": "/ajax.php?action=fmd&id=29&use=searchform_update&pageId=40&ctrl_bundesland=16",
        "referer": "https://freiplatzmeldungen.de/kinder-jugendliche-und-familien.html",
        "sec-ch-ua": '"Not/A)Brand";v="99", "Brave";v="115", "Chromium";v="115"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Linux"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "sec-gpc": "1",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest",
    }

    payload = {
        "REAL_URL": "kinder-jugendliche-und-familien.html",
        "changed_element": "ctrl_bundesland",
        "FORM_URL": "kinder-jugendliche-und-familien.html",
        "FORM_SUBMIT": "Sin_form_offer_id_",
        "REQUEST_TOKEN": "",
        "sozialer_bereich": "1",
        "country": "DE",
        "bundesland": "16",  # Berlin
        "landkreis": "0",
        "hilfeform": "",
        "projektausrichtung": "",
        "kapazitaet_sex": "",
        "search_alter": "",
        "stichwort": "",
    }

    response = requests.post(url=url, headers=headers, data=payload)

    response_json = json.loads(response.content)
    soup = BeautifulSoup(response_json["content"]["content"], "html.parser")  # .prettify()

    return soup


def create_report_from_container_elem(container_offer_halfbox: Tag) -> Report:
    angebotstitel = container_offer_halfbox.find_next("h2", class_="offertitle").text

    try:
        container_offer_halfbox.select_one(".big-number").attrs["alt"]
        freie_plaetze = -1
    except KeyError:
        freie_plaetze = int(container_offer_halfbox.select_one(".big-number").text)

    try:
        freie_plaetze_ab = datetime.strptime(
            container_offer_halfbox.find_next("span", class_="green").text, "ab %d.%m.%Y"
        )
    except AttributeError:
        freie_plaetze_ab = None

    hilfeform_combined_str = [elem.find_next("dd").text for elem in container_offer_halfbox(text="Hilfeform:")][0]
    hilfeform = [f"({hf}".replace(")", ") ") for hf in hilfeform_combined_str.strip().split("(") if hf]

    aktualisiert_am = datetime.strptime(
        container_offer_halfbox.select_one(".aktualisiert_am").text, "aktualisiert am %d.%m.%Y"
    )

    traeger = [elem.find_next("dd").text for elem in container_offer_halfbox(text="Träger:")][0]
    alter = [elem.find_next("dd").text for elem in container_offer_halfbox(text="Alter:")][0]

    einsatzgebiet_standort = [
        elem.find_next("dd") for elem in container_offer_halfbox(text=re.compile(r"^(Einsatzgebiet|Standort):$"))
    ][0].text.strip().split(",")

    projektausrichtung = [
        elem.find_next("dd") for elem in container_offer_halfbox(text="Projektausrichtung")
    ][0].text.strip().split(",")

    geschlecht = [
        elem.find_next("dd") for elem in container_offer_halfbox(text="Geschlecht:")
    ][0].text

    try:
        kommentarfeld = container_offer_halfbox.find_next("p", class_="kommentarfeld").text
    except AttributeError:
        kommentarfeld = ""

    href = container_offer_halfbox.find_next(
        "div", class_="offerlink offer_footer is_closed"
    ).find_next("a")["href"]

    report = Report(
        freie_plaetze=freie_plaetze,
        freie_plaetze_ab=freie_plaetze_ab,
        kommentarfeld=kommentarfeld,
        traeger=traeger,
        hilfeform=hilfeform,
        projektausrichtung=projektausrichtung,
        alter=alter,
        einsatzgebiet_standort=einsatzgebiet_standort,
        geschlecht=geschlecht,
        aktualisiert_am=aktualisiert_am,
        href=href,
        angebotstitel=angebotstitel
    )

    return report


def generate_reports(cookie: RequestCookie, pickle_data_after_requests: bool = False) -> list[Report]:
    url_scrape = f"{URL_SCRAPE_NO_PAGE}&page=1"
    soup_first_page = get_soup_liste(url=url_scrape, cookie=cookie)
    max_page = int(soup_first_page.find_all("a", class_="last")[0].attrs["title"].lower().replace("gehe zu seite ", ""))

    all_reports = []
    for page in range(1, 2): #max_page + 1):
        url_scrape = f"{URL_SCRAPE_NO_PAGE}&page={page}"
        soup_first_page = get_soup_liste(url=url_scrape, cookie=cookie)
        container_offer_halfboxes = soup_first_page.select(".container_offer.halfbox")

        for container_offer_halfbox in container_offer_halfboxes:
            report = create_report_from_container_elem(container_offer_halfbox)

            all_reports.append(report)
        print(f"Progress: {page:03d}/{max_page} pages done")

    return all_reports


def main():
    cookie = get_cookie(url=BASE_URL)

    all_reports = generate_reports(cookie)

    for report in all_reports:
        report.add_details(cookie=cookie)


        print()

    print()


if __name__ == "__main__":
    main()
