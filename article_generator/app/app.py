from article_generator.data.db_details import DbName, get_components_list, ArxivDbQuery
from article_generator.data.data_extractor import DataExtractor
import pandas as pd

# TODO: Change to dynamicly changing list
components_list = get_components_list(DbName.arxiv, "cs")
queries = set()
for component in components_list:
    queries.add(ArxivDbQuery("cat:{}".format(component), from_date="2020-05-22"))

data = DataExtractor(DbName.arxiv).add_queries(queries).query_db().download_papers().get_queries_results()

# TODO: Decide what text files need to be used and add them as properties on data object

# Usage example
cols = tuple(list(data)[0].keys())
df = pd.DataFrame(data, columns=cols)