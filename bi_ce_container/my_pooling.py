import torch
from torch import Tensor
from torch import nn
from typing import Dict


class MyPooling(nn.Module):
    def __init__(self, word_embedding_dimension):
        """
        :param word_embedding_dimension:
        """
        super(MyPooling, self).__init__()
        self.word_embedding_dimension = word_embedding_dimension

    def forward(self, features: Dict[str, Tensor]):
        """
        :param features:
        :return features:
        """
        token_embeddings = features['token_embeddings']
        attention_mask = features['attention_mask']

        output_vectors = []
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).bfloat16()
        sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1)
        sum_mask = input_mask_expanded.sum(1)
        sum_mask = torch.clamp(sum_mask, min=1e-9)
        output_vectors.append(sum_embeddings / sum_mask)
        output_vector = torch.cat(output_vectors, 1)
        features.update({'sentence_embedding': output_vector})
        return features
