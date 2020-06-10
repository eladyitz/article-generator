import shutil
import tarfile
from urllib.request import urlretrieve

import arxiv
import concurrent.futures
import os
from datetime import datetime
from time import mktime
from article_generator.data.db_details import DbName, DataActions, ArxivDbQuery
from article_generator.data.data_parser import consolidate_papers


def get_data_from_db(db_name, queries, data_action, delete_files=True):
    if not issubclass(db_name.__class__, DbName) and issubclass(data_action.__class__, DataActions):
        raise Exception("DB name {} and Data action {} must be allowed".format(db_name), data_action)

    if not db_name == DbName.arxiv and len(queries) > 0 and len(
            [query for query in queries if issubclass(query.__class__, ArxivDbQuery)]) is not len(queries):
        raise Exception("DB name {} and queries type {} must be allowed".format(db_name), data_action)

    if data_action == DataActions.metadata_only:
        return _get_meta_data(queries)
    elif data_action == DataActions.download_files_only:
        papers_metadata = _get_meta_data(queries)
        return _download_papers(papers_metadata)
    elif data_action == DataActions.metadata_and_files_content:
        papers_metadata = _get_meta_data(queries)
        papers_downloaded_folder = _download_papers(papers_metadata)
        papers_metadata = _add_text_to_metadata(papers_metadata)
        if delete_files:
            shutil.rmtree(papers_downloaded_folder)
        return papers_metadata
    elif data_action == DataActions.test_parser:
        papers_metadata = _get_meta_data(queries)
        papers_metadata = _add_text_to_metadata(papers_metadata)
        return papers_metadata

def _get_meta_data(queries):
    queries_results = set()

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(queries)) as query_puller:
        future_to_query = {query_puller.submit(_query, query): query for query in queries}

        for future_query_result in concurrent.futures.as_completed(future_to_query):
            query_details = future_to_query[future_query_result]
            try:
                query_data = future_query_result.result()
                queries_results.update(query_data)
            except Exception as exc:
                print('query {} returned exception {}'.format(query_details, exc))

        return queries_results


# TODO: Change to https://github.com/Mahdisadjadi/arxivscraper
# Using http://export.arxiv.org/oai2
def _query(query):
    print("Querying DB with {}".format(query))
    query_result = arxiv.query(
        query=query.query,
        id_list=query.id_list,
        max_results=query.max_results,
        start=query.start,
        sort_by=query.sort_by,
        sort_order=query.sort_order,
        prune=query.prune,
        max_chunk_results=query.max_chunk_results
    )

    query_result = list(filter(
        lambda result: query.from_date <= datetime.fromtimestamp(mktime(result['published_parsed'])) <= query.to_date,
        query_result))
    print("Query Successfully retrieved and filtered!")

    return query_result


def _download_papers(papers_metadata, path="./papers"):
    _clean_workspace(path)

    with concurrent.futures.ThreadPoolExecutor() as paper_downloader:
        future_to_paper = {
            paper_downloader.submit(_download_paper, paper, path): paper for paper in papers_metadata
        }

        for future_paper_result in concurrent.futures.as_completed(future_to_paper):
            paper_metadata = future_to_paper[future_paper_result]
            try:
                paper_full_path = future_paper_result.result()
                papers_metadata.remove(paper_metadata)
                paper_metadata['paper_full_path'] = paper_full_path
                papers_metadata.add(paper_metadata)
            except Exception as exc:
                print('paper {} download returned exception {} after many attempts'.format(paper_metadata["id"], exc))
                papers_metadata.remove(paper_metadata)

        return path


def _download_paper(paper, path):
    success = False
    attempts = 0
    while not success and attempts <= 3:
        try:
            url = paper['pdf_url'].replace("http://arxiv.org/pdf", "https://export.arxiv.org/e-print")
            path = "{}.tar.gz".format(os.path.join(path, paper['id'].split('/')[-1]))
            urlretrieve(url, path)
            success = True
            print('paper {} downloaded'.format(url))
        except Exception as exc:
            attempts += 1
            print('paper {} download returned exception {} after {} attempts'.format(url, exc, attempts))

    return path


def _clean_workspace(path):
    try:
        shutil.rmtree(path)
        os.mkdir(path)
    except OSError as e:
        print("Cant delete dir {}, {}".format(path, e.strerror))
        os.mkdir(path)


def _untar_paper_zip(paper):
    # TODO: Handle more formats and uknown format before download issue
    print("unzipping file {}".format(paper['paper_full_path']))
    try:
        my_tar = tarfile.open(paper['paper_full_path'])
        extracted_folder = "{}_{}".format(paper['paper_full_path'], "extracted")
        os.mkdir(extracted_folder)
        my_tar.extractall(extracted_folder)
        my_tar.close()
        os.remove(paper['paper_full_path'])
        print("file {} extracted to folder {}".format(paper['paper_full_path'], extracted_folder))
        return True
    except Exception as exc:
        print("file {} cant be unzipped, might not be tar.gz".format(paper['paper_full_path']))
        return False


def _add_text_to_metadata(papers_metadata):
    for paper in papers_metadata:
        if _untar_paper_zip(paper):
            paper_folder_name = "{}_{}".format(paper['paper_full_path'], "extracted")
            files_in_directory = os.listdir(paper_folder_name)
            tex_filtered_files = [file for file in files_in_directory if file.endswith(".tex")]
            paper["paper_text"] = consolidate_papers(tex_filtered_files, paper_folder_name)
    
    return papers_metadata