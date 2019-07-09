#!/usr/bin/env python
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from bs4 import BeautifulSoup
import xmlrpclib
import ssl
import random
from datetime import datetime
import time
import logging


#Logging Configuration
log_directory = '/home/anagh/projects/price-paper/custom_addons/website_scraping/script/logging'
filename = ("%s.log") %(datetime.now().strftime("%m_%d_%Y_%H_%M_%S"))
log_path = "%s/%s" %(log_directory, filename)
logging.basicConfig(filename=log_path, level=logging.INFO)


#Geckodriver Configuration
geckodriver_path = "/home/anagh/projects/price-paper/custom_addons/website_scraping/script/geckodriver"


#Browser Configuration
options = Options()
options.add_argument("--headless")  # declare the browser to run in headless mode


#Socket Connection Configuration
login = 1
pwd = "admin"
db = "ppt_live_66"
socket = xmlrpclib.ServerProxy('http://localhost:9997/xmlrpc/object', context=ssl._create_unverified_context())
#socket = xmlrpclib.ServerProxy('https://odoodemo.pricepaper.com/xmlrpc/object',context=ssl._create_unverified_context())




def odoo_writeback(create_vals, product_id, write_url=''):
    """
    The common method which is used to
    write values back into the odoo instance
    """
    if write_url:
        write_status = socket.execute(db, login, pwd, 'product.sku.reference', 'write', product_id, {'website_link': write_url})
    create_status = socket.execute(db, login, pwd, 'competitor.website.price', 'create', create_vals)



def random_sleep():
    """
    This method is used to introduce a random
    seconds of sleep time to the scraping process
    """
    ran_int = random.randint(0,1)
    if ran_int == 1:
        nap_time = random.randint(4,10)
        logging.info("sleeping for %s seconds." %(nap_time))
        time.sleep(nap_time)



def restaurant_depot_login(driver, website_config):
    login = False
    while not login:
        try:
            if 'rdepot' in website_config:
                login_url = website_config['rdepot'][0]
                username = website_config['rdepot'][1]
                password = website_config['rdepot'][2]

                driver.get(login_url)
                driver.implicitly_wait(40)

                uname = driver.find_element_by_id('cphMainContent_txtUserName')
                uname.clear()
                uname.send_keys(username)

                pwd = driver.find_element_by_id('cphMainContent_txtPassword')
                pwd.clear()
                pwd.send_keys(password)

                submit_button = driver.find_element_by_id('cphMainContent_btnSubmit')
                submit_button.click()
                driver.implicitly_wait(60)
                login = True
        except Exception as e:
            pass

    return driver







def restaurant_depot_fetch(driver, item, products, mode):


    if mode == 'search':
        search_box = driver.find_element_by_id('searchTerm')
        search_box.clear()
        search_box.send_keys(item)
        search_button = driver.find_element_by_id('search-button')
        search_button.click()

    if mode== 'url':
        driver.get(products[item][2])

    driver.implicitly_wait(random.randint(40,45))
    unit_price = 0
    product_sku_id = products[item][0]
    item_url = driver.current_url
    soup_level2 = BeautifulSoup(driver.page_source, 'lxml')
    name_td = soup_level2.findAll('td', {'class': 'sHC3'})
    name = False
    if name_td:
        name =  name_td[0].label.get_text()
    price_div = soup_level2.findAll('div', {'id': 'ctl00_cphMainContent_resultsGrid_ctl00_ctl04_pnlUnitPrice'})

    if price_div:
        unit_price = price_div[0].label.get_text().split()[1][1:]
        create_vals = {'product_sku_ref_id': product_sku_id, 'item_name': name, 'item_price': unit_price, 'update_date': str(datetime.now())}
        logging.info("Writing %s values to Odoo database" %(item))
        res = odoo_writeback(create_vals, product_sku_id, write_url=item_url)
        return True
    return False


def restaurant_depot(products, website_config):
    driver = webdriver.Firefox(firefox_options=options, executable_path=geckodriver_path)
    driver = restaurant_depot_login(driver, website_config)

    if 'rdepot' in website_config:
        for item in products:
            res = False
            write_except = False
            try:
                res = restaurant_depot_fetch(driver, item, products, 'search')
                if not res and products[item][2]:
                    logging.info("could not find product in search. Redo the failed SKU with URL")
                    res = restaurant_depot_fetch(driver, item, products, 'url')
                random_sleep()


            except Exception as e:
                # if exception due to logout timeout, then redo login and repeat
#                driver.close()
                driver.quit()
                logging.info("Closed Driver, Quit driver, Spawning new driver instance and Logging in .................")
                driver = webdriver.Firefox(firefox_options=options, executable_path=geckodriver_path)
                driver = restaurant_depot_login(driver, website_config)
                try:
                    res = restaurant_depot_fetch(driver, item, products, 'search')
                    if not res and products[item][2]:
                        logging.info("could not find product in search. Redo the failed SKU with URL")
                        res = restaurant_depot_fetch(driver, item, products, 'url')
                    random_sleep()
                except Exception as er:
                    logging.error('Exception occured for %s: %s' %(item, er))
                    write_except = socket.execute(db, login, pwd, 'product.sku.reference', 'log_exception_error', products[item][0], str(er))

            if res:
                schedule_to_unlink = socket.execute(db, login, pwd, 'price.fetch.schedule', 'search', [('product_sku_ref_id','=', products[item][0])], 0, 1)
                unlink_scheduled = schedule_to_unlink and socket.execute(db, login, pwd, 'price.fetch.schedule', 'unlink', schedule_to_unlink)
            if not res and not write_except:
                write_except = socket.execute(db, login, pwd, 'product.sku.reference', 'log_exception_error', products[item][0], "Couldn't fetch price due to unknown reason, please check.")


    else:
        logging.error('Website Configuration required for Resturant Depot. Returning...')
        return False
    try:
#        driver.close()
        driver.quit()
        logging.info('Successfully closed driver for Restaurant Depot. Returning...')
        return True
    except:
        logging.error('Exception! cannot close driver Exiting...')
        return False







def webstaurant_store_fetch(driver, item, products, mode):
    unit_price = 0
    product_sku_id = products[item][0]

    if mode == 'search':
        search_box = driver.find_element_by_id('searchval')
        search_box.clear()
        search_box.send_keys(item)
        search_button = driver.find_element_by_xpath("//input[@class='btn btn-info banner-search-btn']")
        search_button.click()

    if mode== 'url':
        driver.get(products[item][2])

    driver.implicitly_wait(random.randint(40,45))
    item_url = driver.current_url

    soup_level2 = BeautifulSoup(driver.page_source, 'lxml')

    price_tr = soup_level2.findAll('div', {'class': 'pricing'})[0].findAll('tr')
    price = []
    name_tag = soup_level2.findAll('h1', {'itemprop': 'Name'})
    name= False
    if name_tag:
        name = name_tag[0].get_text()
    for tr in price_tr:
        if tr.find('td'):
            price.append(float(tr.find('td').get_text().replace('\n','').replace('\t', '').replace('$', '').split('/')[0]))
    if price:
        unit_price = max(price)
    else:
        price_span = soup_level2.findAll('span', {'itemprop': 'price'})
        if price_span:
            unit_price = price_span[0].get_text()

    if unit_price:
        logging.info("writing info sku:%s  Price:%s" %(item, unit_price))
        create_vals = {'product_sku_ref_id': product_sku_id, 'item_name': name, 'item_price': unit_price, 'update_date': str(datetime.now())}
        res = odoo_writeback(create_vals, product_sku_id, write_url=item_url)
        return True
    return False




def webstaurant_store(products, website_config):
    driver = webdriver.Firefox(firefox_options=options, executable_path=geckodriver_path)
    item_url = ''
    if 'wdepot' in website_config:
        login_url = website_config['wdepot'][0]
        driver.get(login_url)
        driver.implicitly_wait(random.randint(40,45))
        for item in products:
            res = False
            write_except = False
            try:
                res = webstaurant_store_fetch(driver, item, products, 'search')
                if not res and products[item][2]:
                    logging.info("could not find product in search. Redo the failed SKU with URL")
                    res = webstaurant_store_fetch(driver, item, products, 'url')
                random_sleep()

            except Exception as e:

                # if exception due to timeout, then recreate driver and repeat
#                driver.close()
                driver.quit()
                logging.info("Closed Driver, Quit driver, Spawning new driver instance.................")
                driver = webdriver.Firefox(firefox_options=options, executable_path=geckodriver_path)
                driver.get(login_url)
                driver.implicitly_wait(random.randint(40,45))
                try:
                    res = webstaurant_store_fetch(driver, item, products, 'search')
                    if not res and products[item][2]:
                        logging.info("could not find product in search. Redo the failed SKU with URL")
                        res = webstaurant_store_fetch(driver, item, products, 'url')
                    random_sleep()
                except Exception as er:
                    logging.error('Exception occured for %s: %s' %(item, er))
                    write_except = socket.execute(db, login, pwd, 'product.sku.reference', 'log_exception_error', products[item][0], str(er))

            if res:
                schedule_to_unlink = socket.execute(db, login, pwd, 'price.fetch.schedule', 'search', [('product_sku_ref_id','=', products[item][0])], 0, 1)
                unlink_scheduled = schedule_to_unlink and socket.execute(db, login, pwd, 'price.fetch.schedule', 'unlink', schedule_to_unlink)
            if not res and not write_except:
                write_except = socket.execute(db, login, pwd, 'product.sku.reference', 'log_exception_error', products[item][0], "Couldn't fetch price due to unknown reason, please check.")



    else:
        logging.error('Website Configuration required for Websturant Store')
    try:
#        driver.close()
        driver.quit()
    except:
        logging.error('Cannot close driver. Exiting...')




def check_queued_fetches(login_config):
    queued_fetches = socket.execute(db, login, pwd, 'price.fetch.schedule', 'search_read', [], ['id', 'product_sku_ref_id'])
    queued_fetches_ids = [ele['id'] for ele in queued_fetches]
    queued_fetches = [ele['product_sku_ref_id'][0] for ele in queued_fetches]
    rdepot_skus = socket.execute(db, login, pwd, 'product.sku.reference', 'search_read', [('id', 'in', queued_fetches), ('competitor', '=', 'rdepot'), ('in_exception', '=', False)], ['id', 'competitor_sku', 'website_link', 'qty_in_uom'])
    wdepot_skus = socket.execute(db, login, pwd, 'product.sku.reference', 'search_read', [('id', 'in', queued_fetches), ('competitor', '=', 'wdepot'), ('in_exception', '=', False)], ['id', 'competitor_sku', 'website_link', 'qty_in_uom'])
    rdepot_products = {sku['competitor_sku']: (sku['id'], sku['qty_in_uom'], sku['website_link']) for sku in rdepot_skus}
    wdepot_products = {sku['competitor_sku']: (sku['id'], sku['qty_in_uom'], sku['website_link']) for sku in wdepot_skus}
    if wdepot_products:
        webstaurant_store(wdepot_products, login_config)
    if rdepot_products:
        restaurant_depot(rdepot_products, login_config)
    return rdepot_products.keys(), wdepot_products.keys()














while True:
    website_config = socket.execute(db, login, pwd, 'website.scraping.cofig', 'search_read', [], ['id', 'home_page_url', 'username', 'password', 'competitor'])
    login_config = {config['competitor']: (config['home_page_url'], config['username'], config['password']) for config in website_config}
    if not login_config:
        logging.error('Website configuration required')
        exit()
    rdepot_keys, wdepot_keys = check_queued_fetches(login_config)
    time.sleep(300)









