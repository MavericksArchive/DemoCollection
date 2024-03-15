from transformers import AutoModelForSequenceClassification, AutoTokenizer, AutoConfig
from torch import nn
import numpy as np
from torch.utils.data import DataLoader
import torch

class MyCEModel(nn.Module):
    def __init__(self, model_name, num_labels=1, device='cuda:0'):
        super(MyCEModel, self).__init__()
        self.config = AutoConfig.from_pretrained(model_name)
        self.max_length = self.config.max_position_embeddings
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name, config=self.config)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.default_activation_function = nn.Sigmoid() if self.config.num_labels == 1 else nn.Identity()
        self.activation_fct = nn.Identity()
        self.num_label = num_labels
        self.config.num_labels = num_labels
        self.device = device

    def forward(self,features):
        model_predictions = self.model(**features, return_dict=True)
        logits = self.activation_fct(model_predictions.logits)  
        if self.config.num_labels == 1:
            logits = logits.view(-1) 
        return logits   
    
    def smart_batching_collate_text_only(self, batch):
        texts = [[] for _ in range(len(batch[0]))]

        for example in batch:
            for idx, text in enumerate(example):
                texts[idx].append(text.strip())
        tokenized = self.tokenizer(*texts, padding=True, truncation='longest_first', return_tensors="pt", max_length=self.max_length)

        for name in tokenized:
            tokenized[name] = tokenized[name].to(self.device)
        return tokenized
    
    def predict(self, sentences, batch_size=256):
        iterator  = DataLoader(sentences, batch_size=batch_size, collate_fn=self.smart_batching_collate_text_only, shuffle=False)

        pred_scores = []
        with torch.no_grad():
            for features in iterator:
                model_predictions = self.model(**features, return_dict=True)
                logits = self.activation_fct(model_predictions.logits)
                pred_scores.extend(logits)

        pred_scores = [score[0] for score in pred_scores]
        pred_scores = np.asarray([score.cpu().detach().numpy() for score in pred_scores])
        return pred_scores

    def smart_batching_collate(self, batch):
        texts = [[] for _ in range(len(batch[0].texts))]
        labels = []

        for example in batch:
            for idx, text in enumerate(example.texts):
                texts[idx].append(text.strip())

            labels.append(example.label)

        tokenized = self.tokenizer(
            *texts, padding=True, truncation="longest_first", return_tensors="pt", max_length=self.max_length
        ).to(self.device)
        labels = torch.tensor(labels, dtype=torch.float if self.config.num_labels == 1 else torch.long).to(
            self.device
        )

        for name in tokenized:
            tokenized[name] = tokenized[name].to(self.device)

        return tokenized, labels