from rdflib import Graph, URIRef
from typing import List
import os
from burr_evaluator.mapping_parser.classmap import ClassMap
from burr_evaluator.mapping_parser.relation import Relation
from burr_evaluator.mapping_parser.translationtable import TranslationTable
from burr_evaluator.mapping_parser.mapping.BaseMapping import BaseMapping
import logging
import wandb

class D2RQMapping(BaseMapping):
    def __init__(self, mapping_content, database, meta) -> None:
        logging.getLogger("rdflib.term").setLevel(logging.ERROR)
        super().__init__(mapping_content, database, meta)

    def parse_mapping(self, mapping_content):
        self.graph = Graph()
        if os.path.isfile(mapping_content):
            self.graph.parse(mapping_content)
        else:
            with open("temp_mapping_file.ttl", "w") as f:
                f.write(mapping_content)
            wandb.save("temp_mapping_file.ttl")
            self.graph.parse(data=mapping_content, format="turtle")
        self.classes = self.parse_classes()
        self.relations = self.parse_relations()
        self.translation_tables = []
        self.parse_translation_tables()

        # for class_ in self.get_classes():
        #     self.convert_subclass_to_relations(class_) 
    
    def get_context_elements(self, schema_element):
        if schema_element in self.classes:
            return self.get_classes_connected_to_class(schema_element)
        elif schema_element in self.relations:
            return self.get_relations_connected_to_relation(schema_element)
        else:
            raise Exception("Schema element not found in mapping")

    # def _mapping_id_to_class(self, id, attribute="mapping_id"):
    #     for class_ in self.classes:
    #         if getattr(class_, attribute) == id:
    #             return class_
    #     return None 
    
    def get_classes_connected_to_class(self, class_: ClassMap):
        outgoing_classes = [relation.refersToClassMap for relation in self.relations if relation.belongsToClassMap == class_]
        ingoing_classes = [relation.belongsToClassMap for relation in self.relations if relation.refersToClassMap == class_]
        return list(set(outgoing_classes + ingoing_classes))

    def get_relations_connected_to_relation(self, relation: Relation):
        def mapping_id_to_relation(mapping_id):
            for rel in self.relations:
                if rel.mapping_id == mapping_id:
                    return rel
            return None
        relations = list(set(self.relations) - set([relation]))
        relations_of_outgoing_class = [mapping_id_to_relation(rel.mapping_id) for rel in relations if rel.belongsToClassMap == relation.belongsToClassMap or rel.refersToClassMap == relation.belongsToClassMap]
        relations_of_ingoing_class = [mapping_id_to_relation(rel.mapping_id) for rel in relations if rel.belongsToClassMap == relation.refersToClassMap or rel.refersToClassMap == relation.refersToClassMap]
        return list(set(relations_of_outgoing_class + relations_of_ingoing_class))
    
    def parse_classes(self) -> List[str]:
        classes = []
        properties = ["d2rq:uriPattern", "d2rq:class", "d2rq:join", "d2rq:bNodeIdColumns", "d2rq:additionalClassDefinitionProperty", "d2rq:condition", "d2rq:translateWith"]
        class_maps = self.query_properties("ClassMap", properties)
        for class_map in class_maps:
            parent_classes = []
            if "d2rq:additionalClassDefinitionProperty" in class_map.keys():
                print("ADDITIONAL CLASS DEFINITION PROPERTY", class_map["d2rq:additionalClassDefinitionProperty"])
                if isinstance(class_map["d2rq:additionalClassDefinitionProperty"], list):
                    for el in class_map["d2rq:additionalClassDefinitionProperty"]:
                        parent_classes.append(self.shorten_uri(self.parse_additionalClassDefinitionProperty(el)))
                else:
                    parent_classes = [self.shorten_uri(self.parse_additionalClassDefinitionProperty(class_map["d2rq:additionalClassDefinitionProperty"]))]
            classes.append(ClassMap(
                        #fix first three
                        prefix="base",
                        datastorage="database",
                        translate_with=self.shorten_uri(class_map["d2rq:translateWith"]) if "d2rq:translateWith" in class_map.keys() else None,
                        mapping_id=self.shorten_uri(class_map["mapping_id"]),
                        bNodeIdColumns=class_map["d2rq:bNodeIdColumns"] if "d2rq:bNodeIdColumns" in class_map.keys() else None,
                        uriPattern=class_map["d2rq:uriPattern"] if "d2rq:uriPattern" in class_map.keys() else None,
                        class_uri=self.shorten_uri(class_map["d2rq:class"]) if "d2rq:class" in class_map.keys() else None,
                        #additionalClassDefinitionProperty=class_map["d2rq:additionalClassDefinitionProperty"] if "d2rq:additionalClassDefinitionProperty" in class_map.keys() else None,
                        join=class_map["d2rq:join"] if "d2rq:join" in class_map.keys() else None,
                        condition=class_map["d2rq:condition"] if "d2rq:condition" in class_map.keys() else None,
                        parent_classes=parent_classes,
                        #graph = self.graph
                        ))
                        
        return classes    

    def parse_translation_tables(self):
        sparql_query = """
        SELECT ?table ?databaseValue ?rdfValue
        WHERE {
            ?table a d2rq:TranslationTable ;
                d2rq:translation ?translation .
            ?translation d2rq:databaseValue ?databaseValue ;
                        d2rq:rdfValue ?rdfValue .
        }
        """
        results = self.graph.query(sparql_query)
        table_data = {}
        for row in results:
            table_name = self.shorten_uri(row.table)
            translation_entry = {
                "databaseValue": str(row.databaseValue),
                "targetValue": str(row.rdfValue)
            }
            if table_name not in table_data:
                table_data[table_name] = {
                    "name": table_name,
                    "translations": []
                }
            table_data[table_name]["translations"].append(translation_entry)
        for table in table_data.values():
            self.translation_tables.append(TranslationTable(table["name"], table["translations"]))

    def parse_additionalClassDefinitionProperty(self, uri):
        query = f"""             
            SELECT DISTINCT ?class
            WHERE {{ {uri} d2rq:propertyValue ?class. }}
        """
        res = [obj[0].n3() for obj in self.graph.query(query)]
        return res if len(res)>1 else res[0]

    def parse_relations(self):
        relations = []
        properties = ["d2rq:property", "d2rq:belongsToClassMap", "d2rq:dynamicProperty", "d2rq:pattern", "d2rq:translateWith", "d2rq:refersToClassMap", "d2rq:join", "d2rq:column","d2rq:uriPattern", "d2rq:sqlExpression", "d2rq:constantValue", "d2rq:condition"]
        property_bridges = self.query_properties("PropertyBridge", properties)
        for property_bridge in property_bridges:
            if "d2rq:column" not in property_bridge.keys():
                relations.append(Relation(
                        prefix="base",
                        mapping_id=self.shorten_uri(property_bridge["mapping_id"]),
                        property=self.shorten_uri(property_bridge["d2rq:property"]) if "d2rq:property" in property_bridge.keys() else None,
                        dynamic_property=self.shorten_uri(property_bridge["d2rq:dynamicProperty"]) if "d2rq:dynamicProperty" in property_bridge.keys() else None,
                        pattern = property_bridge["d2rq:pattern"] if "d2rq:pattern" in property_bridge.keys() else None,
                        uriPattern = property_bridge["d2rq:uriPattern"] if "d2rq:uriPattern" in property_bridge.keys() else None,
                        translate_with=self.shorten_uri(property_bridge["d2rq:translateWith"]) if "d2rq:translateWith" in property_bridge.keys() else None,
                        belongsToClassMap=self._mapping_id_to_class(self.shorten_uri(property_bridge["d2rq:belongsToClassMap"])) if "d2rq:belongsToClassMap" in property_bridge.keys() else None,
                        refersToClassMap=self._mapping_id_to_class(self.shorten_uri(property_bridge["d2rq:refersToClassMap"])) if "d2rq:refersToClassMap" in property_bridge.keys() else None,
                        constantValue=self.shorten_uri(property_bridge["d2rq:constantValue"]) if "d2rq:constantValue" in property_bridge.keys() else None,
                        sqlExpression=property_bridge["d2rq:sqlExpression"] if "d2rq:sqlExpression" in property_bridge.keys() else None,
                        join=property_bridge["d2rq:join"] if "d2rq:join" in property_bridge.keys() else None,
                        column=None,
                        condition=property_bridge["d2rq:condition"] if "d2rq:condition" in property_bridge.keys() else None,
                    ))
                continue
            if "d2rq:column" in property_bridge.keys() and isinstance(property_bridge["d2rq:column"], list):
                columns = property_bridge["d2rq:column"]
            else:
                columns = [property_bridge["d2rq:column"]] if "d2rq:column" in property_bridge.keys() else None
            for column in columns:
                relations.append(Relation(
                        prefix="base",
                        mapping_id=self.shorten_uri(property_bridge["mapping_id"]),
                        property=self.shorten_uri(property_bridge["d2rq:property"]) if "d2rq:property" in property_bridge.keys() else None,
                        dynamic_property=self.shorten_uri(property_bridge["d2rq:dynamicProperty"]) if "d2rq:dynamicProperty" in property_bridge.keys() else None,
                        pattern = property_bridge["d2rq:pattern"] if "d2rq:pattern" in property_bridge.keys() else None,
                        translate_with=self.shorten_uri(property_bridge["d2rq:translateWith"]) if "d2rq:translateWith" in property_bridge.keys() else None,
                        belongsToClassMap=self._mapping_id_to_class(self.shorten_uri(property_bridge["d2rq:belongsToClassMap"])) if "d2rq:belongsToClassMap" in property_bridge.keys() else None,
                        refersToClassMap=self._mapping_id_to_class(self.shorten_uri(property_bridge["d2rq:refersToClassMap"])) if "d2rq:refersToClassMap" in property_bridge.keys() else None,
                        constantValue=self.shorten_uri(property_bridge["d2rq:constantValue"]) if "d2rq:constantValue" in property_bridge.keys() else None,
                        sqlExpression=property_bridge["d2rq:sqlExpression"] if "d2rq:sqlExpression" in property_bridge.keys() else None,
                        join=property_bridge["d2rq:join"] if "d2rq:join" in property_bridge.keys() else None,
                        column=column,
                        condition=property_bridge["d2rq:condition"] if "d2rq:condition" in property_bridge.keys() else None,
                    ))
        return relations

    def convert_subclass_to_relations(self, class_: ClassMap):
        for idx, parent_map in enumerate(class_.parent_classes) if class_.parent_classes is not None else []:
            parent_class = self._mapping_id_to_class(self.shorten_uri(parent_map), "class_uri")
            self.relations.append(
                Relation(
                    prefix="base",
                    mapping_id=f"{parent_class.mapping_id}_{class_.mapping_id}_{idx}" if parent_class is not None else self.shorten_uri(parent_map),
                    property="subclassOf",
                    belongsToClassMap=class_,
                    refersToClassMap=parent_class if parent_class is not None else self.shorten_uri(parent_map),
                    join=None,
                    column=None,
                )
            )

    def expand_uri(self, prefixed_uri, graph):
        prefix, name = prefixed_uri.split(":", 1)
        namespace = dict(graph.namespaces()).get(prefix)
        if namespace:
            return URIRef(namespace + name)
        else:
            raise ValueError(f"Prefix '{prefix}' not found in the graph namespaces.")

    def set_eq_strategy(self, classes=False):
        for relation in self.relations:
            relation.set_eq_strategy(classes)

    def set_concept_eq_strategy(self, name_based=False):
        [classmap.set_eq_strategy(name_based) for classmap in self.classes]

    def get_attributes(self):
        return list(filter(lambda rel: rel.refersToClassMap is None, self.relations))
    
    def get_relations(self):
        return list(filter(lambda rel: rel.refersToClassMap is not None, self.relations))

    def query_properties(self, id, properties):
        result = []
        query = f"""             
            SELECT DISTINCT ?mapping_id
            WHERE {{ ?mapping_id a d2rq:{id}. }}
        """

        ids = [obj[0].n3() for obj in self.graph.query(query)]
        query_properties = lambda uri, property: f"""             
            SELECT DISTINCT ?classes
            WHERE {{ {uri} {property} ?classes. }}
        """
        for id in ids:
            temp = {}
            for property in properties:
                res = self.graph.query(query_properties(id, property))
                if len(res) == 1:
                    for obj in res:
                        temp[property] = obj[0].n3().replace('"', "")
                elif len(res) > 1:
                    objects_of_property = []
                    for obj in res:
                        objects_of_property.append(obj[0].n3().replace('"', ""))
                    temp[property] = objects_of_property
            temp["mapping_id"] = id
            result.append(temp)
        return result
    
    def get_attribute_from_mapping(self, attribute, table):
        for class_ in self.classes:
            if class_.sql_uri_pattern.table == table and class_.sql_uri_pattern.attribute == attribute:
                return class_
        return None