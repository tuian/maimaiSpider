# -*- coding: utf-8 -*-
import scrapy
import re
import json
import time
import random
from Maimai.items import BaseItem
from Maimai.items import WorkItem
from Maimai.items import EduItem
from Maimai.items import CommentItem

NONE_STR = lambda x : '' if x == None else x

WORK_END_DATE = lambda x : '至今' if x == None else x

KEY_WORDS = {
		'2221' : '陌陌',
		'11070' : '豆瓣',
		#'1' : '脉脉',
		#'8877' : '人人网',
		#'10020' : '去哪儿',
		#'27394' : '友盟',
		#'10041' : '优酷',
		#'8220' : '爱奇艺',
		#'10989' : '搜狐',
		#'10993' : '今日头条',
		#'8538' : '微软',
		#'9859' : '滴滴',
		#'12207' : '雅虎',
		#'10860' : '亚马逊',
		#'24030' : 'boss直聘',
		#'11973' : '领英',
		#'16017' : '谷歌',
	}

SEX_DICT = {
		u'他' : '男',
		u'她' : '女',
	}

DEGREE_DICT = {
		0 : '专科',
		1 : '本科',
		2 : '硕士',
		3 : '博士',
		4 : '博士后',
		5 : '其他',
		255 : '其他',
	}

class MaimaiSpider(scrapy.Spider):
	name = 'maimai'
	allowed_domains = ['maimai.cn',]
	start_urls = ['http://maimai.cn/',]

	#每次获取员工数量
	count = '200'
	#获取页数
	page = 1
	#请求延迟秒数
	sleep_time = 1

	head_url = 'https://maimai.cn/company/contacts?count='
	page_url = '&page='
	cid_url = '&cid='
	json_url = '&jsononly=1'

	cookies = {
		'token' : '"QFBKXO4Q8hr5+lfxC7zMEBSev2fW4AiD8FQvu3brKafOAj8L/PLp9Fgkvp0XPPA78CKuzcDfAvoCmBm7+jVysA=="',
		'uid' : '"42d7njHRjiXyJdBe+Wj6zPAirs3A3wL6ApgZu/o1crA="',
		}

	def start_requests(self):
		'''
			查询公司员工
		'''
		for cid in KEY_WORDS.keys():
			i = 0
			while True:
				url = self.head_url + self.count + self.page_url + str(i) + self.cid_url + cid + self.json_url
				time.sleep(self.sleep_time)
				yield scrapy.Request(url, cookies=self.cookies, callback=self.parse)
				i += 1
				if i == self.page:
					break

	def parse(self, response):
		'''
			解析个人员工url
		'''
		
		start_url = 'https://maimai.cn/contact/detail/'
		end_url = '?from=webview%23%2Fcompany%2Fcontacts&jsononly=1'

		comment_start_url = 'https://maimai.cn/contact/comment_list/'
		comment_end_url = '?jsononly=1'

		content = json.loads(response.body)
		contacts = content['data']['contacts']
		for contact in contacts:
			person_url = start_url + contact['contact']['encode_mmid'] + end_url
			time.sleep(self.sleep_time)
			yield scrapy.Request(person_url, cookies=self.cookies, callback=self.get_info)

			comment_url = comment_start_url + contact['contact']['encode_mmid'] + comment_end_url

			time.sleep(self.sleep_time)
			yield scrapy.Request(comment_url, callback=self.get_comment)


	def get_info(self, response):
		'''
			解析员工个人信息
		'''
		
		content = json.loads(response.body)

		try:
			card = content['data']['card']
			uinfo = content['data']['uinfo']
			sex = content['data']['ta']

			#个人ID
			id = str(card['id'])

			#基本信息
			item = BaseItem()
			#id
			item['id'] = id
			#url
			item['url'] = response.url
			#姓名
			item['name'] = card['name']
			#头像链接
			item['img'] = card['avatar_large']
			#公司
			item['company'] = card['company']
			#职位
			item['position'] = card['position']
			#工作地
			item['work_city'] = card['province'] + '-' +  card['city']
			#性别
			item['sex'] = SEX_DICT.get(sex, '不详')
			#家乡
			item['birth_city'] = NONE_STR(uinfo.get('ht_province', '')) + '-' + NONE_STR(uinfo.get('ht_city', ''))
			if item['birth_city'] == '-':
				item['birth_city'] = ''
			#星座
			item['xingzuo'] = uinfo.get('xingzuo', '')
			#生日
			item['birthday'] = NONE_STR(uinfo.get('birthday', ''))
			#标签
			item['tag'] = ','.join(uinfo['weibo_tags'])
			yield item	
	
			#工作经历
			for work_exp in uinfo['work_exp']:
				item = WorkItem()
				item['id'] = id
				item['company'] = work_exp['company']
				item['position'] = work_exp['position']
				item['description'] = work_exp.get('description', '')
				item['start_date'] = work_exp['start_date']
				item['end_date'] = WORK_END_DATE(work_exp['end_date'])
				yield item

			#教育经历
			for edu_exp in uinfo['education']:
				item = EduItem()
				item['id'] = id
				item['school'] = edu_exp['school']
				item['degree'] = DEGREE_DICT[edu_exp.get('degree', '255')]
				item['department'] = edu_exp['department']
				item['start_date'] = edu_exp['start_date']
				item['end_date'] = edu_exp.get('end_date', '')
				yield item
		except Exception, e:
			print e

	def get_comment(self, response):
		try:
			content = json.loads(response.body)
			comment_list = content['data']['evaluation_list']
		except Exception, e:
			print e

		for comment in comment_list:
			item = CommentItem()
			item['id'] = comment['user']['id']
			item['friend_id'] = comment['src_user']['id']
			item['friend_name'] = comment['src_user']['name']
			item['friend_company'] = comment['src_user']['company']
			item['friend_position'] = comment['src_user']['position']
			item['level'] = comment['re']
			item['comment'] = comment['text']
			yield item

