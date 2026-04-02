from abc import ABC, abstractmethod
from rdflib import URIRef
from urllib.parse import urlparse


from burr_evaluator.utils.get_jinja_env import get_jinja_env


class BaseMapping(ABC):
    def __init__(self, mapping_content, database, meta):
        self.classes = []
        self.relations = []
        self.translation_tables = []
        self.meta = meta
        self.parse_mapping(mapping_content)
        self.mapping_content = mapping_content
        self.database = database
    
    @abstractmethod
    def parse_mapping(self):
        raise NotImplementedError
    
    def get_classes(self):
        return self.classes
    
    def _mapping_id_to_class(self, id, attribute="mapping_id"):
        for class_ in self.classes:
            if getattr(class_, attribute) == id:
                return class_
        return None
    
    def shorten_uri(self, uri):
        uri = str(URIRef(uri)).replace("<", "").replace(">", "").replace(" ", "")#.replace("#", "")
        most_specific_namespace = ""
        for _, namespace in self.graph.namespaces():
            # if urlparse(uri).path.strip("/") == "":
            #     continue
            # namespace_parsed = "/".join(urlparse(namespace).path.strip("/").split("/")[:-1])
            # uri_parsed = "/".join(urlparse(uri).path.strip("/").split("/")[:-1])
            # if namespace_parsed == uri_parsed:
            #     return urlparse(uri).path.strip("/").split("/")[-1]
            if str(uri).startswith(namespace):
                if len(namespace.split("/")) > len(most_specific_namespace.split("/")):
                    most_specific_namespace = namespace
        if most_specific_namespace != "":
            return str(uri)[len(most_specific_namespace):]
        if "#" in uri:
            short_uri = uri.split("#")[-1]
        else:
            short_uri = uri.split("/")[-1]
        print("WARNING - URI could not be shortened: ", uri, " - returning last part of URI, divided by / or #: ", short_uri)
        return short_uri
    
    def create_ttl_string(self, database):
        output = ""
        output += self.build_meta_data(database)
        for _cls in self.classes:
            output += _cls.get_ttl_string()
        for prop in self.get_relations():
            output += prop.get_d2rq_mapping()
        for attr in self.get_attributes():
            output += attr.get_d2rq_mapping()
        for translation_table in self.translation_tables:
            #print("TRANSLATION TABLE", translation_table)
            output += str(translation_table)
        return output

    def build_meta_data(self, database): return get_jinja_env().get_template('meta.j2').render(prefixes=self.meta["prefixes"], database=database, database_username="lukaslaskowski") 
