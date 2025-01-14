# -*- coding: utf-8 -*-
"""
Created on Thu Dec 13 14:13:02 2018
@author: piesauce, birkhoffg
"""
import torch
import torch.nn as nn
from torch.autograd import Variable
import torch.nn.functional as F


class MainClassifier(nn.Module):
    """
    Implements a BiLSTM based text classifier that utilizes both word and character embeddings.
    Characters in each word are passed through an LSTM to generate an encoding.
    The character encoding is concatenated with the word embeddings for each word in the input
    and is fed through a BiLSTM to generate an intermediate representation which is
    then fed to a fully connected layer that performs the classification.
    """
    
    def __init__(self, alphabet_size, vocab_size, output_size, args):
        """
        Args:
            alphabet_size (int): Number of unique characters in the input
            vocab_size (int): Size of the input vocabulary
            output_size (int): Number of class labels
            args: Command-line arguments
        """
        super(MainClassifier, self).__init__()
       
        self.char_hidden_dim = args.char_hidden_dim
        
        # self.char_embedding = nn.Embedding(alphabet_size, args.char_embed_dim)
        # self.char_bilstm = nn.LSTM(args.char_embed_dim, self.char_hidden_dim, bidirectional=True)
        
        self.word_hidden_dim = args.word_hidden_dim 
        
        self.num_layers = 2
        self.word_embedding = nn.Embedding(vocab_size, args.word_embed_dim)
        self.bilstm = nn.LSTM(args.word_embed_dim, self.word_hidden_dim, bidirectional=True, num_layers = self.num_layers)
        # self.bilstm = nn.LSTM(args.word_embed_dim + self.char_hidden_dim * 2, self.word_hidden_dim, bidirectional=True)
        self.fc1 = nn.Linear(self.word_hidden_dim * 2, args.fc_dim)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(args.fc_dim, output_size)
        self.softmax = nn.Softmax(dim=-1)

        self.hidden_size = self.word_hidden_dim * 2 
        self.seq_len = args.seq_len
        self.batch_size = args.batch_size
        self.device = args.device

        self.weight_init()
    
    def forward(self, sentence, adversary=False):
        """
        Args:
            sentence (list): Input sentence, consisting of a tuple (sentence_c, sentence_w)
                - (currently disabled) sentence_c contains the character indices of the input sentence.
                - sentence_w contains the word indices of the input sentence.
            adversary (bool): return intermediate encoding or softmax output 
        Returns:
            if adversary, returns intermediate encoding
            if not adversary, returns softmax output
        """
        last_hidden_state = self.get_lstm_embed(sentence)
        
        if adversary:
            return last_hidden_state

        fc_output = self.fc1(last_hidden_state)
        fc_output = self.relu(fc_output)
        fc_output = self.fc2(fc_output)
        fc_output = self.softmax(fc_output)
#         print('fc_output',fc_output.shape)
        return fc_output

    def get_lstm_embed(self, sentence):
        if len(sentence.shape) == 1:
            sentence = sentence.view(1, sentence.shape[0])
        word_embed = self.word_embedding(sentence).transpose(0,1)#.view(sentence_w.shape[1], sentence_w.shape[0], -1)
        
        h_w = torch.zeros(self.num_layers*2, sentence.shape[0], self.word_hidden_dim).to(self.device)
        c_w = torch.zeros(self.num_layers*2, sentence.shape[0], self.word_hidden_dim).to(self.device)
        
        output , (hidden_state, cell_state) = self.bilstm(word_embed, (h_w, c_w))
        output = output.transpose(0,1)#hidden_state[-2:].view(-1, self.word_hidden_dim * 2)
        last_hidden_state = output[:,-1,:]
        return last_hidden_state
    
    def get_loss(self, sentence, target):
        loss = nn.CrossEntropyLoss()
        if len(sentence.shape) == 1: 
            return loss(self(sentence), torch.tensor([target]))
        else:
            return loss(self(sentence), target.view(-1))


    def get_prediction(self, sentence):
        if len(sentence.shape) == 1:
            return torch.argmax(self(sentence))
        else: 
            return torch.argmax(self(sentence), dim=1)

    def get_loss_prediction(self, sentence, target):
        loss = nn.CrossEntropyLoss()
        output = self(sentence)
        if len(sentence.shape) == 1: 
            return loss(output, torch.tensor([target])), torch.argmax(output)
        else: 
            return loss(output, target.view(-1)), torch.argmax(output, dim=1)

    def freeze_parameters(self):
        for p in self.parameters():
            p.requires_grad = False

    def weight_init(self):
        for param in self.bilstm.parameters():
            if len(param.shape) >= 2:
                nn.init.orthogonal_(param.data)
            else:
                nn.init.normal_(param.data)

class AdversaryClassifier(nn.Module):
    """
    Implements a classifier used by the attacker to predict private variables from the hidden representations 
    of the main classifier.
    """
    def __init__(self, hidden_state_size, output_size, args):
        """
        Args:
            hidden_state_size (int): Dimensions of the intermediate representation
            output_size (int): Number of class labels
            args: Command-line arguments
        """
        super(AdversaryClassifier, self).__init__()
        self.fc1 = nn.Linear(hidden_state_size,  args.fc_dim)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(args.fc_dim, output_size)
        self.sigmoid = nn.Sigmoid()
        self.output_size = output_size
    
    def forward(self, hidden_state):
        """
        Args:
            hidden_state (int): Intermediate representation of neural network for the main task
        """
        fc_output = self.fc1(hidden_state)
        fc_output = self.relu(fc_output)
        fc_output = self.fc2(fc_output)
        fc_output = self.sigmoid(fc_output)
        return fc_output
    
    def get_loss(self, hidden_state, target):
        output = self(hidden_state)  
        loss_function = nn.BCEWithLogitsLoss()
        return loss_function(output, target.float())
        
    def get_prediction(self, hidden_state):
        output = self(hidden_state)
        prediction = output.cpu().clone()
        prediction[prediction>=0.5] = 1
        prediction[prediction<0.5] = 0
        return prediction

    def get_loss_prediction(self, hidden_state, target):
        output = self(hidden_state) 
#         print('output', output[0])
#         print('target', target[0])
        prediction = output.cpu().clone()
        prediction[prediction>=0.5] = 1
        prediction[prediction<0.5] = 0
        loss_function = nn.BCEWithLogitsLoss()
        return loss_function(output, target.float()), prediction
    
#=========dead kitten==========#
        # sentence_c, sentence_w = sentence
        # c_lstm_hidden = []
        
        # for token in sentence_c:
        #     token = torch.tensor(token)
        #     h_c = torch.zeros(2, 1, self.char_hidden_dim)
        #     c_c = torch.zeros(2, 1, self.char_hidden_dim)
        #     # print("token: ", token)
        #     char_embed = self.char_embedding(token).view(len(token), 1, -1)
        #     _ , (hidden_state, cell_state) = self.char_bilstm(char_embed, (h_c, c_c))
        #     hidden_state = hidden_state.view(-1, self.char_hidden_dim * 2)
        #     c_lstm_hidden.append(hidden_state)
        # c_lstm_hidden = torch.stack(c_lstm_hidden)
        
        # sentence_w = torch.tensor(sentence_w)
#         print('sentence',sentence.shape)
#         sentence_w = sentence
#         if len(sentence_w.shape) == 1:
#             sentence_w = sentence_w.view(1, sentence_w.shape[0])
#         print('sentence_w',sentence_w.shape)
#         word_embed = self.word_embedding(sentence_w).transpose(0,1)#.view(sentence_w.shape[1], sentence_w.shape[0], -1)
#         print('word_embed',word_embed.shape)
        # wc_embed = torch.cat((word_embed, c_lstm_hidden), 2)
