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

"""Example of dynamic use of Google Visualization Python API."""

__author__ = "Misha Seltzer"

import gviz_api

description = {"name": ("string", "Name"),
               "salary": ("number", "Salary"),
               "full_time": ("boolean", "Full Time Employee")}
data = [{"name": "Mike", "salary": (10000, "$10,000"), "full_time": True},
        {"name": "Jim", "salary": (800, "$800"), "full_time": False},
        {"name": "Alice", "salary": (12500, "$12,500"), "full_time": True},
        {"name": "Bob", "salary": (7000, "$7,000"), "full_time": True}]

data_table = gviz_api.DataTable(description)
data_table.LoadData(data)
print "Content-type: text/plain"
print
print data_table.ToJSonResponse(columns_order=("name", "salary", "full_time"),
                                order_by="salary")

# Put the url (http://google-visualization.appspot.com/python/dynamic_example) as your
# Google Visualization data source.
