import csv
import datetime
from bs4 import BeautifulSoup
import requests
import logging
import os
import sys

class Apt(object):
    def __init__(self, account, unit):
        self._deed_page = None
        self._buildings_page = None
        self._owner = None
        self._account = account
        self._unit = unit
        self._deed_url = f"http://services.wakegov.com/realestate/Account.asp?id={self._account}"

    @property
    def unit(self):
        return self._unit

    @property
    def owner(self):
        if self._owner is None:
            page = self._get_deed_page()
            rows = page.find_all('tr')
            for row in rows:
                if 'Property Owner' in row.text:
                    defs = row.find_all('td')
                    assert('Property Owner' in defs[1].text)
                    # owner text is in subsequent <td> elements, until 'Use the Deeds link' <td>
                    owners = []
                    for idx in range(2, len(defs)):
                        cell_text = defs[idx].text
                        if 'Use the Deeds' in cell_text:
                            break
                        owner = cell_text.strip()
                        if len(owner):
                            owners.append(cell_text.strip())
                    self._owner = '; '.join(owners)
                    break
        assert(self._owner is not None)
        return self._owner

    @property
    def account(self):
        return self._account

    @property
    def deed_date(self):
        self._deed_date = self._get_value('Deed Date')
        if self._deed_date != None:
            format_str = '%m/%d/%Y'
            d = datetime.datetime.strptime(self._deed_date, format_str)
            return d
        return None

    @property
    def pkg_sale_price(self):
        self._pkg_sale_price = self._get_value('Pkg Sale Price')
        if self._pkg_sale_price is not None:
            val = 0
            try:
                val = int(''.join([c for c in self._pkg_sale_price if c != ',' and c != '$']))
            except:
                pass
            return val
        return None

    @property
    def heated_area(self):
        self._heated_area = self._get_value('Heated Area', Apt._get_buildings_page)
        result = 0
        try:
            result = int(''.join([c for c in str(self._heated_area) if c != ',']))
        except:
            pass
        return result

    @property
    def assessed(self):
        self._assessed = self._get_value('Total Value Assessed*')
        if self._assessed is not None:
            val = 0
            try:
                val = int(''.join([c for c in self._assessed if c != ',' and c != '$']))
            except:
                pass
            return val
        return None

    @property
    def deed_url(self):
        return self._deed_url

    def _get_deed_page(self):
        if self._deed_page is None:
            url = f"http://services.wakegov.com/realestate/Account.asp?id={self._account}"
            page = requests.get(url)
            self._deed_page = BeautifulSoup(page.content, 'html.parser')
        return self._deed_page

    def _get_buildings_page(self):
        if self._buildings_page is None:
            url = f"http://services.wakegov.com/realestate/Building.asp?id={self._account}&cd=01"
            page = requests.get(url)
            self._buildings_page = BeautifulSoup(page.content, 'html.parser')
        return self._buildings_page

    def _get_value(self, name, get_page_fn=None):
        if get_page_fn is None:
            get_page_fn = Apt._get_deed_page
        page = get_page_fn(self)
        for row in page.find_all('tr'):
            cols = row.find_all('td')
            for col_num in range(0, len(cols)):
                if cols[col_num].text == name:
                    p = cols[col_num].parent
                    cols2 = p.find_all('td')
                    value = cols2[1].text
                    return value
        return None

class Apts(object):
    def __init__(self, csv_filename):
        self._apts = None
        self._csv_filename = csv_filename
        self._get_current_csv()

    def _get_current_csv(self):
        self._prev_unit_map = {}
        try:
            with open(self._csv_filename) as csv_file:
                rdr = csv.DictReader(csv_file)
                for row in rdr:
                    unit_num = row['unit_num']
                    if unit_num in self._prev_unit_map:
                        logging.error(f"Duplicate units: {unit_num}")
                    else:
                        self._prev_unit_map[row['unit_num']] = dict(row)
        except Exception as err:
            logging.error(f"ERROR: {err}")

    @property
    def apts(self):
        if self._apts is None:
            self._apts = self.search_apts()
        return self._apts

    def search_apts(self):
        self._apts = []
        # Note: need to iterate through all the pages
        url = 'http://services.wakegov.com/realestate/AddressSearch.asp'
        #params = {'c1': '1857', 'stype': 'addr', 'stnum': '317', 'stname': 'MORGAN', 'locidList': '1857'}
        page_num = 1
        while True:
            apt_count = 0
            url = f'http://services.wakegov.com/realestate/AddressSearch.asp?stnum=317&stype=addr&stname=morgan&locidList=1857&spg={page_num}'
            page = requests.get(url)
            soup = BeautifulSoup(page.content, 'html.parser')
            # search thru all tr looking for good results
            for row in soup.find_all('tr'):
                cols = row.find_all('td')
                if len(cols) < 9 or cols[2].text != '317':
                    continue
                account = cols[1].text
                unit = cols[3].text
                if unit != '':
                    self._apts.append(Apt(account, unit))
                apt_count += 1
            if apt_count == 0:
                break
            page_num += 1
        logging.info(f"Found {len(self._apts)} units online")
        return self._apts

    def by_unit_num(self, reverse=False):
        apts = self.apts
        apts.sort(key=lambda x: x.unit, reverse=reverse)
        return apts

    def by_deed_date(self, reverse=False):
        apts = self.apts
        apts.sort(key=lambda x: x.deed_date, reverse=reverse)
        return apts

    def by_heated_area(self, reverse=False):
        apts = self.apts
        apts.sort(key=lambda x: x.heated_area, reverse=reverse)
        return apts

    def get_unit(self, unit_str):
        for apt in self.apts:
            if apt.unit == unit_str:
                return apt
        return None
    
    def check_missing(self):
        curr_unit_nums = set(map(lambda x: x.unit, list(self.apts)))
        prev_unit_nums = set(self._prev_unit_map.keys())
        self._deleted_units = prev_unit_nums - curr_unit_nums
        if len(self._deleted_units):
            logging.warning(f"Deleted: {', '.join(sorted(self._deleted_units))}")
        added = curr_unit_nums - prev_unit_nums
        if len(added):
            logging.warning(f"Added: {', '.join(sorted(added))}")

    def make_csv(self):
        with open(self._csv_filename, "w", newline='') as fp:
            field_names = ['unit_num', 'owner', 'heated_area', 'deed_date', 'pkg_sale_price', 'assessed', 'account', 'deed_url']
            writer = csv.DictWriter(fp, fieldnames=field_names, quoting=csv.QUOTE_NONNUMERIC)
            writer.writeheader()
            for apt in sorted(self.apts, key=lambda x: x.unit):
                writer.writerow({'unit_num': apt.unit, 
                    'owner': apt.owner, 'heated_area': apt.heated_area, 
                    'deed_date': apt.deed_date.strftime('%m/%d/%Y'), 'pkg_sale_price': apt.pkg_sale_price, 
                    'assessed': apt.assessed, 'account': apt.account, 'deed_url': apt.deed_url})
            #Insert old values for deleted unit (on the theory that the search failed for some reason)
            for unit_num in sorted(self._deleted_units):
                prev_dict = self._prev_unit_map[unit_num]
                writer.writerow(prev_dict)
                logging.info(f"Inserted previous info for {unit_num}")

def print_apts(apts, fn, title=''):
    with open(fn, 'w') as fp:
        print(f"\n{title}\n\n", file=fp)
        for apt in apts:
            # Improve owner field by converting newlines into semi-colons
            print("-----------------------", file=fp)
            print(f"Unit: {apt.unit}\tOwner: {apt.owner}", file=fp)
            print(f"Heated Area: {apt.heated_area}", file=fp)
            print(f"Deed Date: {apt.deed_date.strftime('%m/%d/%Y')}", file=fp)
            print(f"Pkg Sale Price: {apt.pkg_sale_price}", file=fp)
            print(f"Assessed: {apt.assessed}", file=fp)
            print(f"Account: {apt.account}", file=fp)
        fp.close()

def main():
    logging.basicConfig(filename='./reports/dawson_deeds.log', level=logging.INFO,
                        format='%(levelname)s\t%(message)s', filemode='w')
    logging.info("Start")
    csv_filename = "./reports/dawson.csv"
    ctlr = Apts(csv_filename)
    ctlr.check_missing()
    ctlr.make_csv()
    print_apts(ctlr.by_unit_num(), "./reports/by_unit.txt", "By Unit")
    print_apts(ctlr.by_deed_date(reverse=True), "./reports/by_deed.txt", "By Deed Date")
    print_apts(ctlr.by_heated_area(reverse=True), "./reports/by_heated_area.txt", "By Heated Area")
    logging.info("Done")

if __name__ == '__main__':
    main()
