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

"""Tests for the gviz_api module."""

__author__ = "Amit Weinstein"

from datetime import date
from datetime import datetime
from datetime import time
import re
import unittest

from gviz_api import DataTable
from gviz_api import DataTableException


class DataTableTest(unittest.TestCase):

  def testSingleValueToJS(self):
    # We first check that given an unknown type it raises exception
    self.assertRaises(DataTableException,
                      DataTable.SingleValueToJS, 1, "no_such_type")

    # If we give a type which does not match the value, we expect it to fail
    self.assertRaises(DataTableException,
                      DataTable.SingleValueToJS, "a", "number")
    self.assertRaises(DataTableException,
                      DataTable.SingleValueToJS, "b", "timeofday")
    self.assertRaises(DataTableException,
                      DataTable.SingleValueToJS, 10, "date")

    # Suppose to fail when giving formatting for a None cell
    self.assertRaises(DataTableException,
                      DataTable.SingleValueToJS, (None, "none"), "string")

    # A tuple for value and formatted value should be of length 2
    self.assertRaises(DataTableException,
                      DataTable.SingleValueToJS, (5, "5$", "6$"), "string")

    # Some good examples from all the different types
    self.assertEqual("true", DataTable.SingleValueToJS(True, "boolean"))
    self.assertEqual("false", DataTable.SingleValueToJS(False, "boolean"))
    self.assertEqual("true", DataTable.SingleValueToJS(1, "boolean"))
    self.assertEqual("null", DataTable.SingleValueToJS(None, "boolean"))
    self.assertEqual(("false", "'a'"),
                     DataTable.SingleValueToJS((False, "a"), "boolean"))

    self.assertEqual("1", DataTable.SingleValueToJS(1, "number"))
    self.assertEqual("1.0", DataTable.SingleValueToJS(1., "number"))
    self.assertEqual("-5", DataTable.SingleValueToJS(-5, "number"))
    self.assertEqual("null", DataTable.SingleValueToJS(None, "number"))
    self.assertEqual(("5", "'5$'"),
                     DataTable.SingleValueToJS((5, "5$"), "number"))

    self.assertEqual("'-5'", DataTable.SingleValueToJS(-5, "string"))
    self.assertEqual("'abc'", DataTable.SingleValueToJS("abc", "string"))
    self.assertEqual("null", DataTable.SingleValueToJS(None, "string"))

    self.assertEqual("new Date(2010,0,2)",
                     DataTable.SingleValueToJS(date(2010, 1, 2), "date"))
    self.assertEqual("new Date(2001,1,3)",
                     DataTable.SingleValueToJS(datetime(2001, 2, 3, 4, 5, 6),
                                               "date"))
    self.assertEqual("null", DataTable.SingleValueToJS(None, "date"))

    self.assertEqual("[10,11,12]",
                     DataTable.SingleValueToJS(time(10, 11, 12), "timeofday"))
    self.assertEqual("[3,4,5]",
                     DataTable.SingleValueToJS(datetime(2010, 1, 2, 3, 4, 5),
                                               "timeofday"))
    self.assertEqual("null", DataTable.SingleValueToJS(None, "timeofday"))

    self.assertEqual("new Date(2001,1,3,4,5,6)",
                     DataTable.SingleValueToJS(datetime(2001, 2, 3, 4, 5, 6),
                                               "datetime"))
    self.assertEqual("null", DataTable.SingleValueToJS(None, "datetime"))

  def testDifferentStrings(self):
    # Checking escaping of strings
    problematic_strings = ["control", "new\nline", "",
                           "single'quote", 'double"quote',
                           r"one\slash", r"two\\slash"]
    for s in problematic_strings:
      self.assertEquals(s, eval(DataTable.SingleValueToJS(s, "string")))
      self.assertEquals(
          s, eval(DataTable.SingleValueToJS(("str", s), "string")[1]))

  def testColumnTypeParser(self):
    # Checking several wrong formats
    self.assertRaises(DataTableException,
                      DataTable.ColumnTypeParser, 5)
    self.assertRaises(DataTableException,
                      DataTable.ColumnTypeParser, ("a", "b", "c", "d"))
    self.assertRaises(DataTableException,
                      DataTable.ColumnTypeParser, ("a", 5, "c"))

    # Checking several legal formats
    self.assertEqual({"id": "abc", "label": "abc", "type": "string"},
                     DataTable.ColumnTypeParser("abc"))
    self.assertEqual({"id": "abc", "label": "abc", "type": "string"},
                     DataTable.ColumnTypeParser(("abc",)))
    self.assertEqual({"id": "abc", "label": "bcd", "type": "string"},
                     DataTable.ColumnTypeParser(("abc", "string", "bcd")))
    self.assertEqual({"id": "a", "label": "b", "type": "number"},
                     DataTable.ColumnTypeParser(("a", "number", "b")))
    self.assertEqual({"id": "a", "label": "a", "type": "number"},
                     DataTable.ColumnTypeParser(("a", "number")))

  def testTableDescriptionParser(self):
    # We expect it to fail with empty lists or dictionaries
    self.assertRaises(DataTableException,
                      DataTable.TableDescriptionParser, {})
    self.assertRaises(DataTableException,
                      DataTable.TableDescriptionParser, [])
    self.assertRaises(DataTableException,
                      DataTable.TableDescriptionParser, {"a": []})
    self.assertRaises(DataTableException,
                      DataTable.TableDescriptionParser, {"a": {"b": {}}})

    # We expect it to fail if we give a non-string at the lowest level
    self.assertRaises(DataTableException,
                      DataTable.TableDescriptionParser, {"a": 5})
    self.assertRaises(DataTableException,
                      DataTable.TableDescriptionParser, [("a", "number"), 6])

    # Some valid examples which mixes both dictionaries and lists
    self.assertEqual(
        [{"id": "a", "label": "a", "type": "date",
          "depth": 0, "container": "iter"},
         {"id": "b", "label": "b", "type": "timeofday",
          "depth": 0, "container": "iter"}],
        DataTable.TableDescriptionParser([("a", "date"), ("b", "timeofday")]))

    self.assertEqual(
        [{"id": "a", "label": "a", "type": "string",
          "depth": 0, "container": "dict"},
         {"id": "b", "label": "b", "type": "number",
          "depth": 1, "container": "iter"},
         {"id": "c", "label": "column c", "type": "string",
          "depth": 1, "container": "iter"}],
        DataTable.TableDescriptionParser({"a": [("b", "number"),
                                                ("c", "string", "column c")]}))

    self.assertEqual(
        [{"id": "a", "label": "column a", "type": "number",
          "depth": 0, "container": "dict"},
         {"id": "b", "label": "b", "type": "number",
          "depth": 1, "container": "dict"},
         {"id": "c", "label": "c", "type": "string",
          "depth": 1, "container": "dict"}],
        DataTable.TableDescriptionParser({("a", "number", "column a"):
                                          {"b": "number", "c": "string"}}))

    self.assertEqual(
        [{"id": "a", "label": "column a", "type": "number",
          "depth": 0, "container": "dict"},
         {"id": "b", "label": "column b", "type": "string",
          "depth": 1, "container": "scalar"}],
        DataTable.TableDescriptionParser({("a", "number", "column a"):
                                          ("b", "string", "column b")}))

  def testAppendData(self):
    # We check a few examples where the format of the data does not match the
    # description and hen a few valid examples. The test for the content itself
    # is done inside the ToJSCode and ToJSon functions.
    table = DataTable([("a", "number"), ("b", "string")])
    self.assertEqual(0, table.NumberOfRows())
    self.assertRaises(DataTableException,
                      table.AppendData, [[1, "a", True]])
    self.assertRaises(DataTableException,
                      table.AppendData, {1: ["a"], 2: ["b"]})
    self.assertEquals(None, table.AppendData([[1, "a"], [2, "b"]]))
    self.assertEqual(2, table.NumberOfRows())
    self.assertEquals(None, table.AppendData([[3, "c"], [4]]))
    self.assertEqual(4, table.NumberOfRows())

    table = DataTable({"a": "number", "b": "string"})
    self.assertEqual(0, table.NumberOfRows())
    self.assertRaises(DataTableException,
                      table.AppendData, [[1, "a"]])
    self.assertRaises(DataTableException,
                      table.AppendData, {5: {"b": "z"}})
    self.assertEquals(None, table.AppendData([{"a": 1, "b": "z"}]))
    self.assertEqual(1, table.NumberOfRows())

    table = DataTable({("a", "number"): [("b", "string")]})
    self.assertEqual(0, table.NumberOfRows())
    self.assertRaises(DataTableException,
                      table.AppendData, [[1, "a"]])
    self.assertRaises(DataTableException,
                      table.AppendData, {5: {"b": "z"}})
    self.assertEquals(None, table.AppendData({5: ["z"], 6: ["w"]}))
    self.assertEqual(2, table.NumberOfRows())

    table = DataTable({("a", "number"): {"b": "string", "c": "number"}})
    self.assertEqual(0, table.NumberOfRows())
    self.assertRaises(DataTableException,
                      table.AppendData, [[1, "a"]])
    self.assertRaises(DataTableException,
                      table.AppendData, {1: ["a", 2]})
    self.assertEquals(None, table.AppendData({5: {"b": "z", "c": 6},
                                              7: {"c": 8},
                                              9: {}}))
    self.assertEqual(3, table.NumberOfRows())

  def testToJSCode(self):
    table = DataTable([("a", "number", "A"), "b", ("c", "timeofday")],
                      [[1],
                       [None, "z", time(1, 2, 3)],
                       [(2, "2$"), "w", time(2, 3, 4)]])
    self.assertEqual(3, table.NumberOfRows())
    self.assertEqual(("var mytab = new google.visualization.DataTable();\n"
                      "mytab.addColumn('number', 'A', 'a');\n"
                      "mytab.addColumn('string', 'b', 'b');\n"
                      "mytab.addColumn('timeofday', 'c', 'c');\n"
                      "mytab.addRows(3);\n"
                      "mytab.setCell(0, 0, 1);\n"
                      "mytab.setCell(1, 1, 'z');\n"
                      "mytab.setCell(1, 2, [1,2,3]);\n"
                      "mytab.setCell(2, 0, 2, '2$');\n"
                      "mytab.setCell(2, 1, 'w');\n"
                      "mytab.setCell(2, 2, [2,3,4]);\n"),
                     table.ToJSCode("mytab"))

    table = DataTable({("a", "number"): {"b": "date", "c": "datetime"}},
                      {1: {},
                       2: {"b": date(1, 2, 3)},
                       3: {"c": datetime(1, 2, 3, 4, 5, 6)}})
    self.assertEqual(3, table.NumberOfRows())
    self.assertEqual(("var mytab2 = new google.visualization.DataTable();\n"
                      "mytab2.addColumn('datetime', 'c', 'c');\n"
                      "mytab2.addColumn('date', 'b', 'b');\n"
                      "mytab2.addColumn('number', 'a', 'a');\n"
                      "mytab2.addRows(3);\n"
                      "mytab2.setCell(0, 2, 1);\n"
                      "mytab2.setCell(1, 1, new Date(1,1,3));\n"
                      "mytab2.setCell(1, 2, 2);\n"
                      "mytab2.setCell(2, 0, new Date(1,1,3,4,5,6));\n"
                      "mytab2.setCell(2, 2, 3);\n"),
                     table.ToJSCode("mytab2", columns_order=["c", "b", "a"]))

  def testToJSon(self):
    # The json of the initial data we load to the table.
    init_data_json = ("{cols: "
                      "[{id:'a',label:'A',type:'number'},"
                      "{id:'b',label:'b',type:'string'},"
                      "{id:'c',label:'c',type:'boolean'}],"
                      "rows: ["
                      "{c:[{v:1},,{v:null}]},"
                      "{c:[,{v:'z'},{v:true}]}"
                      "]}")
    table = DataTable([("a", "number", "A"), "b", ("c", "boolean")],
                      [[1],
                       [None, "z", True]])
    self.assertEqual(2, table.NumberOfRows())
    self.assertEqual(init_data_json,
                     table.ToJSon())
    table.AppendData([[-1, "w", False]])
    self.assertEqual(3, table.NumberOfRows())
    self.assertEqual(init_data_json[:-2] + ",{c:[{v:-1},{v:'w'},{v:false}]}]}",
                     table.ToJSon())

    cols_json = ("{cols: "
                 "[{id:'t',label:'T',type:'timeofday'},"
                 "{id:'d',label:'d',type:'date'},"
                 "{id:'dt',label:'dt',type:'datetime'}],")
    table = DataTable({("d", "date"): [("t", "timeofday", "T"),
                                       ("dt", "datetime")]})
    table.LoadData({date(1, 2, 3): [time(1, 2, 3)]})
    self.assertEqual(1, table.NumberOfRows())
    self.assertEqual(cols_json +
                     "rows: [{c:[{v:[1,2,3]},{v:new Date(1,1,3)},{v:null}]}]}",
                     table.ToJSon(columns_order=["t", "d", "dt"]))
    table.LoadData({date(2, 3, 4): [(time(2, 3, 4), "time 2 3 4"),
                                    datetime(1, 2, 3, 4, 5, 6)],
                    date(3, 4, 5): []})
    self.assertEqual(2, table.NumberOfRows())
    self.assertEqual((cols_json + "rows: ["
                      "{c:[{v:[2,3,4],f:'time 2 3 4'},{v:new Date(2,2,4)},"
                      "{v:new Date(1,1,3,4,5,6)}]},"
                      "{c:[,{v:new Date(3,3,5)},{v:null}]}]}"),
                     table.ToJSon(columns_order=["t", "d", "dt"]))

    json = ("{cols: [{id:'a',label:'a',type:'string'},"
            "{id:'b',label:'b',type:'number'}],"
            "rows: [{c:[{v:'a1'},{v:1}]},{c:[{v:'a2'},{v:2}]},"
            "{c:[{v:'a3'},{v:3}]}]}")
    table = DataTable({"a": ("b", "number")},
                      {"a1": 1, "a2": 2, "a3": 3})
    self.assertEqual(3, table.NumberOfRows())
    self.assertEqual(json,
                     table.ToJSon())

  def testOrderBy(self):
    data = [("b", 3), ("a", 3), ("a", 2), ("b", 1)]
    description = ["col1", ("col2", "number", "Second Column")]
    table = DataTable(description, data)

    table_num_sorted = DataTable(description,
                                 sorted(data, key=lambda x: (x[1], x[0])))

    table_str_sorted = DataTable(description,
                                 sorted(data, key=lambda x: x[0]))

    table_diff_sorted = DataTable(description,
                                  sorted(sorted(data, key=lambda x: x[1]),
                                         key=lambda x: x[0], reverse=True))

    self.assertEqual(table_num_sorted.ToJSon(),
                     table.ToJSon(order_by=("col2", "col1")))
    self.assertEqual(table_num_sorted.ToJSCode("mytab"),
                     table.ToJSCode("mytab", order_by=("col2", "col1")))

    self.assertEqual(table_str_sorted.ToJSon(), table.ToJSon(order_by="col1"))
    self.assertEqual(table_str_sorted.ToJSCode("mytab"),
                     table.ToJSCode("mytab", order_by="col1"))

    self.assertEqual(table_diff_sorted.ToJSon(),
                     table.ToJSon(order_by=[("col1", "desc"), "col2"]))
    self.assertEqual(table_diff_sorted.ToJSCode("mytab"),
                     table.ToJSCode("mytab",
                                    order_by=[("col1", "desc"), "col2"]))

  def testToJSonResponse(self):
    description = ["col1", "col2", "col3"]
    data = [("1", "2", "3"), ("a", "b", "c"), ("One", "Two", "Three")]
    req_id = 4
    table = DataTable(description, data)

    start_str_default = r"google.visualization.Query.setResponse"
    start_str_handler = r"MyHandlerFunction"
    default_params = (r"\s*'version'\s*:\s*'0.5'\s*,\s*'reqId'\s*:\s*'%s'\s*,"
                      r"\s*'status'\s*:\s*'OK'\s*" % req_id)
    regex1 = re.compile("%s\(\s*\{%s,\s*'table'\s*:\s*{(.*)}\s*\}\s*\);" %
                        (start_str_default, default_params))
    regex2 = re.compile("%s\(\s*\{%s,\s*'table'\s*:\s*{(.*)}\s*\}\s*\);" %
                        (start_str_handler, default_params))

    json_str = table.ToJSon().strip()

    json_response = table.ToJSonResponse(req_id=req_id)
    match = regex1.findall(json_response)
    self.assertEquals(len(match), 1)
    # We want to match against the json_str without the curly brackets.
    self.assertEquals(match[0], json_str[1:-1])

    json_response = table.ToJSonResponse(req_id=req_id,
                                         response_handler=start_str_handler)
    match = regex2.findall(json_response)
    self.assertEquals(len(match), 1)
    # We want to match against the json_str without the curly brackets.
    self.assertEquals(match[0], json_str[1:-1])


if __name__ == "__main__":
  unittest.main()
