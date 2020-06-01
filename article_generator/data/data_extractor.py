import shutil
import tarfile
import arxiv
import concurrent.futures
import os
from datetime import datetime
from time import mktime
from article_generator.data.db_details import DbName, ArxivDbQuery


class DataExtractor:
    def __init__(self, db_name=DbName.arxiv):
        if issubclass(db_name.__class__, DbName):
            self.db_name = db_name
        else:
            raise Exception("Wrong db name! db {} not supported".format(db_name))

        self.queries = set()
        self.queries_results = set()

    def add_queries(self, queries=[]):
        for query in queries:
            if not self._check_db_to_query_fit(query):
                raise Exception("Wrong db query! query {} not supported for db {}".format(query, self.db_name))

            self.queries.add(query)
        return self

    def query_db(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(self.queries)) as query_puller:
            future_to_query = {query_puller.submit(self._query, query): query for query in self.queries}

            for future_query_result in concurrent.futures.as_completed(future_to_query):
                query_details = future_to_query[future_query_result]
                try:
                    query_data = future_query_result.result()
                except Exception as exc:
                    print('query {} returned exception {}'.format(query_details, exc))
                else:
                    self.queries_results.update(query_data)

        return self

    def get_queries(self):
        return self.queries

    def get_queries_results(self):
        return self.queries_results

    def _check_db_to_query_fit(self, query):
        if issubclass(query.__class__, ArxivDbQuery) and self.db_name == DbName.arxiv:
            return True
        return False

    def download_papers(self, path="./papers", prefer_source_tarfile=True, unzip_tar=True):
        self._clean_workspace(path)

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(self.queries_results)) as paper_downloader:
            future_to_paper = {paper_downloader.submit(self._download_file, paper, path, lambda paper: paper.get('id').split('/')[-1], prefer_source_tarfile, unzip_tar): paper for paper in self.queries_results}

            for future_paper_result in concurrent.futures.as_completed(future_to_paper):
                paper_details = future_to_paper[future_paper_result]
                try:
                    paper_full_path = future_paper_result.result()
                except Exception as exc:
                    print('paper {} download returned exception {}'.format(paper_details, exc))
                else:
                    self.queries_results.remove(paper_details)
                    paper_details['paper_full_path'] = paper_full_path
                    self.queries_results.add(paper_details)
        return self

    def _clean_workspace(self, path):
        try:
            shutil.rmtree(path)
            os.mkdir(path)
        except OSError as e:
            print("Cant delete dir {}, {}".format(path, e.strerror))
            os.mkdir(path)

    def _download_file(self, paper, path, slugify, prefer_source_tarfile, unzip_tar):
        full_file_path = arxiv.download(paper, path, slugify, prefer_source_tarfile)
        if unzip_tar and prefer_source_tarfile:
            self._unzip_tar(full_file_path)

        return full_file_path

    def _unzip_tar(self, full_file_path):
        my_tar = tarfile.open(full_file_path)
        extracted_folder = "{}_{}".format(full_file_path, "extracted")
        os.mkdir(extracted_folder)
        my_tar.extractall(extracted_folder)
        my_tar.close()
        os.remove(full_file_path)
        os.rename(extracted_folder, full_file_path)

    def _query(self, query):
        if issubclass(query.__class__, ArxivDbQuery) and self.db_name == DbName.arxiv:
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

            query_result = list(filter(lambda result: query.from_date <= datetime.fromtimestamp(mktime(result['published_parsed'])) <= query.to_date, query_result))
            return query_result
