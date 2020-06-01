import enum
from datetime import datetime, date


class DbName(enum.Enum):
    arxiv = 1

# query optional para
# prefix	explanation
# ti	Title
# au	Author
# abs	Abstract
# co	Comment
# jr	Journal Reference
# cat	Subject Category
# rn	Report Number
# id	Id (use id_list instead)
# all	All of the above



class ArxivDbQuery:
    def __init__(self, query, from_date, to_date=None, date_format="%Y-%m-%d", id_list=[], max_results=None, start=0, sort_by="submittedDate",
                 sort_order="descending", prune=True, max_chunk_results=1000):
        self.query = query
        self.from_date = datetime.strptime(from_date, date_format)
        if to_date is None:
            self.to_date = datetime.now()
        else:
            self.to_date = datetime.strptime(to_date, date_format)
        self.id_list = id_list
        self.max_results = max_results
        self.start = start
        self.sort_by = sort_by
        self.sort_order = sort_order
        self.prune = prune
        self.max_chunk_results = max_chunk_results


def get_components_list(db_name, component):
    if db_name == DbName.arxiv and component == "cs":
        return [#"cs.AI",
                "cs.AR"]
                # "cs.CC",
                # "cs.CE",
                # "cs.CG",
                # "cs.CL",
                # "cs.CR",
                # "cs.CV",
                # "cs.CY",
                # "cs.DB",
                # "cs.DC",
                # "cs.DL",
                # "cs.DM",
                # "cs.DS",
                # "cs.ET",
                # "cs.FL",
                # "cs.GL",
                # "cs.GR",
                # "cs.GT",
                # "cs.HC",
                # "cs.IR",
                # "cs.IT",
                # "cs.LG",
                # "cs.LO",
                # "cs.MAv",
                # "cs.MM",
                # "cs.MS",
                # "cs.NA",
                # "cs.NE",
                # "cs.NI",
                # "cs.OH",
                # "cs.OS",
                # "cs.PF",
                # "cs.PL",
                # "cs.RO",
                # "cs.SC",
                # "cs.SD",
                # "cs.SE",
                # "cs.SI",
                # "cs.SY"]