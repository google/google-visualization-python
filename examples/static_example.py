#!/usr/bin/python
#
# Copyright (C) 2008 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Example of static use of Google Visualization Python API."""

__author__ = "Misha Seltzer"

import gviz_api

page_template = """
<html>
  <head>
  <title>Static example</title>
    <script src="http://www.google.com/jsapi" type="text/javascript"></script>
    <script>
      google.load("visualization", "1", {packages:["table"]});

      google.setOnLoadCallback(drawTable);
      function drawTable() {
        %(jscode)s
        var jscode_table = new google.visualization.Table(document.getElementById('table_div_jscode'));
        jscode_table.draw(jscode_data, {showRowNumber: true});

        var json_table = new google.visualization.Table(document.getElementById('table_div_json'));
        var json_data = new google.visualization.DataTable(%(json)s, 0.5);
        json_table.draw(json_data, {showRowNumber: true});
      }
    </script>
  </head>
  <body>
    <H1>Table created using ToJSCode</H1>
    <div id="table_div_jscode"></div>
    <H1>Table created using ToJSon</H1>
    <div id="table_div_json"></div>
  </body>
</html>
"""


def main():
  # Creating the data
  description = {"name": ("string", "Name"),
                 "salary": ("number", "Salary"),
                 "full_time": ("boolean", "Full Time Employee")}
  data = [{"name": "Mike", "salary": (10000, "$10,000"), "full_time": True},
          {"name": "Jim", "salary": (800, "$800"), "full_time": False},
          {"name": "Alice", "salary": (12500, "$12,500"), "full_time": True},
          {"name": "Bob", "salary": (7000, "$7,000"), "full_time": True}]

  # Loading it into gviz_api.DataTable
  data_table = gviz_api.DataTable(description)
  data_table.LoadData(data)

  # Creating a JavaScript code string
  jscode = data_table.ToJSCode("jscode_data",
                               columns_order=("name", "salary", "full_time"),
                               order_by="salary")
  # Creating a JSon string
  json = data_table.ToJSon(columns_order=("name", "salary", "full_time"),
                           order_by="salary")

  # Putting the JS code and JSon string into the template
  print(page_template % vars())


if __name__ == "__main__":
  main()
