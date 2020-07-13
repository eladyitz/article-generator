import pandas as pd
import os
from IPython.display import display
from article_generator.data.db_details import DbName, DataActions, get_components_list, ArxivDbQuery
from article_generator.data.data_extractor import get_data_from_db


papers_folder = "papers"
components_list = get_components_list(DbName.arxiv, "cs") # AI
queries = set()
for component in components_list:
    queries.add(ArxivDbQuery("cat:{}".format(component), from_date="2017-06-03", max_results=5)) # 3 years

data = get_data_from_db(DbName.arxiv, queries, DataActions.metadata_and_files_content, folder=papers_folder)

# data can be used as data frame
cols = tuple(list(data)[0].keys())
df = pd.DataFrame(data, columns=cols)

print("########################################## Summary ##########################################")
display(df["journal_reference"].value_counts(dropna=False))
print("#############################################################################################")

df.to_excel(os.path.join(papers_folder, "articles_data.xlsx"))

# This is section 2
# TODO: Add statistics here