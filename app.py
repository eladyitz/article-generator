import datetime
import pandas as pd
import os
from IPython.display import display
from article_generator.data.db_details import DbName, DataActions, get_components_list, ArxivDbQuery
from article_generator.data.data_extractor import get_data_from_db
from article_generator.data.data_coverter import DataConverter


papers_folder = "papers"
max_results = 50
years_ago = 3
from_date = datetime.datetime.now() - datetime.timedelta(days=years_ago*365)

components_list = get_components_list(DbName.arxiv, "cs") # AI
queries = set()
for component in components_list:
    queries.add(ArxivDbQuery("cat:{}".format(component), from_date=from_date, max_results=max_results)) # 3 years

data = get_data_from_db(DbName.arxiv, queries, DataActions.metadata_and_files_content, folder=papers_folder)

# data can be used as data frame
cols = tuple(list(data)[0].keys())
df = pd.DataFrame(data, columns=cols)

print("########################################## Summary ##########################################")
display(df["journal_reference"].value_counts(dropna=False))
print("#############################################################################################")

df.to_excel(os.path.join(papers_folder, "articles_data.xlsx"))

dataConverter = DataConverter(os.path.join(papers_folder, "articles_data.xlsx"))
print(dataConverter.getTextToColorDictionary())
print(len(dataConverter.getTextToColorDictionary()))
print(dataConverter.getColorToTextDictionary())
print(len(dataConverter.getColorToTextDictionary()))
dataConverter.convertTextsToColorImages()

dataConverter.convertColorImageToText(os.path.join(papers_folder, "2007_15543v1.tar.gz.jpg"), os.path.join(papers_folder, "test.tex"))
