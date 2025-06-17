import argparse
import json
import os
from pathlib import Path
import sqlite3
from tqdm import tqdm

from src.nl2sql.utils.linking_process import SpiderEncoderV2Preproc
from src.nl2sql.utils.pretrained_embeddings import TransformerEmbedder
from src.nl2sql.utils.datasets.spider import load_tables


def schema_linking_producer(data_item, table, db, dataset_dir, compute_cv_link=True):
    """
    Produces schema linking between natural language questions and database schemas.
    This function processes question to create mappings between:
    - Question tokens and database columns/tables
    - Question values and database cell values
    
    Args:
        data_item: question to be linked
        table: Path to database schema JSON file
        db: Directory containing SQLite database files
        dataset_dir: Root directory of the dataset
        compute_cv_link: Whether to compute value linking (can be disabled for large DBs)
    """
    # load schemas
    schemas, _ = load_tables([os.path.join(dataset_dir, table)])

    # Backup in-memory copies of all the DBs and create the live connections
    for db_id, schema in tqdm(schemas.items(), desc="DB connections"):
        sqlite_path = Path(dataset_dir) / db / db_id / f"{db_id}.sqlite"
        source: sqlite3.Connection
        with sqlite3.connect(str(sqlite_path)) as source:
            dest = sqlite3.connect(':memory:')
            dest.row_factory = sqlite3.Row
            source.backup(dest)
        schema.connection = dest

    # Initialize the schema linking processor with transformer-based word embeddings
    word_emb = TransformerEmbedder(model_name='all-MiniLM-L6-v2', lemmatize=True)
    linking_processor = SpiderEncoderV2Preproc(dataset_dir,
            include_table_name_in_column=False,
            word_emb=word_emb,
            fix_issue_16_primary_keys=True,
            compute_sc_link=True,
            compute_cv_link=compute_cv_link)

    # build schema-linking
    db_id = "financial"
    schema = schemas[db_id]
    preprocessed = linking_processor.preprocess_item(data_item, schema)

    # save
    #linking_processor.save()
    return preprocessed


def bird_pre_process(bird_dir, with_evidence=False):
    new_db_path = os.path.join(bird_dir, "database")
    if not os.path.exists(new_db_path):
        os.system(f"cp -r {os.path.join(bird_dir, 'train/train_databases/*')} {new_db_path}")
        os.system(f"cp -r {os.path.join(bird_dir, 'dev/dev_databases/*')} {new_db_path}")

    def json_preprocess(data_jsons):
        new_datas = []
        for data_json in data_jsons:
            ### Append the evidence to the question
            if with_evidence and len(data_json["evidence"]) > 0:
                data_json['question'] = (data_json['question'] + " " + data_json["evidence"]).strip()
            question = data_json['question']
            tokens = []
            for token in question.split(' '):
                if len(token) == 0:
                    continue
                if token[-1] in ['?', '.', ':', ';', ','] and len(token) > 1:
                    tokens.extend([token[:-1], token[-1:]])
                else:
                    tokens.append(token)
            data_json['question_toks'] = tokens
            data_json['query'] = data_json['SQL']
            new_datas.append(data_json)
        return new_datas

    output_dev = 'dev.json'
    output_train = 'train.json'
    with open(os.path.join(bird_dir, 'dev/dev.json')) as f:
        data_jsons = json.load(f)
        wf = open(os.path.join(bird_dir, output_dev), 'w')
        json.dump(json_preprocess(data_jsons), wf, indent=4)
    with open(os.path.join(bird_dir, 'train/train.json')) as f:
        data_jsons = json.load(f)
        wf = open(os.path.join(bird_dir, output_train), 'w')
        json.dump(json_preprocess(data_jsons), wf, indent=4)
    os.system(f"cp {os.path.join(bird_dir, 'dev/dev.sql')} {bird_dir}")
    os.system(f"cp {os.path.join(bird_dir, 'train/train_gold.sql')} {bird_dir}")
    tables = []
    with open(os.path.join(bird_dir, 'dev/dev_tables.json')) as f:
        tables.extend(json.load(f))
    with open(os.path.join(bird_dir, 'train/train_tables.json')) as f:
        tables.extend(json.load(f))
    with open(os.path.join(bird_dir, 'tables.json'), 'w') as f:
        json.dump(tables, f, indent=4)

def bull_pre_process(bull_dir, bull_dev, bull_train):
    def json_preprocess(data_jsons):
        new_datas = []
        for data_json in data_jsons:
            new_data = {}
            new_data["db_id"] = data_json["db_name"]
            new_data["question"] = data_json["question"]
            new_data["query"] = data_json["sql_query"]
            new_data["question_toks"] = ""
            new_datas.append(new_data)

        return new_datas

    with open(os.path.join(bull_dir, bull_dev), 'r') as f:
        dev_data = json.load(f)
        wf = open(os.path.join(bull_dir, "BULL-en/dev-preprocessed.json"), 'w')
        json.dump(json_preprocess(dev_data), wf, indent=4)
    with open(os.path.join(bull_dir, bull_train), 'r') as f:
        train_data = json.load(f)
        wf = open(os.path.join(bull_dir, "BULL-en/train-preprocessed.json"), 'w')
        json.dump(json_preprocess(train_data), wf, indent=4)
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_type", type=str, choices=["spider", "bird", "bull"], default="bull")
    args = parser.parse_args()

    data_type = args.data_type
    if data_type == "spider":
        # merge two training split of Spider
        spider_dir = "./dataset/spider"
        split1 = "train_spider.json"
        split2 = "train_others.json"
        total_train = []
        for item in json.load(open(os.path.join(spider_dir, split1))):
            total_train.append(item)
        for item in json.load(open(os.path.join(spider_dir, split2))):
            total_train.append(item)
        with open(os.path.join(spider_dir, 'train_spider_and_others.json'), 'w') as f:
            json.dump(total_train, f)

        # schema-linking between questions and databases for Spider
        spider_dev = "dev.json"
        spider_train = 'train_spider_and_others.json'
        spider_table = 'tables.json'
        spider_db = 'database'
        schema_linking_producer(spider_dev, spider_train, spider_table, spider_db, spider_dir)
    elif data_type == "bird":
        # schema-linking for bird with evidence
        bird_dir = './dataset/bird'
        bird_pre_process(bird_dir, with_evidence=True)
        bird_dev = 'dev.json'
        bird_train = 'train.json'
        bird_table = 'tables.json'
        bird_db = 'databases'
        ## do not compute the cv_link since it is time-consuming in the huge database in BIRD
        schema_linking_producer(bird_dev, bird_train, bird_table, bird_db, bird_dir, compute_cv_link=False)
    elif data_type == "bull":
        # schema-linking for bull
        bull_dir = './dataset/bull'
        bull_dev = 'BULL-en/dev.json'
        bull_train = 'BULL-en/train.json'
        bull_pre_process(bull_dir, bull_dev, bull_train)
        bull_dev_preprocessed = 'BULL-en/dev-preprocessed.json'
        bull_train_preprocessed = 'BULL-en/train-preprocessed.json'
        bull_table = 'BULL-en/tables.json'
        bull_db = 'database_en'
        schema_linking_producer(bull_dev_preprocessed, bull_train_preprocessed, bull_table, bull_db, bull_dir)
