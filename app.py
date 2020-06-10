from article_generator.data.db_details import DbName, DataActions, get_components_list, ArxivDbQuery
from article_generator.data.data_extractor import get_data_from_db

# TODO: Change to dynamicly changing list
components_list = get_components_list(DbName.arxiv, "cs") # AI
queries = set()
for component in components_list:
    queries.add(ArxivDbQuery("cat:{}".format(component), from_date="2017-06-03", max_results=10)) # 3 years

data = get_data_from_db(DbName.arxiv, queries, DataActions.metadata_and_files_content, delete_files=False)

# Usage example
#cols = tuple(list(data)[0].keys())
#df = pd.DataFrame(data, columns=cols)