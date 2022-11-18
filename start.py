import re
import os
import sqlite3 as db
import pandas as pd
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import ElementClickInterceptedException, UnexpectedAlertPresentException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import Chrome
import random
from nordvpn_connect import initialize_vpn, rotate_VPN
import undetected_chromedriver._compat as uc
# import logging
# logging.basicConfig(filename='app.log', level=logging.INFO, filemode='w',
#                     format='%(name)s - %(levelname)s - %(message)s')


dbFile = os.environ.get('dbFile')
EMAIL = os.environ.get('EMAIL')
STATE = os.environ.get('STATE')


uc.install()


options = uc.ChromeOptions()
# prefs = {"profile.managed_default_content_settings.images": 2,
#          "profile.default_content_setting_values.notifications": 2,
#          "profile.managed_default_content_settings.stylesheets": 2,
#          "profile.managed_default_content_settings.cookies": 2,
#          "profile.managed_default_content_settings.javascript": 1,
#          "profile.managed_default_content_settings.plugins": 1,
#          "profile.managed_default_content_settings.popups": 2,
#          "profile.managed_default_content_settings.geolocation": 2,
#          "profile.managed_default_content_settings.media_stream": 2,
#          }
# options.add_experimental_option("prefs", prefs)
# options.add_argument('--no-sandbox')
# options.add_argument('--disable-dev-shm-usage')
options.add_argument('--headless')  # comment this like to enable UI


def checkDB():
    with db.connect(dbFile) as conn:
        conn.execute("""
                     CREATE TABLE IF NOT EXISTS voters (
                     id INTEGER PRIMARY KEY AUTOINCREMENT
                     , sn VARCHAR(10)
                     , page VARCHAR(10)
                     , voter_vin VARCHAR(70)
                     , voter_name VARCHAR(20)
                     , voter_dob VARCHAR(70)
                     , voter_gender VARCHAR(5)
                     , voter_img VARCHAR(100)
                     , pu VARCHAR(20)
                     , ward VARCHAR(70)
                     , lga VARCHAR(70)
                     , delim VARCHAR(70)
                     , record_count VARCHAR(70)
                     , status VARCHAR(10)
                     , pu_done VARCHAR(10)
                     , ward_done VARCHAR(10)
                     , lga_done VARCHAR(10)
                     , pu_pop VARCHAR(10)
                     , ward_pop VARCHAR(10)
                     , lga_pop VARCHAR(10)
                     , UNIQUE (sn, pu));
                     """)
        df = pd.read_sql('SELECT * from voters', conn)
    return df


def update(sn, page, voter_vin, voter_name, voter_dob, voter_gender, voter_img, pu, ward, lga, delim, record_count):
    with db.connect(dbFile) as conn:
        sql = f'''
            INSERT OR REPLACE INTO voters (sn, page, voter_vin, voter_name, voter_dob, voter_gender, voter_img, pu, ward, lga, delim, record_count) 
            VALUES (
                "{sn}"
                , "{page}"
                , "{voter_vin}"
                , "{voter_name}"
                , "{voter_dob}"
                , "{voter_gender}"
                , "{voter_img}"
                , "{pu}"
                , "{ward}"
                , "{lga}"
                , "{delim}"
                , "{record_count}"
            )
        '''
        conn.execute(sql)


def login():
    browser.find_element('id', 'LoginEmail').send_keys(EMAIL)
    browser.find_element('id', 'LoginPassword').send_keys('secure@123')
    browser.find_element('id', 'LoginPassword').send_keys(Keys.ENTER)
    browser.get('https://cvr.inecnigeria.org/VotersRegister')


def recursive():
    global timenow
    try:
        browser.refresh()
        browser.find_element('tag name', 'body').send_keys(
            Keys.CONTROL+Keys.HOME)
        if not(browser.find_element('id', 'VoterRegisterStateId').is_displayed()):
            browser.find_element('id', 'showSidebarButton').click()
        states = browser.find_element('id', 'VoterRegisterStateId')
        states_list = states.find_elements('xpath', 'option')
        for index, state in enumerate(states_list):
            state = browser.find_element('id', 'VoterRegisterStateId').find_elements(
                'xpath', 'option')[1:][index+1]
            state_text = state.text
            check = checkDB()
            state_pop = 0
            if state_text not in [STATE]:
                continue
            Select(browser.find_element('id', 'VoterRegisterStateId')
                   ).select_by_visible_text(state_text)
            lgas = browser.find_element('id', 'VoterRegisterLocalGovernmentId')
            lga_list = []
            time.sleep(1)
            lgas_list = lgas.find_elements('xpath', 'option')
            for index, _ in enumerate(lgas_list):
                lga = browser.find_element('id', 'VoterRegisterLocalGovernmentId').find_elements(
                    'xpath', 'option')[1:][index]
                lga_text = lga.text
                check = checkDB()
                if check[(check.lga == lga_text) & (check.lga_done == 'done')].any().any() and len(check[(check.lga == lga_text) & (check.lga_done == 'done')]) != 0:
                    continue
                if (len(check.loc[(check.lga == lga_text), 'lga_pop']) != 0) and (check.loc[(check.lga == lga_text), 'lga_pop'].any()):
                    lga_pop = int(
                        check.loc[(check.lga == lga_text), 'lga_pop'].iloc[0])
                else:
                    lga_pop = 0
                # check if ward attempted
                if len(check[(check.lga_done == 'done') & (check.lga == lga_text)]) != 0:
                    # check if done
                    if (len(check[(check.lga == lga_text)]) == check['lga_pop']).any():
                        lga_pop = check.loc[(
                            check.lga == lga_text), 'lga_pop'].count()
                        continue
                Select(browser.find_element(
                    'id', 'VoterRegisterLocalGovernmentId')).select_by_visible_text(lga_text)
                time.sleep(0.25)
                wards = browser.find_element(
                    'id', 'VoterRegisterRegistrationAreaId')
                ward_list = []
                wards_list = wards.find_elements('xpath', 'option')[1:]
                for index, _ in enumerate(wards_list):
                    ward = browser.find_element('id', 'VoterRegisterRegistrationAreaId').find_elements(
                        'xpath', 'option')[1:][index]
                    ward_text = ward.text
                    check = checkDB()
                    if check[(check.ward == ward_text) & (check.ward_done == 'done')].any().any() and len(check[(check.ward == ward_text) & (check.ward_done == 'done')]) != 0:
                        continue
                    if (len(check.loc[(check.ward == ward_text) & (check.lga == lga_text), 'ward_pop']) != 0) and (check.loc[(check.ward == ward_text) & (check.lga == lga_text), 'ward_pop'].any()):
                        ward_pop = int(check.loc[(check.ward == ward_text) & (
                            check.lga == lga_text), 'ward_pop'].iloc[0])
                    else:
                        ward_pop = 0
                    # check if ward attempted
                    if len(check[(check.ward_done == 'done') & (check.lga == lga_text) & (check.ward == ward_text)]) != 0:
                        # check if done
                        if (len(check[(check.ward_done == 'done') & (check.lga == lga_text) & (check.ward == ward_text)]) == check['ward_pop']).any():
                            ward_pop = check.loc[(check.ward == ward_text) & (
                                check.lga == lga_text), 'ward_pop'].count()
                            continue
                    Select(browser.find_element(
                        'id', 'VoterRegisterRegistrationAreaId')).select_by_visible_text(ward_text)
                    time.sleep(0.5)
                    try:
                        pus = browser.find_element(
                            'id', 'VoterRegisterPollingUnitId')
                        pu_list = [{pu.text: pu.get_attribute(
                            'value')} for pu in pus.find_elements('xpath', 'option')[1:]]
                        assert len(pu_list) != 0
                    except:
                        time.sleep(1)
                        pus = browser.find_element(
                            'id', 'VoterRegisterPollingUnitId')
                        pu_list = [{pu.text: pu.get_attribute(
                            'value')} for pu in pus.find_elements('xpath', 'option')[1:]]
                        assert len(pu_list) != 0
                        # map pus to ward
                    pus_list = pus.find_elements('xpath', 'option')[1:]
                    for index, _ in enumerate(pus_list):
                        pu = browser.find_element('id', 'VoterRegisterPollingUnitId').find_elements(
                            'xpath', 'option')[1:][index]
                        pu_text = pu.text
                        if (check.loc[(check.pu == pu_text) & (check.status == 'done'), 'pu_done'] == 'done').all() and len(check.loc[(check.pu == pu_text) & (check.status == 'done'), 'pu_done'] == 'done') != 0:
                            pu_pop = (check.loc[(check.pu == pu_text) & (
                                check['status'] == 'done'), 'pu_done'] == 'done').count()
                            with db.connect(dbFile) as conn:
                                conn.execute(f"""
                                UPDATE voters
                                SET status = 'done', pu_pop = "{pu_pop}"
                                WHERE pu = "{pu_text}" AND lga = "{lga_text}" AND ward = "{ward_text}"
                                """)
                            continue
                        Select(browser.find_element(
                            'id', 'VoterRegisterPollingUnitId')).select_by_visible_text(pu_text)
                        time.sleep(1)
                        try:
                            browser.switch_to.frame(
                                browser.find_element('tag name', 'iframe'))
                            while browser.find_element('id', 'recaptcha-anchor').get_attribute('aria-checked') == 'false':
                                browser.find_element(
                                    'class name', 'recaptcha-checkbox-border').click()
                                time.sleep(3)
                            browser.switch_to.parent_frame()
                            browser.find_element(
                                'id', 'VoterRegisterIndexForm').submit()
                        except (ElementClickInterceptedException, UnexpectedAlertPresentException):
                            browser.refresh()
                            if int(time.time() - timenow) > 60:
                                vpn_settings = initialize_vpn(random.choice(
                                    ['Canada', 'France', 'United Kingdom', 'United States']))
                                rotate_VPN(vpn_settings)
                            time.sleep(5)
                            browser.switch_to.frame(
                                browser.find_element('tag name', 'iframe'))
                            while browser.find_element('id', 'recaptcha-anchor').get_attribute('aria-checked') == 'false':
                                browser.find_element(
                                    'class name', 'recaptcha-checkbox-border').click()
                                time.sleep(2)
                            browser.switch_to.parent_frame()
                            Select(browser.find_element(
                                'id', 'VoterRegisterStateId')).select_by_visible_text(state_text)
                            Select(browser.find_element(
                                'id', 'VoterRegisterLocalGovernmentId')).select_by_visible_text(lga_text)
                            Select(browser.find_element(
                                'id', 'VoterRegisterRegistrationAreaId')).select_by_visible_text(ward_text)
                            Select(browser.find_element(
                                'id', 'VoterRegisterPollingUnitId')).select_by_visible_text(pu_text)
                            browser.find_element(
                                'id', 'VoterRegisterIndexForm').submit()
                        time.sleep(1)
                        try:
                            href = browser.find_element(
                                'xpath', '//*[contains(@href, "voters_register/index/display/page")]').find_element('xpath', '..').text
                            current_page, last_page = re.findall(
                                '\d+ of \d+', href)[0].split(' of ')
                            current_page = int(current_page)
                            last_page = int(last_page)
                        except:
                            current_page = 1
                            last_page = 1
                        page_lga = browser.find_element(
                            'xpath', '//*[contains(@id, "table")]/tbody/tr[1]/td[1]').text.split('\n')[-1]
                        assert page_lga == lga_text
                        page_pu = browser.find_element(
                            'xpath', '//*[contains(@id, "table")]/tbody/tr[1]/td[2]').text.split('\n')[-1]
                        assert page_pu == pu_text
                        page_ward = browser.find_element(
                            'xpath', '//*[contains(@id, "table")]/tbody/tr[2]/td[1]').text.split('\n')[-1]
                        assert page_ward == ward_text
                        page_delim = browser.find_element(
                            'xpath', '//*[contains(@id, "table")]/tbody/tr[2]/td[2]').text.split('\n')[-1]
                        page_record_count = browser.find_element(
                            'xpath', '//*[contains(@id, "table")]/tbody/tr[2]/td[3]').text.split('\n')[-1]

                        # PROCESS PAGE
                        for page in range(1, last_page+1):
                            # Check if page has already been added to db
                            try:
                                check = checkDB()
                                if (check.loc[(check.page.astype(int) == page) & (check.pu == pu_text), 'status'] == 'done').all() and len(check.loc[(check.page.astype(int) == page) & (check.pu == pu_text), 'status'] == 'done') != 0:
                                    continue
                            except:
                                pass
                            link = f"https://cvr.inecnigeria.org/voters_register/index/display/page:{page}"
                            browser.get(link)
                            for element in browser.find_elements('class name', 'voter'):
                                voter = element.text
                                voter_img = element.find_element(
                                    'class name', 'img-fluids').get_attribute('src')
                                sn, voter_name, _, voter_vin, _, voter_dob_gender = voter.split(
                                    '\n')
                                sn = int(sn)
                                voter_vin = voter_vin.split(':')[-1].strip()
                                voter_dob, voter_gender = voter_dob_gender.split(
                                    'GENDER: ')
                                voter_dob = voter_dob.split(':')[-1].strip()
                                update(sn, page, voter_vin, voter_name, voter_dob, voter_gender,
                                       voter_img, pu_text, page_ward, page_lga, page_delim, page_record_count)
                                with db.connect(dbFile) as conn:
                                    conn.execute(f"""
                                    UPDATE voters
                                    SET status = 'done'
                                    WHERE pu = "{pu_text}" AND voter_vin = "{voter_vin}"
                                    """)
                        pu_pop = int(page_record_count.replace(',', ''))
                        with db.connect(dbFile) as conn:
                            conn.execute(f"""
                            UPDATE voters
                            SET pu_done = 'done', pu_pop = "{pu_pop}"
                            WHERE pu = "{pu_text}"
                            """)
                        # tell the db that you are done with this PU
                        if int(time.time() - timenow) > 60:
                            vpn_settings = initialize_vpn(random.choice(
                                ['Canada', 'France', 'United Kingdom', 'United States']))
                            rotate_VPN(vpn_settings)
                            timenow = time.time()
                        time.sleep(3)
                        browser.find_element('tag name', 'body').send_keys(
                            Keys.CONTROL+Keys.HOME)
                        if 'Show Search Options' in browser.find_element('id', 'showSidebarButton').text:
                            browser.find_element(
                                'id', 'showSidebarButton').click()
                        Select(browser.find_element(
                            'id', 'VoterRegisterStateId')).select_by_visible_text(state_text)
                        Select(browser.find_element(
                            'id', 'VoterRegisterLocalGovernmentId')).select_by_visible_text(lga_text)
                        Select(browser.find_element(
                            'id', 'VoterRegisterRegistrationAreaId')).select_by_visible_text(ward_text)
                        Select(browser.find_element(
                            'id', 'VoterRegisterPollingUnitId')).select_by_visible_text(pu_text)
                        ward_pop += pu_pop
                    with db.connect(dbFile) as conn:
                        conn.execute(f"""
                        UPDATE voters
                        SET ward_done = 'done', ward_pop = "{ward_pop}"
                        WHERE ward = "{ward_text}"
                        """)
                    lga_pop += ward_pop
                Select(browser.find_element('id', 'VoterRegisterStateId')
                       ).select_by_visible_text(state_text)
                Select(browser.find_element(
                    'id', 'VoterRegisterLocalGovernmentId')).select_by_visible_text(lga_text)

                with db.connect(dbFile) as conn:
                    conn.execute(f"""
                    UPDATE voters
                    SET lga_done = 'done', lga_pop = "{lga_pop}"
                    WHERE lga = "{lga_text}"
                    """)
            Select(browser.find_element('id', 'VoterRegisterStateId')
                   ).select_by_visible_text(state_text)
            Select(browser.find_element(
                'id', 'VoterRegisterLocalGovernmentId')).select_by_visible_text(lga_text)
    except:
        recursive()


browser = Chrome(options=options)
browser.get("https://cvr.inecnigeria.org/Home/register")
browser.get('https://cvr.inecnigeria.org/VotersRegister')
login()
timenow = time.time()

recursive()
