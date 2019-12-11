from __future__ import annotations
from typing import List, Callable, Dict, Any, Tuple, Iterable
from jinja2 import Environment, FileSystemLoader
import base64
from io import BytesIO
import matplotlib.pyplot as plt
from urllib.request import urlopen, Request
import pdfkit
import logging
import os
import logging
import matplotlib
import pandas

class Tereport:
	
	def __init__(self, template_path:str):
		self.template_path = template_path
		self.templateFilePath = templateFilePath
		self.log = logging.getLogger("Tereport")
		self.context = {}

	def to_pdf(self, file_path:str):
		assert file_path != None
		assert file_path.strip() not in [""]

		import random
		salt = random.randint(1000)
		temp_file_name = "report_temp_%d.html"%(salt)
		self.to_html(temp_file_name)
		self.log.debug('Converting html to pdf --> "%s.pdf"'%(file_path))
		pdfkit.from_file('./'+temp_file_name, file_path)


	def to_html(self, file_path:str):
		assert file_path != None
		assert file_path.strip() not in [""]

		self.log.debug('Generating html --> "%s.html"' % (file_path))

		template_dir = os.path.basename(self.template_path)
		template_file_name = os.path.relpath(self.template_path, template_dir)

		loader = FileSystemLoader(template_dir)
		env = Environment(loader=loader)

		template = env.get_template(template_file_name)
		template_vars = self.context
		html_out = template.render(template_vars)

		with open(file_path, "w") as fout:
			fout.write(html_out)

		self.log.debug('Generating html -- Done' % (file_path))

	def report_value(self, id:str, content:str):
		assert content != None
		assert id != None
		assert id not in self.context, f"{id} is already defined"

		self.context[id] = content

	def report_values(self, id:str, values:Dict[str, Any]):
		for k in values:
			self.report_value(k, values[k])

	def report_title(self, title:str):
		assert title != None

		self.report_value("title", title)

	def report_figure(self, id:str, fig):
		assert fig != None

		fig_file = BytesIO()
		fig.savefig(fig_file)
		fig_file.seek(0)
		fig_data_png = base64.b64encode(fig_file.getvalue())
		value = "<img src=\"data:image/png;base64,%s\"/>"%(fig_data_png.decode("UTF8"))
		self.report_value(id, value)
		plt.close()
		plt.cla()
		plt.clf()

	def report_figure_from_url(self, id:str, url:str, request_headers:Dict={}):
		assert url != None and url.strip() != ""

		fig_file = BytesIO()
		req = Request(url.strip(), headers=headers)
		img = urlopen(req)
		fig_file.write(img.read())
		fig_file.seek(0)
		fig_data_png = base64.b64encode(fig_file.getvalue())
		value = "<img src=\"data:image/png;base64,%s\"/>"%(fig_data_png.decode("UTF8"))
		self.report_value(id, value)

	def report_figure_from_grafana(self, id:str, server:str, token:str, dashboardId:str, dashboard:str, panel_id:str, fromTs:str, toTs:str, width:int, height:int, vars:dict):
		# See http://docs.grafana.org/reference/sharing/#direct-link-rendered-image
		url = "http://%(server)s/render/d-solo/%(dashboardId)s/%(dashboard)s?orgId=1&panelId=%(panel_id)s&from=%(fromTs)s&to=%(toTs)s&width=%(width)s&height=%(height)s&tz=UTC%%2B02%%3A00"%{
			"server":server, "dashboardId": dashboardId, "dashboard":dashboard, "panel_id":panel_id, "fromTs":fromTs, "toTs":toTs, "width":width, "height":height}

		for var in vars:
			varName = var
			varValue = vars[var]
			url += "&var-%s=%s"%(varName, varValue)

		self.report_figure_from_url(id, url, headers={"Authorization" : token})

	def report_data_frame(self, id:str, df:pandas.DataFrame):
		value = df.to_html(classes="table table-striped table-sm")
		self.report_value(id, value)

	def report_html(self, id:str, content:str):
		value = content
		self.report_value(id, value)
