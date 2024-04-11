import numpy as np 
from tqdm import tqdm


import torch 
from torch import nn
from transformers import (
    AutoModel, AutoTokenizer, AutoConfig, T5EncoderModel, 
    T5Config, MistralConfig, LongT5EncoderModel, LongT5Config)


from my_pooling import MyPooling
from bi_ce_utils import pairwise_dot_score 


class MyBIModel(nn.Module):
    """
    Bi-encoder
    """
    def __init__(self, model_name, bnb_config, train_type="sim", device="cuda"):
        """
        :param model_name:
        :param bnb_config:
        :param train_type:
        :param device:        
        """
        super(MyBIModel, self).__init__()
        self.device = device
        self.config = AutoConfig.from_pretrained(model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        print("LOAD Model", type(self.config))
                
        if isinstance(self.config ,  LongT5Config):
            LongT5EncoderModel._keys_to_ignore_on_load_unexpected = ["decoder.*"]
            self.auto_model = LongT5EncoderModel.from_pretrained(
                model_name, config=self.config).to(self.device)
            print("Initialize model LongT5EncoderModel")
            
            # set the max_length to a fixed number 
            self.max_length = 2048
            print("self.max_length", self.max_length)
        elif isinstance(self.config , T5Config):
            T5EncoderModel._keys_to_ignore_on_load_unexpected = ["decoder.*"]
            self.auto_model = T5EncoderModel.from_pretrained(
                model_name, config=self.config).to(self.device)
            print("Initialize model T5EncoderModel")
            # set the max_length to a fixed number 
            self.max_length = 1024
            print("self.max_length", self.max_length)
        elif isinstance(self.config , MistralConfig):
            if bnb_config is not None:        
                self.auto_model = AutoModel.from_pretrained(
                    model_name,     
                    device_map=device,
                    quantization_config=bnb_config,
                    config=self.config)
            else:
                self.auto_model = AutoModel.from_pretrained(
                    model_name,     
                    load_in_8bit=True,
                    device_map=device,
                    config=self.config)
            self.tokenizer.pad_token=self.tokenizer.eos_token
            self.tokenizer.padding_side="right"
        else:
            self.auto_model = AutoModel.from_pretrained(model_name).to(device)
        # auto_model.eval()

        self.pooling_model = MyPooling(
            self.auto_model.config.hidden_size).to(device)
        
        self.train_type = train_type
        if self.train_type in ['sim', 'margin']: 
            self.loss_fct = nn.MSELoss()

    def forward(self, tokenized_inputs, label):
        """
        :param tokenized_inputs:
        :param label:
        :return loss:
        """
        if self.train_type == "sim":
            tokenized_inputs[0]['token_embeddings']=self.auto_model(
                **tokenized_inputs[0], return_dict=False)[0]
            tokenized_inputs[1]['token_embeddings']=self.auto_model(
                **tokenized_inputs[1], return_dict=False)[0]
            embeddings_0 = self.pooling_model(tokenized_inputs[0])['sentence_embedding']
            embeddings_1 = self.pooling_model(tokenized_inputs[1])['sentence_embedding']
            output = torch.cosine_similarity(embeddings_0, embeddings_1)
            loss = self.loss_fct(output, label.view(-1))
        elif self.train_type == "margin":
            tokenized_inputs[0]['token_embeddings']=self.auto_model(
                **tokenized_inputs[0], return_dict=False)[0]
            tokenized_inputs[1]['token_embeddings']=self.auto_model(
                **tokenized_inputs[1], return_dict=False)[0]
            tokenized_inputs[2]['token_embeddings']=self.auto_model(
                **tokenized_inputs[2], return_dict=False)[0]
                
            embeddings_query = self.pooling_model(tokenized_inputs[0])['sentence_embedding']
            embeddings_pos = self.pooling_model(tokenized_inputs[1])['sentence_embedding']
            embeddings_neg = self.pooling_model(tokenized_inputs[2])['sentence_embedding']

            scores_pos = pairwise_dot_score(embeddings_query, embeddings_pos)
            scores_neg = pairwise_dot_score(embeddings_query, embeddings_neg)

            margin_pred = scores_pos - scores_neg
            loss = self.loss_fct(margin_pred, label)
        return loss
    
    def encode(self, sentences, batch_size=8, normalize_embeddings= True, show_bar=True):
        """
        :param sentences:
        :param batch_size:
        :param normalize_embeddings:
        :param show_bar:
        :return all_embeddings:
        """
        all_embeddings = []
        self.eval()
        for start_index in tqdm(range(0, len(sentences), batch_size), disable = not show_bar):
            with torch.no_grad():
                
                # ENCODING
                sentences_batch = sentences[start_index:start_index+batch_size]
                tokenized = self.tokenizer(
                    sentences_batch, padding=True, 
                    truncation=True, return_tensors='pt').to(self.device)
                token_embeddings = self.auto_model(**tokenized, return_dict=False)[0]

                # POOLING 
                attention_mask = tokenized['attention_mask']
                output_vectors = []
                input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size())
                sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1)
                sum_mask = input_mask_expanded.sum(1)
                sum_mask = torch.clamp(sum_mask, min=1e-9)
                output_vectors.append(sum_embeddings / sum_mask)
                output_vector = torch.cat(output_vectors, 1).detach().cpu()

                if normalize_embeddings:
                    embeddings = torch.nn.functional.normalize(output_vector, p=2, dim=1)
                all_embeddings.extend(embeddings)

        all_embeddings = np.asarray([emb.numpy() for emb in all_embeddings])
        return all_embeddings
    
    def smart_batching_collate(self, batch):
        """
        :param batch:
        :return sentence_features:
        :return labels:
        """
        num_texts = len(batch[0].texts)
        texts = [[] for _ in range(num_texts)]
        labels = []

        for example in batch:
            for idx, text in enumerate(example.texts):
                texts[idx].append(text)

            labels.append(example.label)

        labels = torch.tensor(labels)

        sentence_features = []
        for idx in range(num_texts):
            tokenized = self.tokenizer(
                texts[idx], return_tensors="pt",padding=True, 
                max_length=self.max_length, truncation=True).to(self.device)
            sentence_features.append(tokenized)

        return sentence_features, labels
