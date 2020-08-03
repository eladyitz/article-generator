import concurrent.futures
import datetime
import os
import re
import shutil
import tarfile
from urllib.request import urlretrieve

import arxiv
from time import mktime

from alive_progress import alive_bar

from article_generator.data.data_parser import consolidate_papers
from article_generator.data.db_details import DbName, DataActions, ArxivDbQuery


def get_data_from_db(db_name, queries, data_action, folder):
    if not issubclass(db_name.__class__, DbName) and issubclass(data_action.__class__, DataActions):
        raise Exception("DB name {} and Data action {} must be allowed".format(db_name), data_action)

    if not db_name == DbName.arxiv and len(queries) > 0 and len(
            [query for query in queries if issubclass(query.__class__, ArxivDbQuery)]) is not len(queries):
        raise Exception("DB name {} and queries type {} must be allowed".format(db_name), data_action)

    if data_action == DataActions.metadata_only:
        return _get_meta_data(queries)
    elif data_action == DataActions.download_files_only:
        papers_metadata = _get_meta_data(queries)
        return _download_papers(papers_metadata, folder)
    elif data_action == DataActions.metadata_and_files_content:
        papers_metadata = _get_meta_data(queries)
        _download_papers(papers_metadata, folder)
        papers_metadata = _add_text_to_metadata(papers_metadata)
        return papers_metadata
    elif data_action == DataActions.test_parser:
        papers_metadata = _get_meta_data(queries)
        papers_metadata = _add_text_to_metadata(papers_metadata)
        return papers_metadata


def _get_meta_data(queries):
    queries_results = set()

    with alive_bar(len(queries)) as bar:
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(queries)) as query_puller:
            future_to_query = {query_puller.submit(_query, query): query for query in queries}

            for future_query_result in concurrent.futures.as_completed(future_to_query):
                query_details = future_to_query[future_query_result]
                try:
                    query_data = future_query_result.result()
                    queries_results.update(query_data)
                except Exception as exc:
                    print('query {} returned exception {}'.format(query_details, exc))
                bar()

        return queries_results


# TODO: Change to https://github.com/Mahdisadjadi/arxivscraper
# Using http://export.arxiv.org/oai2
def _query(query):
    print("######################### Querying DB #################################")
    print()
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
        lambda result: query.from_date <= datetime.datetime.fromtimestamp(mktime(result['published_parsed'])) <= query.to_date,
        query_result))
    print("Query Successfully retrieved and filtered!")
    print()
    return query_result


def _download_papers(papers_metadata, path):
    _clean_workspace(path)

    print("####################### Download Articles ###################################")
    print()
    papers_counter = 0
    with alive_bar(len(papers_metadata)) as bar:
        with concurrent.futures.ThreadPoolExecutor() as paper_downloader:
            future_to_paper = {
                paper_downloader.submit(_download_paper, paper, path): paper for paper in papers_metadata
            }

            for future_paper_result in concurrent.futures.as_completed(future_to_paper):
                paper_metadata = future_to_paper[future_paper_result]
                try:
                    download_details = future_paper_result.result()
                    paper_metadata['paper_prefix_path'] = path
                    paper_metadata['paper_file_name'] = download_details["file_name"]
                    paper_metadata['paper_full_path'] = download_details["file_path"]
                    papers_metadata.add(paper_metadata)
                    papers_counter += 1
                except Exception as exc:
                    print("Cant download {} because {}".format(download_details["url"], exc))
                    paper_metadata['for_deletion'] = True
                bar()

        print("Papers downloaded {}".format(papers_counter))
        print()
        return path


def _download_paper(paper, path):
    success = False
    attempts = 0
    while not success and attempts <= 3:
        try:
            url = paper['pdf_url'].replace("http://arxiv.org/pdf", "https://export.arxiv.org/e-print")
            file_name = "{}.tar.gz".format(paper['id'].split('/')[-1].replace(".", "_"))
            file_path = os.path.join(path, file_name)
            urlretrieve(url, file_path)
            success = True
        except Exception as exc:
            attempts += 1

    return {"url": url, "file_name": file_name, "file_path": file_path}


def _clean_workspace(path):
    if os.path.exists(path):
        try:
            shutil.rmtree(path)
        except OSError as e:
            print("Cant delete dir {}, {}".format(path, e.strerror))
    os.mkdir(path)


def _untar_paper_zip(paper):
    extracted_folder = "{}_{}".format(paper['paper_full_path'], "extracted")
    try:
        my_tar = tarfile.open(paper['paper_full_path'])
        os.mkdir(extracted_folder)
        my_tar.extractall(extracted_folder)
        my_tar.close()
        os.remove(paper['paper_full_path'])
        paper['paper_full_path'] = extracted_folder
        return True
    except Exception as exc:
        if os.path.exists(paper['paper_full_path']):
            os.remove(paper['paper_full_path'])
        if os.path.exists(extracted_folder):
            os.remove(extracted_folder)
        return False


def _create_folder_for_sorting(paper):
    if not paper["journal_reference"]:
        folder_name = "not_peer_reviewed"
    else:
        folder_name = "peer_reviewed"
        # folder_name = re.sub("[^0-9a-zA-Z]+", "_", paper["journal_reference"])

    folder_path = os.path.join(paper["paper_prefix_path"], folder_name)
    paper["paper_prefix_path"] = folder_path
    paper["paper_folder_label"] = folder_name
    if not os.path.exists(folder_path):
        os.mkdir(folder_path)


def _add_text_to_metadata(papers_metadata):
    print("######################### Consolidate Papers #################################")
    print()
    papers_consolidated_counter = 0
    papers_corrupted = 0
    papers_cant_be_consolidated = 0
    with alive_bar(len(papers_metadata)) as bar:
        for paper in papers_metadata:
            if _untar_paper_zip(paper):
                _create_folder_for_sorting(paper)
                consolidated_paper = consolidate_papers(paper)
                if consolidated_paper:
                    paper["paper_text"] = consolidated_paper
                    paper['for_deletion'] = False
                    papers_consolidated_counter += 1
                else:
                    paper['for_deletion'] = True
                    papers_cant_be_consolidated += 1
            else:
                paper['for_deletion'] = True
                papers_corrupted += 1
            bar()

    print("Papers consolidated {}".format(papers_consolidated_counter))
    print("Papers zip corrupted {}".format(papers_corrupted))
    print("Papers format can't be consolidated {}".format(papers_cant_be_consolidated))
    print()

    papers_metadata = list(filter(lambda x: not x['for_deletion'], papers_metadata))

    return papers_metadata