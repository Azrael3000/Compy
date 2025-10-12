import logging
import re
from collections import namedtuple
from packaging.version import Version

try:
    import country_converter
    assert Version(country_converter.version.__version__) >= Version("1.2")
except ImportError:
    print("Could not find country_converter. Install with 'pip3 install country_converter'")
    exit(-1)
except AssertionError:
    print("country_converter found with version", country_converter.version.__version__, "but version >= 1.2 required, please update it.")
    exit(-1)

try:
    import requests
except ImportError:
    print("Could not find requests. Install with 'pip3 install requests'")
    exit(-1)

NR = namedtuple("NR", ["federation", "country", "cls", "gender", "discipline"])

def convDay(day):
    try:
        day = int(day)
        year = day//10000
        month = (day-year*10000)//100
        day = day%100
        return str(year).zfill(4) + "-" + str(month).zfill(2) + "-" + str(day).zfill(2)
    except ValueError:
        if '-' in day:
            day = day.split('-')
            if len(day) == 3:
                return int(day[0])*10000 + int(day[1])*100 + int(day[2])
    return None

def convTime(time):
    try:
        time = int(time)
        hour = time//100
        time = time%100
        return str(hour).zfill(2) + ":" + str(time).zfill(2)
    except ValueError:
        if ':' in time:
            time = time.split(':')
            if len(time) == 2:
                return int(time[0])*100 + int(time[1])
    return None

def getNationalRecordsAida():
    breakpoint()
    empty_req = requests.post('https://www.aidainternational.org/public_pages/all_national_records.php', data={})
    html = empty_req.text
    start = html.find('id="nationality"')
    start = html.find('<option', start)
    end = html.find('</select>', start)
    nationalities = str.splitlines(html[start:end])
    p = re.compile("<option.*value=\"([0-9]+)\">(.*)</option>")
    country_value_map = {}
    cc = country_converter.CountryConverter()
    for n in nationalities:
        result = p.search(n)
        if result:
            country_value_map[cc.convert(result.group(2), to = 'IOC')] = result.group(1)
    nrs = {}
    for c_ioc, c_str in country_value_map.items():
        data = {
            'nationality': str(c_str),
            'discipline': '',
            'gender': '',
            'apply': ''
        }
        req = requests.post('https://www.aidainternational.org/public_pages/all_national_records.php', data=data)
        html = req.text
        start = html.find('<tbody>')
        start = html.find('<tr>', start)
        end = html.find('</tbody>', start)
        entries = str.splitlines(html[start:end])[:-1]
        p = re.compile("<td>(.*)</td>")
        for i in range(int(len(entries)/10)):
            gender = p.search(entries[i*10 + 2]).group(1)
            dis = p.search(entries[i*10 + 3]).group(1)
            res_str = p.search(entries[i*10 + 4]).group(1)
            result = 0.
            if dis == "STA":
                p_dis = re.compile("([0-9]+):([0-9][0-9])")
                res_re = p_dis.search(res_str)
                result = float(res_re.group(1))*60.0 + float(res_re.group(2))
            else:
                p_dis = re.compile("[0-9]+")
                result = float(p_dis.search(res_str).group(0))
            points = float(p.search(entries[i*10 + 6]).group(1))
            nrs[self.NR(federation="aida", country=c_ioc, cls="", gender=gender, discipline=dis)] = result
    logging.debug("National records:")
    logging.debug("Country | Gender | Discipline | Result | Points")
    for key, val in nrs.items():
        logging.debug("%s | %s | %s | %s | %d", key.country, key.gender, key.discipline, val)
    logging.debug("-----------------")
    return nrs
