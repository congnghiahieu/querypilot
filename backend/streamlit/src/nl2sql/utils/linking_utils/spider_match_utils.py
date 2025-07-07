import collections
import re
import string

import nltk.corpus

STOPWORDS = set(nltk.corpus.stopwords.words("english"))
PUNKS = set(a for a in string.punctuation)

CELL_EXACT_MATCH_FLAG = "EXACTMATCH"
CELL_PARTIAL_MATCH_FLAG = "PARTIALMATCH"
COL_PARTIAL_MATCH_FLAG = "CPM"
COL_EXACT_MATCH_FLAG = "CEM"
TAB_PARTIAL_MATCH_FLAG = "TPM"
TAB_EXACT_MATCH_FLAG = "TEM"


# schema linking, similar to IRNet
def compute_schema_linking(question, column, table):
    """
    Performs schema linking between natural language question tokens and database schema elements.
    This function identifies which parts of the question correspond to database columns and tables.

    Args:
        question (list): List of tokens from the natural language question
        column (list): List of column names from the database schema
        table (list): List of table names from the database schema

    Returns:
        dict: Dictionary containing two keys:
            - q_col_match: Maps question token positions to column matches
            - q_tab_match: Maps question token positions to table matches
    """

    def partial_match(x_list, y_list):
        """
        Checks if a sequence of words appears as a whole word within another sequence.
        Ignores matches that are stopwords or punctuation.

        Args:
            x_list (list): First sequence of words to compare
            y_list (list): Second sequence of words to compare

        Returns:
            bool: True if x_list appears as a whole word in y_list, False otherwise
        """
        x_str = " ".join(x_list)
        y_str = " ".join(y_list)
        if x_str in STOPWORDS or x_str in PUNKS:
            return False
        if re.match(rf"\b{re.escape(x_str)}\b", y_str):
            assert x_str in y_str
            return True
        else:
            return False

    def exact_match(x_list, y_list):
        """
        Checks if two sequences of words are identical.

        Args:
            x_list (list): First sequence of words to compare
            y_list (list): Second sequence of words to compare

        Returns:
            bool: True if sequences are identical, False otherwise
        """
        x_str = " ".join(x_list)
        y_str = " ".join(y_list)
        if x_str == y_str:
            return True
        else:
            return False

    # Initialize dictionaries to store matches
    q_col_match = dict()  # Maps question positions to column matches
    q_tab_match = dict()  # Maps question positions to table matches

    # Create mapping from column IDs to column names
    col_id2list = dict()
    for col_id, col_item in enumerate(column):
        if col_id == 0:  # Skip the first column (usually *)
            continue
        col_id2list[col_id] = col_item

    # Create mapping from table IDs to table names
    tab_id2list = dict()
    for tab_id, tab_item in enumerate(table):
        tab_id2list[tab_id] = tab_item

    # Use n-gram approach to find matches, starting with 5-grams and decreasing to 1-grams
    n = 5
    while n > 0:
        # Slide window of size n over the question
        for i in range(len(question) - n + 1):
            n_gram_list = question[i : i + n]
            n_gram = " ".join(n_gram_list)
            if len(n_gram.strip()) == 0:
                continue

            # Check for exact matches with columns
            for col_id in col_id2list:
                if exact_match(n_gram_list, col_id2list[col_id]):
                    for q_id in range(i, i + n):
                        q_col_match[f"{q_id},{col_id}"] = COL_EXACT_MATCH_FLAG

            # Check for exact matches with tables
            for tab_id in tab_id2list:
                if exact_match(n_gram_list, tab_id2list[tab_id]):
                    for q_id in range(i, i + n):
                        q_tab_match[f"{q_id},{tab_id}"] = TAB_EXACT_MATCH_FLAG

            # Check for partial matches with columns
            for col_id in col_id2list:
                if partial_match(n_gram_list, col_id2list[col_id]):
                    for q_id in range(i, i + n):
                        if f"{q_id},{col_id}" not in q_col_match:
                            q_col_match[f"{q_id},{col_id}"] = COL_PARTIAL_MATCH_FLAG

            # Check for partial matches with tables
            for tab_id in tab_id2list:
                if partial_match(n_gram_list, tab_id2list[tab_id]):
                    for q_id in range(i, i + n):
                        if f"{q_id},{tab_id}" not in q_tab_match:
                            q_tab_match[f"{q_id},{tab_id}"] = TAB_PARTIAL_MATCH_FLAG
        n -= 1

    return {"q_col_match": q_col_match, "q_tab_match": q_tab_match}


def compute_cell_value_linking(tokens, schema):
    """
    Performs cell value linking between natural language question tokens and database cell values.
    This function identifies which parts of the question correspond to actual values in the database tables.

    Args:
        tokens (list): List of tokens from the natural language question
        schema: Database schema object containing column and table information

    Returns:
        dict: Dictionary containing two keys:
            - num_date_match: Maps question token positions to number/date matches
            - cell_match: Maps question token positions to cell value matches
    """

    def isnumber(word):
        try:
            float(word)
            return True
        except:
            return False

    def db_word_partial_match(word, column, table, db_conn):
        """
        Checks if a word partially matches any values in a database column.
        Matches if the word appears at the start, end, or middle of any cell value.

        Args:
            word (str): Word to match
            column (str): Column name to search in
            table (str): Table name to search in
            db_conn: Database connection object

        Returns:
            list/bool: List of matching results if found, False otherwise
        """
        cursor = db_conn.cursor()

        p_str = (
            f"select {column} from {table} where {column} like '{word} %' or {column} like '% {word}' or "
            f"{column} like '% {word} %' or {column} like '{word}'"
        )
        try:
            cursor.execute(p_str)
            p_res = cursor.fetchall()
            if len(p_res) == 0:
                return False
            else:
                return p_res
        except Exception:
            return False

    def db_word_exact_match(word, column, table, db_conn):
        """
        Checks if a word exactly matches any values in a database column.
        Matches if the word is identical to a cell value (with optional surrounding spaces).

        Args:
            word (str): Word to match
            column (str): Column name to search in
            table (str): Table name to search in
            db_conn: Database connection object

        Returns:
            list/bool: List of matching results if found, False otherwise
        """
        cursor = db_conn.cursor()

        p_str = (
            f"select {column} from {table} where {column} like '{word}' or {column} like ' {word}' or "
            f"{column} like '{word} ' or {column} like ' {word} '"
        )
        try:
            cursor.execute(p_str)
            p_res = cursor.fetchall()
            if len(p_res) == 0:
                return False
            else:
                return p_res
        except Exception:
            return False

    # Initialize dictionaries to store matches
    num_date_match = {}  # Maps question positions to number/date matches
    cell_match = {}  # Maps question positions to cell value matches

    # Process each column in the schema
    for col_id, column in enumerate(schema.columns):
        if col_id == 0:
            assert column.orig_name == "*"
            continue
        match_q_ids = []

        # Check each token in the question
        for q_id, word in enumerate(tokens):
            if len(word.strip()) == 0:
                continue
            if word in STOPWORDS or word in PUNKS:
                continue

            # Handle numeric values
            num_flag = isnumber(word)
            if num_flag:  # TODO refine the date and time match
                if column.type in ["number", "time"]:
                    num_date_match[f"{q_id},{col_id}"] = column.type.upper()
            else:
                # Check for partial matches in the database
                ret = db_word_partial_match(
                    word, column.orig_name, column.table.orig_name, schema.connection
                )
                if ret:
                    match_q_ids.append(q_id)

        # Process consecutive matching tokens to find exact matches
        f = 0
        while f < len(match_q_ids):
            t = f + 1
            while t < len(match_q_ids) and match_q_ids[t] == match_q_ids[t - 1] + 1:
                t += 1
            q_f, q_t = match_q_ids[f], match_q_ids[t - 1] + 1
            words = [token for token in tokens[q_f:q_t]]

            # Try to find exact match for the sequence of words
            ret = db_word_exact_match(
                " ".join(words), column.orig_name, column.table.orig_name, schema.connection
            )
            if ret:
                for q_id in range(q_f, q_t):
                    cell_match[f"{q_id},{col_id}"] = CELL_EXACT_MATCH_FLAG
            else:
                for q_id in range(q_f, q_t):
                    cell_match[f"{q_id},{col_id}"] = CELL_PARTIAL_MATCH_FLAG
            f = t

    cv_link = {"num_date_match": num_date_match, "cell_match": cell_match}
    return cv_link


def match_shift(q_col_match, q_tab_match, cell_match):
    q_id_to_match = collections.defaultdict(list)
    for match_key in q_col_match.keys():
        q_id = int(match_key.split(",")[0])
        c_id = int(match_key.split(",")[1])
        type = q_col_match[match_key]
        q_id_to_match[q_id].append((type, c_id))
    for match_key in q_tab_match.keys():
        q_id = int(match_key.split(",")[0])
        t_id = int(match_key.split(",")[1])
        type = q_tab_match[match_key]
        q_id_to_match[q_id].append((type, t_id))
    relevant_q_ids = list(q_id_to_match.keys())

    priority = []
    for q_id in q_id_to_match.keys():
        q_id_to_match[q_id] = list(set(q_id_to_match[q_id]))
        priority.append((len(q_id_to_match[q_id]), q_id))
    priority.sort()
    matches = []
    new_q_col_match, new_q_tab_match = dict(), dict()
    for _, q_id in priority:
        if not list(set(matches) & set(q_id_to_match[q_id])):
            exact_matches = []
            for match in q_id_to_match[q_id]:
                if match[0] in [COL_EXACT_MATCH_FLAG, TAB_EXACT_MATCH_FLAG]:
                    exact_matches.append(match)
            if exact_matches:
                res = exact_matches
            else:
                res = q_id_to_match[q_id]
            matches.extend(res)
        else:
            res = list(set(matches) & set(q_id_to_match[q_id]))
        for match in res:
            type, c_t_id = match
            if type in [COL_PARTIAL_MATCH_FLAG, COL_EXACT_MATCH_FLAG]:
                new_q_col_match[f"{q_id},{c_t_id}"] = type
            if type in [TAB_PARTIAL_MATCH_FLAG, TAB_EXACT_MATCH_FLAG]:
                new_q_tab_match[f"{q_id},{c_t_id}"] = type

    new_cell_match = dict()
    for match_key in cell_match.keys():
        q_id = int(match_key.split(",")[0])
        if q_id in relevant_q_ids:
            continue
        # if cell_match[match_key] == CELL_EXACT_MATCH_FLAG:
        new_cell_match[match_key] = cell_match[match_key]

    return new_q_col_match, new_q_tab_match, new_cell_match
