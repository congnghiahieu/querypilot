import numpy as np
import random
import os
import glob
import time

from src.nl2sql.dail_sql.utils.utils import sql2skeleton, jaccard_similarity
from src.nl2sql.dail_sql.utils.linking_utils.application import mask_question_with_schema_linking


def cleanup_old_target_embeddings(max_age_hours=24):
    """Clean up target embedding cache files older than max_age_hours"""
    from src.core.settings import PROJECT_ROOT
    cache_pattern = PROJECT_ROOT / "dataset" / "target_embedding_*.npy"
    current_time = time.time()
    
    for cache_file in glob.glob(str(cache_pattern)):
        file_age = current_time - os.path.getmtime(cache_file)
        if file_age > (max_age_hours * 3600):  # Convert hours to seconds
            try:
                os.remove(cache_file)
                print(f"Removed old target embedding cache: {os.path.basename(cache_file)}")
            except OSError:
                pass


class BasicExampleSelector(object):
    def __init__(self, data, *args, **kwargs):
        self.data = data
        self.train_json = self.data.get_train_json()
        self.db_ids = [d["db_id"] for d in self.train_json]
        self.train_questions = self.data.get_train_questions()


    def get_examples(self, question, num_example, cross_domain=False):
        pass

    def domain_mask(self, candidates: list, db_id):
        cross_domain_candidates = [candidates[i] for i in range(len(self.db_ids)) if self.db_ids[i] != db_id]
        return cross_domain_candidates

    def retrieve_index(self, indexes: list, db_id):
        cross_domain_indexes = [i for i in range(len(self.db_ids)) if self.db_ids[i] != db_id]
        retrieved_indexes = [cross_domain_indexes[i] for i in indexes]
        return retrieved_indexes


class RandomExampleSelector(BasicExampleSelector):
    def __init__(self, data, *args, **kwargs):
        super().__init__(data)
        random.seed(0)

    def get_examples(self, target, num_example, cross_domain=False):
        train_json = self.train_json
        indexes = list(range(len(train_json)))
        if cross_domain:
            indexes = domain_mask(indexes, target["db_id"])
        selected_indexes = random.sample(indexes, num_example)
        if cross_domain:
            selected_indexes = retrieve_index(selected_indexes, target["db_id"])
        return [train_json[index] for index in selected_indexes]


class CosineSimilarExampleSelector(BasicExampleSelector):
    def __init__(self, data, *args, **kwargs):
        super().__init__(data)

        self.SELECT_MODEL = "sentence-transformers/all-mpnet-base-v2"
        # self.SELECT_MODEL = "sentence-transformers/bert-base-nli-mean-tokens"

        from sentence_transformers import SentenceTransformer
        self.bert_model = SentenceTransformer(self.SELECT_MODEL, device="cpu")
        self.train_embeddings = self.bert_model.encode(self.train_questions)

        
    def get_examples(self, target, num_example, cross_domain=False):
        target_embedding = self.bert_model.encode([target["question"]])
        # target_embedding = self.bert_model.embed_text([target["question"]]).cpu().detach().numpy()

        # find the most similar question in train dataset
        from sklearn.metrics.pairwise import cosine_similarity
        similarities = np.squeeze(cosine_similarity(target_embedding, self.train_embeddings)).tolist()
        pairs = [(similarity, index) for similarity, index in zip(similarities, range(len(similarities)))]

        train_json = self.train_json
        pairs_sorted = sorted(pairs, key=lambda x: x[0], reverse=True)
        top_pairs = list()
        for s, index in pairs_sorted:
            similar_db_id = train_json[index]["db_id"]
            if cross_domain and similar_db_id == target["db_id"]:
                continue
            if train_json[index]["question"] == target["question"]:
                continue
            top_pairs.append((index, s))
            if len(top_pairs) >= num_example:
                break

        return [train_json[index] for (index, s) in top_pairs]


class EuclideanDistanceExampleSelector(BasicExampleSelector):
    def __init__(self, data, *args, **kwargs):
        super().__init__(data)

        self.SELECT_MODEL = "sentence-transformers/all-mpnet-base-v2"

        from sentence_transformers import SentenceTransformer
        self.bert_model = SentenceTransformer(self.SELECT_MODEL, device="cpu")
        self.train_embeddings = self.bert_model.encode(self.train_questions)

    def get_examples(self, target, num_example, cross_domain=False):
        target_embedding = self.bert_model.encode([target["question"]])

        # find the most similar question in train dataset
        from sklearn.metrics.pairwise import euclidean_distances
        distances = np.squeeze(euclidean_distances(target_embedding, self.train_embeddings)).tolist()
        pairs = [(distance, index) for distance, index in zip(distances, range(len(distances)))]

        train_json = self.train_json
        pairs_sorted = sorted(pairs, key=lambda x: x[0])
        top_pairs = list()
        for d, index in pairs_sorted:
            similar_db_id = train_json[index]["db_id"]
            if cross_domain and similar_db_id == target["db_id"]:
                continue
            top_pairs.append((index, d))
            if len(top_pairs) >= num_example:
                break

        return [train_json[index] for (index, d) in top_pairs]


class EuclideanDistanceThresholdExampleSelector(BasicExampleSelector):
    def __init__(self, data, *args, **kwargs):
        super().__init__(data)

        self.SELECT_MODEL = "sentence-transformers/all-mpnet-base-v2"
        # self.top_distances = list()
        self.threshold = 0.85

        from sentence_transformers import SentenceTransformer
        self.bert_model = SentenceTransformer(self.SELECT_MODEL, device="cpu")
        self.train_embeddings = self.bert_model.encode(self.train_questions)

    def get_examples(self, target, num_example, cross_domain=False):
        target_embedding = self.bert_model.encode([target["question"]])

        # find the most similar question in train dataset
        from sklearn.metrics.pairwise import euclidean_distances
        distances = np.squeeze(euclidean_distances(target_embedding, self.train_embeddings)).tolist()
        pairs = [(distance, index) for distance, index in zip(distances, range(len(distances)))]

        train_json = self.train_json
        pairs_sorted = sorted(pairs, key=lambda x: x[0])
        top_pairs = list()
        for d, index in pairs_sorted:
            similar_db_id = train_json[index]["db_id"]
            if (cross_domain and similar_db_id == target["db_id"]) or d > self.threshold:
                continue
            top_pairs.append((index, d))
            # self.top_distances.append(d)
            if len(top_pairs) >= num_example:
                break
        # print("mean", np.mean(self.top_distances))    # 0.822
        # print("std", np.std(self.top_distances, ddof=1))  # 0.144
        # print("max", max(self.top_distances)) # 1.166

        return [train_json[index] for (index, d) in top_pairs]


class EuclideanDistanceSkeletonSimilarThresholdSelector(BasicExampleSelector):
    def __init__(self, data, *args, **kwargs):
        super().__init__(data)

        self.SELECT_MODEL = "sentence-transformers/all-mpnet-base-v2"
        self.threshold = 0.85
        self.mask_token = "<mask>"  # the "<mask>" is the mask token of all-mpnet-base-v2
        self.value_token = "<unk>"  # the "<unk>" is the unknown token of all-mpnet-base-v2

        from sentence_transformers import SentenceTransformer
        train_mask_questions = mask_question_with_schema_linking(self.train_json, mask_tag=self.mask_token, value_tag=self.value_token)
        self.bert_model = SentenceTransformer(self.SELECT_MODEL, device="cpu")
        self.train_embeddings = self.bert_model.encode(train_mask_questions)

    def get_examples(self, target, num_example, cross_domain=False):
        target_mask_question = mask_question_with_schema_linking([target], mask_tag=self.mask_token, value_tag=self.value_token)
        target_embedding = self.bert_model.encode(target_mask_question)

        # find the most similar question in train dataset
        from sklearn.metrics.pairwise import euclidean_distances
        distances = np.squeeze(euclidean_distances(target_embedding, self.train_embeddings)).tolist()
        pairs = [(distance, index) for distance, index in zip(distances, range(len(distances)))]

        train_json = self.train_json
        pairs_sorted = sorted(pairs, key=lambda x: x[0])
        top_pairs = list()
        for d, index in pairs_sorted:
            similar_db_id = train_json[index]["db_id"]
            if cross_domain and similar_db_id == target["db_id"]:
                continue
            # Skeleton similarity
            if jaccard_similarity(train_json[index]["query_skeleton"], target["query_skeleton"]) < self.threshold:
                continue
            top_pairs.append((index, d))
            if len(top_pairs) >= num_example:
                break

        if len(top_pairs) < num_example:
            for d, index in pairs_sorted:
                similar_db_id = train_json[index]["db_id"]
                if cross_domain and similar_db_id == target["db_id"]:
                    continue
                # Skeleton similarity
                if jaccard_similarity(train_json[index]["query_skeleton"], target["query_skeleton"]) >= self.threshold:
                    continue
                top_pairs.append((index, d))
                if len(top_pairs) >= num_example:
                    break

        return [train_json[index] for (index, d) in top_pairs]


class EuclideanDistanceQuestionMaskSelector(BasicExampleSelector):
    def __init__(self, data, *args, **kwargs):
        super().__init__(data)

        print("EuclideanDistanceQuestionMaskSelector init")
        self.SELECT_MODEL = "sentence-transformers/all-mpnet-base-v2"
        self.mask_token = "<mask>"  # the "<mask>" is the mask token of all-mpnet-base-v2
        self.value_token = "<unk>" # the "<unk>" is the unknown token of all-mpnet-base-v2
        
        # Clean up old target embedding cache files
        cleanup_old_target_embeddings()

        from sentence_transformers import SentenceTransformer
        import numpy as np
        import os
        from src.core.settings import PROJECT_ROOT
        
        # Path to cached embeddings
        embeddings_cache_path = PROJECT_ROOT / "dataset" / "train_embeddings.npy"
        
        print("before mask_question_with_schema_linking")
        train_mask_questions = mask_question_with_schema_linking(self.train_json, mask_tag=self.mask_token, value_tag=self.value_token)
        print("after mask_question_with_schema_linking")
        
        # Check if cached embeddings exist
        if os.path.exists(embeddings_cache_path):
            print("Loading cached embeddings from train_embedding.npy")
            self.train_embeddings = np.load(embeddings_cache_path)
            print("Cached embeddings loaded successfully")
            # Still need to initialize model for target encoding
            self.bert_model = SentenceTransformer(self.SELECT_MODEL, device="cpu")
        else:
            print("Computing new embeddings (this may take a while)")
            self.bert_model = SentenceTransformer(self.SELECT_MODEL, device="cpu")
            print("before encode")
            print("train_mask_questions", train_mask_questions)
            self.train_embeddings = self.bert_model.encode(train_mask_questions)
            print("Saving embeddings to cache")
            np.save(embeddings_cache_path, self.train_embeddings)
            print("Embeddings cached successfully")
        
        print("EuclideanDistanceQuestionMaskSelector done")

    def get_examples(self, target, num_example, cross_domain=False):
        target_mask_question = mask_question_with_schema_linking([target], mask_tag=self.mask_token, value_tag=self.value_token)
        
        from src.core.settings import PROJECT_ROOT
        target_cache_path = PROJECT_ROOT / "dataset" / f"target_embedding.npy"
        
        if os.path.exists(target_cache_path):
            target_embedding = np.load(target_cache_path)
        else:
            print(f"Computing target embedding for question hash: {target_mask_question}")
            target_embedding = self.bert_model.encode(target_mask_question)
            np.save(target_cache_path, target_embedding)
            print(f"Target embedding cached: {target_cache_path.name}")

        # find the most similar question in train dataset
        from sklearn.metrics.pairwise import euclidean_distances
        distances = np.squeeze(euclidean_distances(target_embedding, self.train_embeddings)).tolist()
        pairs = [(distance, index) for distance, index in zip(distances, range(len(distances)))]

        train_json = self.train_json
        pairs_sorted = sorted(pairs, key=lambda x: x[0])
        top_pairs = list()
        for d, index in pairs_sorted:
            similar_db_id = train_json[index]["db_id"]
            if cross_domain and similar_db_id == target["db_id"]:
                continue
            top_pairs.append((index, d))
            if len(top_pairs) >= num_example:
                break

        return [train_json[index] for (index, d) in top_pairs]
    
    
class EuclideanDistancePreSkeletonSimilarThresholdSelector(BasicExampleSelector):
    def __init__(self, data, *args, **kwargs):
        super().__init__(data)

        self.SELECT_MODEL = "sentence-transformers/all-mpnet-base-v2"
        self.threshold = 0.85

        from sentence_transformers import SentenceTransformer
        self.bert_model = SentenceTransformer(self.SELECT_MODEL, device="cpu")
        self.train_embeddings = self.bert_model.encode(self.train_questions)

    def get_examples(self, target, num_example, cross_domain=False):
        target_embedding = self.bert_model.encode([target["question"]])

        # find the most similar question in train dataset
        from sklearn.metrics.pairwise import euclidean_distances
        distances = np.squeeze(euclidean_distances(target_embedding, self.train_embeddings)).tolist()
        pairs = [(distance, index) for distance, index in zip(distances, range(len(distances)))]

        train_json = self.train_json
        pairs_sorted = sorted(pairs, key=lambda x: x[0])
        top_pairs = list()
        for d, index in pairs_sorted:
            similar_db_id = train_json[index]["db_id"]
            if cross_domain and similar_db_id == target["db_id"]:
                continue
            # Skeleton similarity
            if jaccard_similarity(train_json[index]["pre_skeleton"], target["pre_skeleton"]) < self.threshold:
                continue
            top_pairs.append((index, d))
            if len(top_pairs) >= num_example:
                break

        if len(top_pairs) < num_example:
            for d, index in pairs_sorted:
                similar_db_id = train_json[index]["db_id"]
                if cross_domain and similar_db_id == target["db_id"]:
                    continue
                # Skeleton similarity
                if jaccard_similarity(train_json[index]["pre_skeleton"], target["pre_skeleton"]) >= self.threshold:
                    continue
                top_pairs.append((index, d))
                if len(top_pairs) >= num_example:
                    break

        return [train_json[index] for (index, d) in top_pairs]


class EuclideanDistancePreSkeletonSimilarPlusSelector(BasicExampleSelector):
    def __init__(self, data, *args, **kwargs):
        super().__init__(data)

        self.SELECT_MODEL = "sentence-transformers/all-mpnet-base-v2"

        from sentence_transformers import SentenceTransformer
        self.bert_model = SentenceTransformer(self.SELECT_MODEL, device="cpu")
        self.train_embeddings = self.bert_model.encode(self.train_questions)

    def get_examples(self, target, num_example, cross_domain=False):
        target_embedding = self.bert_model.encode([target["question"]])

        # find the most similar question in train dataset
        from sklearn.metrics.pairwise import euclidean_distances
        distances = np.squeeze(euclidean_distances(target_embedding, self.train_embeddings)).tolist()
        train_json = self.train_json
        for i in range(len(train_json)):
            distances[i] -= jaccard_similarity(train_json[i]["pre_skeleton"], target["pre_skeleton"])
        pairs = [(distance, index) for distance, index in zip(distances, range(len(distances)))]
        pairs_sorted = sorted(pairs, key=lambda x: x[0])
        top_pairs = list()
        for d, index in pairs_sorted:
            similar_db_id = train_json[index]["db_id"]
            if cross_domain and similar_db_id == target["db_id"]:
                continue
            top_pairs.append((index, d))
            if len(top_pairs) >= num_example:
                break

        return [train_json[index] for (index, d) in top_pairs]
    

class EuclideanDistanceQuestionMaskPreSkeletonSimilarThresholdSelector(BasicExampleSelector):
    def __init__(self, data, *args, **kwargs):
        super().__init__(data)

        self.SELECT_MODEL = "sentence-transformers/all-mpnet-base-v2"
        self.mask_token = "<mask>"  # the "<mask>" is the mask token of all-mpnet-base-v2
        self.value_token = "<unk>"  # the "<unk>" is the unknown token of all-mpnet-base-v2
        self.threshold = 0.85

        # Clean up old target embedding cache files
        cleanup_old_target_embeddings()

        from sentence_transformers import SentenceTransformer
        import numpy as np
        import os
        from src.core.settings import PROJECT_ROOT
        
        # Path to cached embeddings for mask questions
        embeddings_cache_path = PROJECT_ROOT / "dataset" / "train_embeddings.npy"
        
        train_mask_questions = mask_question_with_schema_linking(self.train_json, mask_tag=self.mask_token, value_tag=self.value_token)
        
        # Check if cached embeddings exist
        if os.path.exists(embeddings_cache_path):
            print("Loading cached mask embeddings from train_mask_embedding.npy")
            self.train_embeddings = np.load(embeddings_cache_path)
            print("Cached mask embeddings loaded successfully")
            # Still need to initialize model for target encoding
            self.bert_model = SentenceTransformer(self.SELECT_MODEL, device="cpu")
        else:
            print("Computing new mask embeddings (this may take a while)")
            self.bert_model = SentenceTransformer(self.SELECT_MODEL, device="cpu")
            self.train_embeddings = self.bert_model.encode(train_mask_questions)
            print("Saving mask embeddings to cache")
            np.save(embeddings_cache_path, self.train_embeddings)
            print("Mask embeddings cached successfully")

    def get_examples(self, target, num_example, cross_domain=False):
        target_mask_question = mask_question_with_schema_linking([target], mask_tag=self.mask_token, value_tag=self.value_token)
        
        from src.core.settings import PROJECT_ROOT
        target_cache_path = PROJECT_ROOT / "dataset" / f"target_embedding.npy"
        
        if os.path.exists(target_cache_path):
            target_embedding = np.load(target_cache_path)
        else:
            print(f"Computing target embedding for question hash: {target_mask_question}")
            target_embedding = self.bert_model.encode(target_mask_question)
            np.save(target_cache_path, target_embedding)
            print(f"Target embedding cached: {target_cache_path.name}")

        # find the most similar question in train dataset
        from sklearn.metrics.pairwise import euclidean_distances
        distances = np.squeeze(euclidean_distances(target_embedding, self.train_embeddings)).tolist()
        pairs = [(distance, index) for distance, index in zip(distances, range(len(distances)))]

        train_json = self.train_json
        pairs_sorted = sorted(pairs, key=lambda x: x[0])
        top_pairs = list()
        for d, index in pairs_sorted:
            similar_db_id = train_json[index]["db_id"]
            if cross_domain and similar_db_id == target["db_id"]:
                continue
            # Skeleton similarity
            if jaccard_similarity(train_json[index]["pre_skeleton"], target["pre_skeleton"]) < self.threshold:
                continue
            top_pairs.append((index, d))
            if len(top_pairs) >= num_example:
                break

        if len(top_pairs) < num_example:
            for d, index in pairs_sorted:
                similar_db_id = train_json[index]["db_id"]
                if cross_domain and similar_db_id == target["db_id"]:
                    continue
                # Skeleton similarity
                if jaccard_similarity(train_json[index]["pre_skeleton"], target["pre_skeleton"]) >= self.threshold:
                    continue
                top_pairs.append((index, d))
                if len(top_pairs) >= num_example:
                    break

        return [train_json[index] for (index, d) in top_pairs]


class EuclideanDistanceQuestionMaskPreSkeletonSimilarThresholdShiftSelector(BasicExampleSelector):
    def __init__(self, data, *args, **kwargs):
        super().__init__(data)

        self.SELECT_MODEL = "sentence-transformers/all-mpnet-base-v2"
        self.mask_token = "<mask>"  # the "<mask>" is the mask token of all-mpnet-base-v2
        self.value_token = "<unk>"  # the "<unk>" is the unknown token of all-mpnet-base-v2
        self.threshold = 0.85

        from sentence_transformers import SentenceTransformer
        train_mask_questions = mask_question_with_schema_linking(self.train_json, mask_tag=self.mask_token, value_tag=self.value_token)
        self.bert_model = SentenceTransformer(self.SELECT_MODEL, device="cpu")
        self.train_embeddings = self.bert_model.encode(train_mask_questions)

    def get_examples(self, target, num_example, cross_domain=False):
        target_mask_question = mask_question_with_schema_linking([target], mask_tag=self.mask_token, value_tag=self.value_token)
        
        # Cache target embeddings based on masked question
        import hashlib
        question_hash = hashlib.md5(str(target_mask_question[0]).encode()).hexdigest()[:8]
        target_cache_path = PROJECT_ROOT / "dataset" / f"target_embedding_{question_hash}.npy"
        
        if os.path.exists(target_cache_path):
            print(f"Loading cached target embedding for question hash: {question_hash}")
            target_embedding = np.load(target_cache_path)
        else:
            print(f"Computing target embedding for question hash: {question_hash}")
            target_embedding = self.bert_model.encode(target_mask_question)
            np.save(target_cache_path, target_embedding)
            print(f"Target embedding cached: {target_cache_path.name}")

        # find the most similar question in train dataset
        from sklearn.metrics.pairwise import euclidean_distances
        distances = np.squeeze(euclidean_distances(target_embedding, self.train_embeddings)).tolist()
        pairs = [(distance, index) for distance, index in zip(distances, range(len(distances)))]

        train_json = self.train_json
        pairs_sorted = sorted(pairs, key=lambda x: x[0])
        top_pairs = list()
        for d, index in pairs_sorted:
            similar_db_id = train_json[index]["db_id"]
            if cross_domain and similar_db_id == target["db_id"]:
                continue
            # Skeleton similarity
            if jaccard_similarity(train_json[index]["pre_skeleton"], target["pre_skeleton"]) < self.threshold:
                continue
            top_pairs.append((index, d))
            if len(top_pairs) >= num_example:
                break

        return [train_json[index] for (index, d) in top_pairs]
