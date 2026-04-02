import os
import json
import os
from rdflib import Graph

from burr_evaluator.mapping_parser.classmap import ClassMap
from burr_evaluator.mapping_parser.relation import Relation
from burr_evaluator.mapping_parser.translationtable import TranslationTable
from burr_evaluator.mapping_parser.mapping.D2RQMapping import D2RQMapping
from burr_evaluator.mapping_parser.mapping.BaseMapping import BaseMapping


class JsonMapping(BaseMapping):
    def __init__(self, mapping_content, database, meta) -> None:
        self.meta = meta
        self.database = database
        super().__init__(mapping_content, database, meta)
        # self.meta = self.parse_meta(meta, is_directory) #is this really mapping_file?
        self.ttl = self.create_ttl_string(self.database)

    def parse_mapping(self, data):
        for _cls in data["classes"]:
            self.classes.append(self.parse_class_entry(_cls))
        
        mapping_id_counts = {}
        
        for data_prop in data["data_properties"]:
            attribute = self.parse_property_bridge_entry(data_prop, self.meta["relation_prefix"], mapping_id_counts)
            self.relations.append(attribute)
        for obj_prop in data["object_properties"]:
            property = self.parse_property_bridge_entry(obj_prop, self.meta["relation_prefix"], mapping_id_counts)
            self.relations.append(property)
        for translation_table in data["translation_tables"] if "translation_tables" in data else []:
            translation_table = self.parse_translation_table(translation_table)
            self.translation_tables.append(translation_table)
            
    def get_attributes(self):
        return list(filter(lambda rel: rel.refersToClassMap is None, self.relations))
    
    def get_relations(self):
        return list(filter(lambda rel: rel.refersToClassMap is not None, self.relations)) 
    def parse_meta(self, directory):
        meta_file = os.path.join(directory, "meta.json")
        meta_file = meta_file if os.path.exists(meta_file) else './evaluator/mapping_parser/d2rq_mapping/base_meta.json'
        with open(meta_file, 'r') as f:
            meta = json.load(f)
        return meta
    
    def write_to_file(self, output_file):
        graph = Graph().parse(data=self.create_ttl_string(self.meta, self.database), format="turtle")
        graph.serialize(destination=output_file, format="turtle")
    
    def to_D2RQ_Mapping(self):
        x = self.create_ttl_string(self.database)
        with open("output.ttl", "w") as f:
            f.write(x)
        print("[JsonMapping] Converting JsonMapping to D2RQMapping...")
        # print(x)
        d2rq_map = D2RQMapping(x, self.database, self.meta)
        
        return d2rq_map

    
    def parse_translation_table(self, table):
        return TranslationTable(mapping_name=table["name"], translation_table=table["translations"])

    def parse_class_entry(self, entry):
        mapping_name = entry["name"] if "name" in entry else entry["class"]
        cls_ = entry["class"]
        bNodeIdColumns = entry["bNodeIdColumns"] if "bNodeIdColumns" in entry else None
        uri_pattern = entry["id"].lower()
        prefix = entry["prefix"].lower() if "prefix" in entry else "base"
        conditions = entry["condition"] if "condition" in entry else None
        joins = entry["join"] if "join" in entry else None
        translate_with = entry["translateWith"] if "translateWith" in entry else None
        parent_classes = entry["subClassOf"] if "subClassOf" in entry else None
        datastorage = "database"
        confidence = entry.get("confidence")
        cot_prob = entry.get("cot_prob")
        combined_prob = entry.get("combined_prob")
        return ClassMap(mapping_id=mapping_name, prefix=prefix, bNodeIdColumns=bNodeIdColumns, class_uri=cls_, uriPattern=uri_pattern, condition=conditions, join=joins, datastorage=datastorage, parent_classes=parent_classes, translate_with=translate_with, confidence=confidence, cot_prob=cot_prob, combined_prob=combined_prob)

    def parse_property_bridge_entry(self, entry, prefix, mapping_id_counts=None):
        refers_to_class_map = None
        if "refersToClass" in entry or "refersToClassMap" in entry:
            refers_to_class_map = entry["refersToClass"] if "refersToClass" in entry else entry["refersToClassMap"]
        belongs_to_class_map = entry["belongsToClass"] if "belongsToClass" in entry else entry["belongsToClassMap"]
        index = entry["index"] if "index" in entry else None
        mapping_name = f"{entry['property']}_{belongs_to_class_map}_{refers_to_class_map}" + (f"_{index}" if index else "")
        mapping_name = entry["mapping_id"] if "mapping_id" in entry else mapping_name
        
        if mapping_id_counts is not None:
            if mapping_name in mapping_id_counts:
                mapping_id_counts[mapping_name] += 1
                mapping_name = f"{mapping_name}_{mapping_id_counts[mapping_name]}"
            else:
                mapping_id_counts[mapping_name] = 0
        
        property = entry["property"]
        joins = entry["join"] if "join" in entry else None
        pattern = entry["pattern"] if "pattern" in entry else None
        conditions = entry["condition"] if "condition" in entry else None
        column = entry["column"].lower() if "column" in entry else None
        datatype = entry["datatype"] if "datatype" in entry else None
        inverse_of = None#entry["inverseOf"] if "inverseOf" in entry else None
        sqlExpression = entry["sqlExpression"] if "sqlExpression" in entry else None
        translate_with = entry["translateWith"] if "translateWith" in entry else None
        constant_value = entry["constantValue"] if "constantValue" in entry else None#
        return Relation(prefix=prefix, mapping_id=mapping_name, property=property, pattern=pattern, constantValue=constant_value,belongsToClassMap=belongs_to_class_map, refersToClassMap=refers_to_class_map, join=joins, condition=conditions, column=column, datatype=datatype, inverse_of=inverse_of, translate_with=translate_with, sqlExpression=sqlExpression)#.get_d2rq_mapping()

