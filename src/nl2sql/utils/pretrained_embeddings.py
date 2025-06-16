import abc
import functools
import os

import torch
from sentence_transformers import SentenceTransformer
import spacy

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Downloading spaCy model...")
    import subprocess
    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
    nlp = spacy.load("en_core_web_sm")

class Embedder(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def tokenize(self, sentence):
        '''Given a string, return a list of tokens suitable for lookup.'''
        pass

    @abc.abstractmethod
    def untokenize(self, tokens):
        '''Undo tokenize.'''
        pass

    @abc.abstractmethod
    def lookup(self, token):
        '''Given a token, return a vector embedding if token is in vocabulary.
        If token is not in the vocabulary, then return None.'''
        pass

    @abc.abstractmethod
    def contains(self, token):
        pass

    @abc.abstractmethod
    def to(self, device):
        '''Transfer the pretrained embeddings to the given device.'''
        pass

class TransformerEmbedder(Embedder):
    def __init__(self, model_name='all-MiniLM-L6-v2', lemmatize=False):
        """
        Initialize transformer-based embeddings using Sentence Transformers.
        
        Args:
            model_name: Name of the Sentence Transformer model to use
            lemmatize: Whether to lemmatize tokens before embedding
        """
        self.model = SentenceTransformer(model_name)
        self.dim = self.model.get_sentence_embedding_dimension()
        self.lemmatize = lemmatize
        self.nlp = nlp
        
        # Cache for token embeddings
        self._token_cache = {}

    @functools.lru_cache(maxsize=1024)
    def tokenize(self, text):
        doc = self.nlp(text)
        if self.lemmatize:
            return [token.lemma_.lower() for token in doc]
        else:
            return [token.text.lower() for token in doc]

    @functools.lru_cache(maxsize=1024)
    def tokenize_for_copying(self, text):
        """
        Tokenize text while preserving original text for copying.
        Returns both lemmatized/normalized tokens and original text tokens.
        
        Args:
            text: Input text to tokenize
            
        Returns:
            tuple: (normalized_tokens, original_tokens)
        """
        doc = self.nlp(text)
        text_for_copying = [token.text.lower() for token in doc]
        if self.lemmatize:
            text = [token.lemma_.lower() for token in doc]
        else:
            text = [token.text.lower() for token in doc]
        return text, text_for_copying

    def untokenize(self, tokens):
        return ' '.join(tokens)

    def lookup(self, token):
        if token in self._token_cache:
            return self._token_cache[token]
        
        # Get embedding for the token
        with torch.no_grad():
            embedding = self.model.encode(token, convert_to_tensor=True)
            self._token_cache[token] = embedding
            return embedding

    def contains(self, token):
        return True  # Transformers can handle any token

    def to(self, device):
        self.model = self.model.to(device)
        # Move cached embeddings to device
        for token in self._token_cache:
            self._token_cache[token] = self._token_cache[token].to(device)