from __future__ import print_function
import os
import sys
import time
import requests
import urllib
import socket
from urllib2 import URLError, HTTPError
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ExpectedConditions
from selenium.webdriver.support.ui import WebDriverWait

def make_driver(url, timeout, user_agent):
	socket.setdefaulttimeout(timeout)
	dcap = dict(DesiredCapabilities.PHANTOMJS)
	dcap["phantomjs.page.settings.userAgent"] = user_agent
	driver = webdriver.PhantomJS(desired_capabilities = dcap)
	driver.set_window_size(1024, 768)
	return driver

def scroll_down(driver):
	for i in range(100):
		driver.execute_script("window.scrollTo(0, {0})".format(100 * i))
		time.sleep(0.01)
	
def get_gallery_links(driver, url, base_url):
	driver.get(url)
	driver.find_element_by_id("albums_load_more").click()
	scroll_down(driver)
	gallery_links = []
	for a in driver.find_elements_by_class_name("img_link "):	
		gallery_links.append(a.get_attribute("href"))

	return gallery_links, len(gallery_links)

def get_image_links(driver, url, timeout):
	driver.get(url)
	scroll_down(driver)
	tmp_links = []
	container = driver.find_element_by_id("photos_container")
	for a in container.find_elements_by_tag_name("a"):
		tmp_links.append(a.get_attribute("href"))
	image_links = []
	for tmp_link in tmp_links:
		driver.get(tmp_link)
		wait = WebDriverWait(driver, timeout)
		a = wait.until(ExpectedConditions.presence_of_element_located((By.ID, "pv_open_original")))
		image_links.append(a.get_attribute("href"))
	return image_links, len(image_links)

def save_image(url, folder):
	filename = url.split('/')[-1]
	full_path = folder + "/" + filename
	if os.path.isfile(full_path):
		raise OSError("Image found on disk. Skipping")
	else:
		urllib.urlretrieve(url, full_path)	

def crawl_url(gallery, base_url, timeout, user_agent):
	url = base_url + gallery
	driver = make_driver(url, timeout, user_agent)
	print("Looking for galleries in " + url)
	gallery_links, gallery_count = get_gallery_links(driver, url, base_url)
	print("{0} galleries found".format(gallery_count))
	for i, gallery_link in enumerate(gallery_links):
		gallery_name = gallery_link.split('/')[-1].split('.')[0]
		print("crawling gallery '{0}' ({1} of {2})".format(gallery_name, i + 1, gallery_count))
		if not os.path.exists(gallery_name):
			os.makedirs(gallery_name)
		image_links, image_count = get_image_links(driver, gallery_link, timeout)
		print("{0} images found".format(image_count))
		images_saved = 0
		images_skipped = 0
		images_failed = 0
		for j, image_link in enumerate(image_links):
			print ("saving image {0} of {1}{2}".format(j + 1, image_count, ' ' * 20), end='\r'),
			try:
				save_image(image_link, gallery_name)
				images_saved += 1
			except OSError as e:
				print(e.args, end='\r'),
				images_skipped += 1
			except (HTTPError, URLError, WebDriverException) as e:
				print('Failed to download image: ' + image_link)
				print(e.args)
				images_failed += 1
			sys.stdout.flush()
		if images_saved > 0:
			print("downloaded {0} of {1} images{2}".format(images_saved, image_count, ' ' * 20))
		if images_skipped > 0:
			print("skipped {0} of {1} images{2}".format(images_skipped, image_count, ' ' * 20))
		if images_failed > 0:
			print("failed to download {0} of {1} images{2}".format(images_failed, image_count, ' ' * 20))

gallery = "albums-id"
base_url = "https://vk.com/"
timeout = 20
user_agent = "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:33.0) Gecko/20100101 Firefox/33.0"

if __name__ == '__main__':
    crawl_url(gallery, base_url, timeout, user_agent)
