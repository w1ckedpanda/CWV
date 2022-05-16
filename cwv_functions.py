import time
from datetime import date
from datetime import datetime
import requests
import re
import xml.etree.ElementTree as ET
import json
import os

today_is = date.today()
today_is = str(today_is)

def log(message):
    """

    """
    filename ='log.txt'
    moment = datetime.now()
    moment = moment.strftime("%Y-%m-%d, %H:%M:%S:%f")
    message =  f'{moment} - {message}\n'
    with open(filename, 'a') as file:
        file.write(message)

# find sitemaps URL in robots.txt
# (starndard, non-image, non-video sitemaps)
def list_website_urls_from_sitemap(website_global_url,
                            headers={'user-agent': 'wickePandaBot'}):
    """
    this function performs end-to-end listing of URLs located in all
    standard sitemaps linked in robots.txt files.
    robots.txt is accessed to find all 'Sitemap:' records
    (case insensitive) and lists all urls listed in those sitemaps.

    If robots.txt lists a sitemapindex file - based on schema - it will
    be recognized, and all of listed sitemaps will be crawled for links.

    The output is a list of URLs reported by sitemap
    NOTE:
    this functionality works only with standard sitemaps.
    Sitemap extensions, such as video sitemap, or image sitemap are not
    recognized, and will throw errors.

    URL sent to this function has to specify protocol and be a
    root-level url for your domain.
    It doesn't matter if you add trailing slash, or not.

    If needed, you can also specify headers - f.ex to indicate
    User-Agent, or Content

    example:
    website_global_url = 'https://guzdek.co/'
    headers = {'user-agent': 'wickePandaBot',
    'Content-Type': 'application/json'}
    """
    path = website_global_url.replace('://','&')
    path_list = path.split('/',1)
    path = path_list[0]
    robots_url = path.replace('&','://')+'/robots.txt'
    log(f'started to look for urls in {website_global_url} ;')
    sitemaps_found = find_sitemap_from_robots(robots_url, headers)

    all_found_urls = []

    if sitemaps_found == []:
        raise Exception('there are no sitemaps in the robots.txt file')
    else:
        for sitemap in sitemaps_found:
            status = check_if_sitemap_or_sitemapindex(sitemap, headers)
            if status == 'index':
                sitemaps_in_index = parse_sitemap_index_for_sitemaps(sitemaps_found,
                headers)
                for sitemap in sitemaps_in_index:
                    list_of_urls_in_sitemap = find_urls_in_sitemap(sitemap,
                    headers)
                    for url in list_of_urls_in_sitemap:
                        all_found_urls.append(url)
                return all_found_urls
            elif status == 'sitemap' :
                list_of_urls_in_sitemap = find_urls_in_sitemap(sitemap,
                headers)
                for url in list_of_urls_in_sitemap:
                    all_found_urls.append(url)
                return all_found_urls
            else:
                print('error while checking if sitemap or index')
                break



def find_sitemap_from_robots(robots_url, headers):
    """
    this function fetches all urls of
    'Sitemap:'
    listed in robots.txt file.

    NOTE: - you can only fetch sitemaps listing websites.
    If your robots.txt specifies video  or image sitmap - this will not
    be fetched.

    The input is a root-level url of website you want to get the
    robots.txt file from, and headers that you want to send along
    with the GET request.

    The website url has to specify protocol (http:// or https://)

    example:
    url = 'https://guzdek.co/robots.txt'
    headers = {'user-agent': 'wickePandaBot'}
    """
    robots_response = requests.get(robots_url,headers = headers)
    robots_txt = robots_response.text
    list_of_sitemaps = re.findall(r"sitemap.*", robots_txt, flags=re.IGNORECASE)
    sitemaps_found = []
    for i, sitemap in enumerate(list_of_sitemaps):
        potential_sitemap_url = list_of_sitemaps[i].replace('Sitemap:','')
        potential_sitemap_url = potential_sitemap_url.replace('Sitemap :','')
        potential_sitemap_url = potential_sitemap_url.strip()
        potential_sitemap_url = potential_sitemap_url.rstrip()
        sitemaps_found.append(potential_sitemap_url)
    amount = len(sitemaps_found)
    log (f'found {amount} addresses within robots.txt ;')
    print(f'found {amount} addresses within robots.txt ;')
    return sitemaps_found

#check if a link is a sitemap or a sitemap index
def check_if_sitemap_or_sitemapindex(url, headers):
    """
    this function checks if url provided is a sitemap, or sitemapindex.
    URL sent to this function has to specify protocol and be an .xml

    example:
    url = 'https://guzdek.co/robots.txt'
    headers = {'user-agent': 'wickePandaBot'}
    """
    response_to_be_checked = requests.get(url, headers=headers)
    response_to_be_checked.encoding ='UTF-8'
    response_root = ET.fromstring(response_to_be_checked.text)
    root_tag = response_root.tag
    if root_tag == '{http://www.sitemaps.org/schemas/sitemap/0.9}sitemapindex':
        log(f'{url} is a sitemapindex;')
        print(f'{url} is a sitemapindex;')
        return('index')
    elif root_tag == '{http://www.sitemaps.org/schemas/sitemap/0.9}urlset':
        log(f'{url} is a sitemap;')
        print(f'{url} is a sitemap;')
        return('sitemap')
    else:
        log(f'unable to check if specified path is sitemapindex or sitemap;')
        return('Unable to check if specified path is sitemapindex or sitemap')


#fetch sitemapindex and parse its xml looking for single sitemaps
def parse_sitemap_index_for_sitemaps(sitemaps_found_list, headers):
    """
    this function parses all identified sitemapindex files and
    extracts urls to single sitemap files.
    URL sent to this function has to specify protocol and be an .xml

    example:
    url = 'https://guzdek.co/sitemap.xml'
    headers = {'user-agent': 'wickePandaBot'}
    """
    sitemaps_in_index =[]
    for sitemap in sitemaps_found_list:
        sitemap_index = requests.get(sitemap, headers=headers)
        sitemap_index.encoding ='UTF-8'
        sitemap_index_root = ET.fromstring(sitemap_index.text)
        for sitemap_url in sitemap_index_root.itertext():
            if sitemap_url[0:4] == "http" and sitemap_url[-4:] =='.xml':
                sitemaps_in_index.append(sitemap_url)
    amount = len(sitemaps_in_index)
    log(f'found {amount} sitemaps in sitemapindex;')
    print(f'found {amount} sitemaps in sitemapindex;')
    return sitemaps_in_index

#iterate through single sitemaps to fetch website URLs
def find_urls_in_sitemap(single_sitemap_url, headers):
    """
    this function checks all identified sitemaps, and lists all URLs
    found in them.
    URL sent to this function has to specify protocol and be an .xml

    example:
    url = 'https://guzdek.co/sitemap-part_1.xml'
    headers = {'user-agent': 'wickePandaBot'}
    """
    single_sitemap = requests.get(single_sitemap_url, headers=headers)
    single_sitemap.encoding ='UTF-8'
    single_sitemap_root = ET.fromstring(single_sitemap.text)

    urls_in_single_sitemap = []

    for i, url in enumerate(single_sitemap_root.itertext()):
        if url[0:4] == "http":
            urls_in_single_sitemap.append(url)
    amount = len(urls_in_single_sitemap)
    log(f'{amount} urls identified in sitemap: {single_sitemap_url} ;')
    print(f'{amount} urls identified in sitemap: {single_sitemap_url} ;')
    return urls_in_single_sitemap



###
### End of url extraction from sitemaps logic
###



###
### Logic checking if a URL is present in CrUX API. If so, add url to a
### list in csv for processing with next jobs. Additionally create first
### output for all ALL_FORM_FACTORS.
###


def request_and_parse(url, api_key, device, header, today):
    data = {"url": url, "formFactor": device }
    r = requests.post(f'https://chromeuxreport.googleapis.com/v1/records:queryRecord?key={api_key}', headers = header, json = data)
    time.sleep(0.2)
    response_code = r.status_code
    response_body = r.text
    if response_code == 200:
        json_content = json.loads(response_body)
        normalized_url = ''
        cls_good = ''
        cls_needs_improv = ''
        cls_bad = ''
        cls_p75 = ''
        exitnp_good = ''
        exitnp_needs_improv = ''
        exitnp_bad = ''
        exitnp_p75 = ''
        exttfb_good = ''
        exttfb_needs_improv = ''
        exttfb_bad = ''
        exttfb_p75 = ''
        fcp_good = ''
        fcp_needs_improv = ''
        fcp_bad = ''
        fcp_p75 = ''
        fid_good = ''
        fid_needs_improv = ''
        fid_bad = ''
        fid_p75 = ''
        lcp_good = ''
        lcp_needs_improv = ''
        lcp_bad = ''
        lcp_p75 = ''
        status = ''
        details =''
        try:
             if 'cumulative_layout_shift' in json_content['record']['metrics']:
                cls_good = str(json_content['record']['metrics']['cumulative_layout_shift']['histogram'][0]['density'])
                cls_needs_improv = str(json_content['record']['metrics']['cumulative_layout_shift']['histogram'][1]['density'])
                cls_bad = str(json_content['record']['metrics']['cumulative_layout_shift']['histogram'][2]['density'])
                cls_p75 = str(json_content['record']['metrics']['cumulative_layout_shift']['percentiles']['p75'])
        except KeyError as err0:
            status = 'error'
            details = f'CLS parsing error: {err0}. '
            pass

        try:
            if 'experimental_interaction_to_next_paint' in json_content['record']['metrics']:
                exitnp_good = str(json_content['record']['metrics']['experimental_interaction_to_next_paint']['histogram'][0]['density'])
                exitnp_needs_improv = str(json_content['record']['metrics']['experimental_interaction_to_next_paint']['histogram'][1]['density'])
                exitnp_bad = str(json_content['record']['metrics']['experimental_interaction_to_next_paint']['histogram'][2]['density'])
                exitnp_p75 = str(json_content['record']['metrics']['experimental_interaction_to_next_paint']['percentiles']['p75'])
        except KeyError as err1:
            status = 'error'
            details = f'Ex ITNP parsing error: {err1}. '
            pass

        try:
            if 'experimental_time_to_first_byte' in json_content['record']['metrics']:
                exttfb_good = str(json_content['record']['metrics']['experimental_time_to_first_byte']['histogram'][0]['density'])
                exttfb_needs_improv = str(json_content['record']['metrics']['experimental_time_to_first_byte']['histogram'][1]['density'])
                exttfb_bad = str(json_content['record']['metrics']['experimental_time_to_first_byte']['histogram'][2]['density'])
                exttfb_p75 = str(json_content['record']['metrics']['experimental_time_to_first_byte']['percentiles']['p75'])
        except KeyError as err2:
            status = 'error'
            details = f'Ex TTFB parsing error: {err2}. '
            pass

        try:
            if 'first_contentful_paint' in json_content['record']['metrics']:
                fcp_good = str(json_content['record']['metrics']['first_contentful_paint']['histogram'][0]['density'])
                fcp_needs_improv = str(json_content['record']['metrics']['first_contentful_paint']['histogram'][0]['density'])
                fcp_bad = str(json_content['record']['metrics']['first_contentful_paint']['histogram'][0]['density'])
                fcp_p75 = str(json_content['record']['metrics']['first_contentful_paint']['percentiles']['p75'])
        except KeyError as err3:
            status = 'error'
            details = f'FCP parsing error: {err3}. '
            pass

        try:
            if 'first_input_delay' in json_content['record']['metrics']:
                fid_good = str(json_content['record']['metrics']['first_input_delay']['histogram'][0]['density'])
                fid_needs_improv = str(json_content['record']['metrics']['first_input_delay']['histogram'][1]['density'])
                fid_bad = str(json_content['record']['metrics']['first_input_delay']['histogram'][2]['density'])
                fid_p75 = str(json_content['record']['metrics']['first_input_delay']['percentiles']['p75'])
        except KeyError as err4:
            status = 'error'
            details = f'FID parsing error: {err4}. '
            # return ['error', f'{url};err FID; {err4}; {response_body}']
            pass

        try:
            if 'largest_contentful_paint' in json_content['record']['metrics']:
                lcp_good = str(json_content['record']['metrics']['largest_contentful_paint']['histogram'][0]['density'])
                lcp_needs_improv = str(json_content['record']['metrics']['largest_contentful_paint']['histogram'][1]['density'])
                lcp_bad = str(json_content['record']['metrics']['largest_contentful_paint']['histogram'][2]['density'])
                lcp_p75 = str(json_content['record']['metrics']['largest_contentful_paint']['percentiles']['p75'])
        except KeyError as err5:
            status = 'error'
            details = f'LCP parsing error: {err5}. '
            # return ['error', f'{url};err LCP; {err5}; {response_body}']
            pass

        if 'urlNormalizationDetails' in json_content:
            normalized_url = json_content['urlNormalizationDetails']['normalizedUrl']

        line = (today +';'+ device +';'+ domain +';'+ url +';'+
        normalized_url +';'+ ' ' +';'+
        cls_good +';'+ cls_needs_improv +';'+ cls_bad +';'+ cls_p75 +';'+
        exitnp_good +';'+ exitnp_needs_improv +';'+ exitnp_bad +';'+ exitnp_p75 +';'+
        exttfb_good +';'+ exttfb_needs_improv +';'+ exttfb_bad +';'+ exttfb_p75 +';'+
        fcp_good +';'+fcp_needs_improv +';'+fcp_bad+';'+ fcp_p75 +';'+
        fid_good +';'+ fid_needs_improv +';'+ fid_bad+';'+ fid_p75 +';'+
        lcp_good +';'+ lcp_needs_improv +';'+ lcp_bad +';'+ lcp_p75)

        return [status, details, line,url, response_body]
    else:
        return ''

def check_if_urls_in_crux(list_of_urls, api_key, device='ALL_FORM_FACTORS'):
    domain = list_of_urls[0]
    domain = domain.replace('://','&')
    domain = domain.split('/',1)
    domain = domain[0].split('&',1)
    domain = domain[1]
    today = date.today()
    today = str(today)

    init_amount = len(list_of_urls)
    log(f'commencing CrUX API querying for {domain}. {init_amount} urls will be checked;')
    live_list = []
    initial_report_list = []
    err_lst = []

    header = {"Content-Type": "application/json"}
    working_dir = os.getcwd()

    for i, url in enumerate(list_of_urls):
        resp= request_and_parse (url, api_key, device, header, today_is )
        if resp == '':
            pass
        elif resp[0] == 'error':
            err_lst.append(resp[3] + ';' + resp[1] + ';' + resp[4])
            initial_report_list.append(resp[2])
            print(f'url {i} - {url} - found in CrUX - issues parsing some values')
        else:
            line = resp[2]
            live_list.append(url)
            initial_report_list.append(line)
            print(f'url {i} - {url} - found in CrUX')


    path_output = working_dir+'\\output'
    path_live_list = working_dir+'\\output\\live-list'
    path_live_list_domain = working_dir+'\\output\\live-list\\'+domain
    path_report = working_dir+'\\output\\report'
    if os.access(path_output, os.F_OK) == False: os.mkdir(path_output)
    if os.access(path_live_list, os.F_OK) == False: os.mkdir(path_live_list)
    if os.access(path_live_list_domain, os.F_OK) == False: os.mkdir(path_live_list_domain)
    if os.access(path_report, os.F_OK) == False: os.mkdir(path_report)
    path_live_file = working_dir+'\\output\\live-list\\'+domain+'\\'+today_is+'-'+domain+'-live-list.csv'
    path_report_file =  working_dir+'\\output\\report\\cwv-output.csv'
    chk = True
    if os.access(path_report_file, os.F_OK) == False: chk = False

    amount = len(live_list)
    amount_err = len(err_lst)
    log(f'identified {amount} live urls, of which {amount_err} errors within {domain};')

    with open(path_live_file,'a') as lv:
        for element in live_list:
            lv.write(element+'\n')
        log(f'list of urls present in CrUX stored at {path_live_file} ;' )

    with open(f'{path_report}\err-{today_is}-{domain}.txt','a') as lv:
        for element in err_lst:
            lv.write(element+'\n')
        log(f'error report stored at {path_report}\err-{today_is}-{domain}.txt ;' )

    with open(path_report_file,'a') as rp:
        if chk == False:
            rp.write(f'date;device;domain;url;normalized_url;CMS page type;cls_good;cls_needs_improv;cls_bad;cls_p75;exitnp_good;exitnp_needs_improv;exitnp_bad;exitnp_p75;exttfb_good;exttfb_needs_improv;exttfb_bad;exttfb_p75;fcp_good;fcp_needs_improv;fcp_bad;fcp_p75;fid_good;fid_needs_improv;fid_bad;fid_p75;lcp_good;lcp_needs_improv;lcp_bad;lcp_p75\n')
            log(f'new report file created at {path_report_file}. Headers added;')
        for line in initial_report_list:
            rp.write(line+'\n')
    log(f'Processing {domain} finished. Data added to report file.')
    print('Processing ' + domain + ' finished')



def check_file_with_latest_links_in_crux(dom):
    """
    """
    r = os.getcwd()
    p = '\\output\\live-list\\'
    track = r+p+dom
    locations =[]
    for r, d, f in os.walk(track):
        for file in f:
            if '.csv' in file:
                locations.append(os.path.join(r, file))
    locations.sort()
    return locations[-1]
    log('the latest file containing live links in CrUX identified: ' + locations[-1])

def get_domains (filename):
    working_dir = os.getcwd()
    path=working_dir+'\\'+filename
    domains_list = []
    with open(path,'r') as domain:
        for host in domain:
            host = host.replace('\n','')
            domains_list.append(host)
    amount = len(domains_list)
    log(f'identified {amount} domains')
    return domains_list

def iter_urls_by_crux(domain, api_key, device='ALL_FORM_FACTORS'):
    """
    domain - as stated in output/live-list/{DOMAIN}
    """
    working_dir = os.getcwd()
    path_report = working_dir+'\\output\\report\\cwv-output.csv'

    latest_in_crux_file = check_file_with_latest_links_in_crux(domain)

    report_list = []
    err_lst = []

    header = {"Content-Type": "application/json"}

    with open(latest_in_crux_file,'r') as lv:
        for i, url in enumerate(lv):
            url = url.replace('\n','')
            resp= request_and_parse (url, api_key, device, header, today_is )
            if resp == '':
                pass
            elif resp[0] == 'error':
                report_list.append(resp[2])
                print(f'url {i} - {url} - found in CrUX - issues parsing some values')
            else:
                line = resp[2]
                report_list.append(resp[2])
                print(f'url {i} - {url} - found in CrUX')

    amount = len(report_list)
    amount_err = len(err_lst)

    chk = True
    if os.access(path_report, os.F_OK) == False: chk = False
    with open(path_report,'a') as rp:
        if chk == False:
            raise Exception('first - run check_if_url_in_crux')
        for line in report_list:
            rp.write(line+'\n')

    amount = len(report_list)
    amount_err = len(err_lst)
    log(f'{device} CrUX data was requested for {amount} of found live urls from {domain}. {amount_err} of that resulted with malformed API responses ;')
    log(f'Processing {domain} finished. Data added to report file.')







#check for statistics of single live URLs per domain
#  you can get you CrUX API Key from here:
#https://developers.google.com/web/tools/chrome-user-experience-report/api/guides/getting-started#APIKey

##### data for the job
cwv_devices = ['ALL_FORM_FACTORS', 'DESKTOP', 'PHONE', 'TABLET']
api_key=''
headers = {'user-agent': 'wickePandaBot'}


# # download CWV data - starting from sitemaps of websites listed in domains.txt file
domains = get_domains('domains.txt')
for domain in domains:
    pages_in_domain = list_website_urls_from_sitemap(domain, headers=headers)
    check_if_urls_in_crux(pages_in_domain, api_key, device='ALL_FORM_FACTORS')
    dom = domain.split('://',1)
    dom=dom[-1].replace('/','')
    iter_urls_by_crux(dom, api_key, device='PHONE')
    iter_urls_by_crux(dom, api_key, device='DESKTOP')
