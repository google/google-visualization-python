#!/usr/bin/python
#
# Copyright (C) 2009 Google Inc.
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
    self.assertEqual(("null", "'none'"),
                     DataTable.SingleValueToJS((None, "none"), "string"))

  def testDifferentStrings(self):
    # Checking escaping of strings
    problematic_strings = ["control", "new\nline", "",
                           "single'quote", 'double"quote',
                           r"one\slash", r"two\\slash", u"unicode eng",
                           u"unicode \u05e2\u05d1\u05e8\u05d9\u05ea"]
    for s in problematic_strings:
      js_value = DataTable.SingleValueToJS(s, "string")
      if isinstance(js_value, unicode):
        js_value = "u%s" % js_value
      self.assertEquals(s, eval(js_value))

      js_value = DataTable.SingleValueToJS(("str", s), "string")[1]
      if isinstance(js_value, unicode):
        js_value = "u%s" % js_value
      self.assertEquals(s, eval(js_value))

  def testDifferentCustomProperties(self):
    # Checking escaping of custom properties
    problematic_cps = [{"control": "test"}, {u"unicode": "value"},
                       {"key": u"unicode"}, {u"unicode": u"unicode"},
                       {"regular": "single'quote"}, {"unicode": u"s'quote"}]
    for cp in problematic_cps:
      js_value = DataTable._EscapeCustomProperties(cp)
      self.assertEquals(cp, eval(js_value))

  def testColumnTypeParser(self):
    # Checking several wrong formats
    self.assertRaises(DataTableException,
                      DataTable.ColumnTypeParser, 5)
    self.assertRaises(DataTableException,
                      DataTable.ColumnTypeParser, ("a", 5, "c"))
    self.assertRaises(DataTableException,
                      DataTable.ColumnTypeParser, ("a", "blah"))
    self.assertRaises(DataTableException,
                      DataTable.ColumnTypeParser, ("a", "number", "c", "d"))

    # Checking several legal formats
    self.assertEqual({"id": "abc", "label": "abc", "type": "string",
                      "custom_properties": {}},
                     DataTable.ColumnTypeParser("abc"))
    self.assertEqual({"id": "abc", "label": "abc", "type": "string",
                      "custom_properties": {}},
                     DataTable.ColumnTypeParser(("abc",)))
    self.assertEqual({"id": "abc", "label": "bcd", "type": "string",
                      "custom_properties": {}},
                     DataTable.ColumnTypeParser(("abc", "string", "bcd")))
    self.assertEqual({"id": "a", "label": "b", "type": "number",
                      "custom_properties": {}},
                     DataTable.ColumnTypeParser(("a", "number", "b")))
    self.assertEqual({"id": "a", "label": "a", "type": "number",
                      "custom_properties": {}},
                     DataTable.ColumnTypeParser(("a", "number")))
    self.assertEqual({"id": "i", "label": "l", "type": "string",
                      "custom_properties": {"key": "value"}},
                     DataTable.ColumnTypeParser(("i", "string", "l",
                                                 {"key": "value"})))

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
          "depth": 0, "container": "iter", "custom_properties": {}},
         {"id": "b", "label": "b", "type": "timeofday",
          "depth": 0, "container": "iter", "custom_properties": {}}],
        DataTable.TableDescriptionParser([("a", "date"), ("b", "timeofday")]))

    self.assertEqual(
        [{"id": "a", "label": "a", "type": "string",
          "depth": 0, "container": "dict", "custom_properties": {}},
         {"id": "b", "label": "b", "type": "number",
          "depth": 1, "container": "iter", "custom_properties": {}},
         {"id": "c", "label": "column c", "type": "string",
          "depth": 1, "container": "iter", "custom_properties": {}}],
        DataTable.TableDescriptionParser({"a": [("b", "number"),
                                                ("c", "string", "column c")]}))

    self.assertEqual(
      [{"id": "a", "label": "column a", "type": "number", "depth": 0,
        "container": "dict", "custom_properties": {}},
       {"id": "b", "label": "column b", "type": "string", "depth": 0,
        "container": "dict", "custom_properties": {}}],
       DataTable.TableDescriptionParser({'a': ('number', 'column a'),
                                         'b': ('string', 'column b')}))

    self.assertEqual(
        [{"id": "a", "label": "column a", "type": "number",
          "depth": 0, "container": "dict", "custom_properties": {}},
         {"id": "b", "label": "b", "type": "number",
          "depth": 1, "container": "dict", "custom_properties": {}},
         {"id": "c", "label": "c", "type": "string",
          "depth": 1, "container": "dict", "custom_properties": {}}],
        DataTable.TableDescriptionParser({("a", "number", "column a"):
                                          {"b": "number", "c": "string"}}))

    self.assertEqual(
        [{"id": "a", "label": "column a", "type": "number",
          "depth": 0, "container": "dict", "custom_properties": {}},
         {"id": "b", "label": "column b", "type": "string",
          "depth": 1, "container": "scalar", "custom_properties": {}}],
        DataTable.TableDescriptionParser({("a", "number", "column a"):
                                          ("b", "string", "column b")}))

    # Cases that might create ambiguity
    self.assertEqual(
      [{"id": "a", "label": "column a", "type": "number", "depth": 0,
        "container": "dict", "custom_properties": {}}],
       DataTable.TableDescriptionParser({'a': ('number', 'column a')}))
    self.assertRaises(DataTableException, DataTable.TableDescriptionParser,
                      {'a': ('b', 'number')})

    self.assertEqual(
      [{"id": "a", "label": "a", "type": "string", "depth": 0,
        "container": "dict", "custom_properties": {}},
       {"id": "b", "label": "b", "type": "number", "depth": 1,
        "container": "scalar", "custom_properties": {}}],
       DataTable.TableDescriptionParser({'a': ('b', 'number', 'b', {})}))

    self.assertEqual(
      [{"id": "a", "label": "a", "type": "string", "depth": 0,
        "container": "dict", "custom_properties": {}},
       {"id": "b", "label": "b", "type": "number", "depth": 1,
        "container": "scalar", "custom_properties": {}}],
       DataTable.TableDescriptionParser({('a',): ('b', 'number')}))

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
    table = DataTable([("a", "number", "A'"), "b'", ("c", "timeofday")],
                      [[1],
                       [None, "z", time(1, 2, 3)],
                       [(2, "2$"), "w", time(2, 3, 4)]])
    self.assertEqual(3, table.NumberOfRows())
    self.assertEqual(("var mytab = new google.visualization.DataTable();\n"
                      "mytab.addColumn('number', \"A'\", 'a');\n"
                      "mytab.addColumn('string', \"b'\", \"b'\");\n"
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
    init_data_json = ("{cols:"
                      "[{id:'a',label:'A',type:'number'},"
                      "{id:'b',label:'b',type:'string'},"
                      "{id:'c',label:'c',type:'boolean'}],"
                      "rows:["
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

    cols_json = ("{cols:"
                 "[{id:'t',label:'T',type:'timeofday'},"
                 "{id:'d',label:'d',type:'date'},"
                 "{id:'dt',label:'dt',type:'datetime'}],")
    table = DataTable({("d", "date"): [("t", "timeofday", "T"),
                                       ("dt", "datetime")]})
    table.LoadData({date(1, 2, 3): [time(1, 2, 3)]})
    self.assertEqual(1, table.NumberOfRows())
    self.assertEqual(cols_json +
                     "rows:[{c:[{v:[1,2,3]},{v:new Date(1,1,3)},{v:null}]}]}",
                     table.ToJSon(columns_order=["t", "d", "dt"]))
    table.LoadData({date(2, 3, 4): [(time(2, 3, 4), "time 2 3 4"),
                                    datetime(1, 2, 3, 4, 5, 6)],
                    date(3, 4, 5): []})
    self.assertEqual(2, table.NumberOfRows())
    self.assertEqual((cols_json + "rows:["
                      "{c:[{v:[2,3,4],f:'time 2 3 4'},{v:new Date(2,2,4)},"
                      "{v:new Date(1,1,3,4,5,6)}]},"
                      "{c:[,{v:new Date(3,3,5)},{v:null}]}]}"),
                     table.ToJSon(columns_order=["t", "d", "dt"]))

    json = ("{cols:[{id:\"a'\",label:\"a'\",type:'string'},"
            "{id:'b',label:\"bb'\",type:'number'}],"
            "rows:[{c:[{v:'a1'},{v:1}]},{c:[{v:'a2'},{v:2}]},"
            "{c:[{v:'a3'},{v:3}]}]}")
    table = DataTable({"a'": ("b", "number", "bb'", {})},
                      {"a1": 1, "a2": 2, "a3": 3})
    self.assertEqual(3, table.NumberOfRows())
    self.assertEqual(json,
                     table.ToJSon())

  def testCustomProperties(self):
    # The json of the initial data we load to the table.
    json = ("{cols:"
            "[{id:'a',label:'A',type:'number',p:{'col_cp':'col_v'}},"
            "{id:'b',label:'b',type:'string'},"
            "{id:'c',label:'c',type:'boolean'}],"
            "rows:["
            "{c:[{v:1},,{v:null,p:{'null_cp':'null_v'}}],p:{'row_cp':'row_v'}},"
            "{c:[,{v:'z',p:{'cell_cp':'cell_v'}},{v:true}]},"
            "{c:[{v:3},,{v:null}],p:{'row_cp2':'row_v2'}}],"
            "p:{'global_cp':'global_v'}"
            "}")
    jscode = ("var mytab = new google.visualization.DataTable();\n"
              "mytab.setTableProperties({'global_cp':'global_v'});\n"
              "mytab.addColumn('number', 'A', 'a');\n"
              "mytab.setColumnProperties(0, {'col_cp':'col_v'});\n"
              "mytab.addColumn('string', 'b', 'b');\n"
              "mytab.addColumn('boolean', 'c', 'c');\n"
              "mytab.addRows(3);\n"
              "mytab.setCell(0, 0, 1);\n"
              "mytab.setCell(0, 2, null, null, {'null_cp':'null_v'});\n"
              "mytab.setRowProperties(0, {'row_cp':'row_v'});\n"
              "mytab.setCell(1, 1, 'z', null, {'cell_cp':'cell_v'});\n"
              "mytab.setCell(1, 2, true);\n"
              "mytab.setCell(2, 0, 3);\n"
              "mytab.setRowProperties(2, {'row_cp2':'row_v2'});\n")

    table = DataTable([("a", "number", "A", {"col_cp": "col_v"}), "b",
                       ("c", "boolean")],
                      custom_properties={"global_cp": "global_v"})
    table.AppendData([[1, None, (None, None, {"null_cp": "null_v"})]],
                     custom_properties={"row_cp": "row_v"})
    table.AppendData([[None, ("z", None, {"cell_cp": "cell_v"}), True], [3]])
    table.SetRowsCustomProperties(2, {"row_cp2": "row_v2"})
    self.assertEqual(json, table.ToJSon())
    self.assertEqual(jscode, table.ToJSCode("mytab"))

  def testToCsv(self):
    init_data_csv = "\n".join(['"A", "b", "c"',
                               '1, "", ""',
                               '"", "zz\'top", true'])
    table = DataTable([("a", "number", "A"), "b", ("c", "boolean")],
                      [[(1, "$1")], [None, "zz'top", True]])
    self.assertEqual(init_data_csv, table.ToCsv())
    table.AppendData([[-1, "w", False]])
    init_data_csv = "%s\n%s" % (init_data_csv, '-1, "w", false')
    self.assertEquals(init_data_csv, table.ToCsv())

    init_data_csv = "\n".join([
        '"T", "d", "dt"',
        '"[1,2,3]", "new Date(1,1,3)", ""',
        '"time ""2 3 4""", "new Date(2,2,4)", "new Date(1,1,3,4,5,6)"',
        '"", "new Date(3,3,5)", ""'])
    table = DataTable({("d", "date"): [("t", "timeofday", "T"),
                                       ("dt", "datetime")]})
    table.LoadData({date(1, 2, 3): [time(1, 2, 3)],
                    date(2, 3, 4): [(time(2, 3, 4), 'time "2 3 4"'),
                                    datetime(1, 2, 3, 4, 5, 6)],
                    date(3, 4, 5): []})
    self.assertEqual(init_data_csv, table.ToCsv(columns_order=["t", "d", "dt"]))

  def testToTsvExcel(self):
    table = DataTable({("d", "date"): [("t", "timeofday", "T"),
                                       ("dt", "datetime")]})
    table.LoadData({date(1, 2, 3): [time(1, 2, 3)],
                    date(2, 3, 4): [(time(2, 3, 4), 'time "2 3 4"'),
                                    datetime(1, 2, 3, 4, 5, 6)],
                    date(3, 4, 5): []})
    self.assertEqual(table.ToCsv().replace(", ", "\t").encode("UTF-16LE"),
                     table.ToTsvExcel())

  def testToHtml(self):
    html_table_header = "<html><body><table border='1'>"
    html_table_footer = "</table></body></html>"
    init_data_html = html_table_header + (
        "<thead><tr>"
        "<th>A&lt;</th><th>b&gt;</th><th>c</th>"
        "</tr></thead>"
        "<tbody>"
        "<tr><td>'$1'</td><td></td><td></td></tr>"
        "<tr><td></td><td>'&lt;z&gt;'</td><td>true</td></tr>"
        "</tbody>") + html_table_footer
    table = DataTable([("a", "number", "A<"), "b>", ("c", "boolean")],
                      [[(1, "$1")], [None, "<z>", True]])
    self.assertEqual(init_data_html.replace("\n", ""), table.ToHtml())

    init_data_html = html_table_header + (
        "<thead><tr>"
        "<th>T</th><th>d</th><th>dt</th>"
        "</tr></thead>"
        "<tbody>"
        "<tr><td>[1,2,3]</td><td>new Date(1,1,3)</td><td></td></tr>"
        "<tr><td>'time 2 3 4'</td><td>new Date(2,2,4)</td>"
        "<td>new Date(1,1,3,4,5,6)</td></tr>"
        "<tr><td></td><td>new Date(3,3,5)</td><td></td></tr>"
        "</tbody>") + html_table_footer
    table = DataTable({("d", "date"): [("t", "timeofday", "T"),
                                       ("dt", "datetime")]})
    table.LoadData({date(1, 2, 3): [time(1, 2, 3)],
                    date(2, 3, 4): [(time(2, 3, 4), "time 2 3 4"),
                                    datetime(1, 2, 3, 4, 5, 6)],
                    date(3, 4, 5): []})
    self.assertEqual(init_data_html.replace("\n", ""),
                     table.ToHtml(columns_order=["t", "d", "dt"]))

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
    default_params = (r"\s*'version'\s*:\s*'0.6'\s*,\s*'reqId'\s*:\s*'%s'\s*,"
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

  def testToResponse(self):
    description = ["col1", "col2", "col3"]
    data = [("1", "2", "3"), ("a", "b", "c"), ("One", "Two", "Three")]
    table = DataTable(description, data)

    self.assertEquals(table.ToResponse(), table.ToJSonResponse())
    self.assertEquals(table.ToResponse(tqx="out:csv"), table.ToCsv())
    self.assertEquals(table.ToResponse(tqx="out:html"), table.ToHtml())
    self.assertRaises(DataTableException, table.ToResponse, tqx="version:0.1")
    self.assertEquals(table.ToResponse(tqx="reqId:4;responseHandler:handle"),
                      table.ToJSonResponse(req_id=4, response_handler="handle"))
    self.assertEquals(table.ToResponse(tqx="out:csv;reqId:4"), table.ToCsv())
    self.assertEquals(table.ToResponse(order_by="col2"),
                      table.ToJSonResponse(order_by="col2"))
    self.assertEquals(table.ToResponse(tqx="out:html",
                                       columns_order=("col3", "col2", "col1")),
                      table.ToHtml(columns_order=("col3", "col2", "col1")))
    self.assertRaises(ValueError, table.ToResponse, tqx="SomeWrongTqxFormat")
    self.assertRaises(DataTableException, table.ToResponse, tqx="out:bad")


if __name__ == "__main__":
  unittest.main()
