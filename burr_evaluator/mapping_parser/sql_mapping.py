from burr_evaluator.mapping_parser.sql_mapping import SQLAttribute, Join, Condition


import re


def sql_attribute_equal(sql_attribute1, sql_attribute2): sql_attribute1.table == sql_attribute2.table and sql_attribute1.attribute == sql_attribute2.attribute
def join_equal(join1, join2): sql_attribute_equal(join1.left_attribute, join2.left_attribute) and sql_attribute_equal(join1.right_attribute, join2.right_attribute) or sql_attribute_equal(join1.left_attribute, join2.right_attribute) and sql_attribute_equal(join1.right_attribute, join2.left_attribute)
def condition_equal(condition1: Condition, condition2: Condition): sql_attribute_equal(condition1.sql_attribute, condition2.sql_attribute) and condition1.operator == condition2.operator and condition1.value == condition2.value
