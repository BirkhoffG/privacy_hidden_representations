# privacy_hidden_representations

## Train the model
```
python -m src.main -device cpu -d tp_us
```


**Privacy preserving ML for NLP tasks**


This project explores at ways to prevent intermediate representations of neural networks from leaking private information contained in the input features while balancing the tradeoff with model accuracy. The models are implemented in PyTorch with some help from NLTK and Gensim.

**Key assumptions:**
1. Private information may be explicitly present in the input features or might be heavily correlated with them.

2. The attacker has access to the representation function and thus the intermediate representations generated by the model at test time.

Many of the ideas implemented in this project comes from the following EMNLP 2018 papers:

Coavoux et al., [Privacy-preserving Neural Representations of Text](http://aclweb.org/anthology/D18-1001)

Elazar et al., [Adversarial Removal of Demographic Attributes from Text Data](http://aclweb.org/anthology/D18-1002)

I have written an accompanying [blog post](https://medium.com/@piesauce/what-i-learned-from-emnlp2018-papers-part-2-4ae0f550ced8) explaining techniques for privacy-preservation.

For the latest advances in improving privacy and security in machine learning applications, have a look at the related workshops conducted at NeurIPS:

[Privacy Preserving Machine Learning Workshop @ NeurIPS 2018](https://ppml-workshop.github.io/ppml/)

[Workshop on Security in Machine Learning @ NeurIPS 2018](https://secml2018.github.io/)

**Datasets**

The experiments are performed on the same datasets as the ones used by [Coavoux et al](http://aclweb.org/anthology/D18-1001)
They are:
1. The Trustpilot reviews dataset, containing reviews associated with a sentiment score. The corpus is subdivided into 5 sections based on geographical origin. The main task is to predict the sentiment score associated with a review. The private (demographic) variables are the age and the gender of each reviewer.

2. The AG news corpus, containing news articles and the topics associated with them. The main task is to classify a news article based on the topic it belongs to. The private variables are the named entities mentioned in the news articles.

3. The Blog Authorship corpus, containing a collection of blog posts. We perform topic modeling on this dataset to generate the topic labels. The main task is to classify a blog post based on its topic. The private variables are the age and the gender of the authors.

To download the datasets, please run the python scripts in the **data** folder.

**Code**

The **data** folder contains python code to download all three datasets.

The **preprocessing** folder contains code to clean, normalize, and preprocess the datasets and generate training examples.

The **models** folder contains various neural network models used to accomplish the main task and the adversarial task of predicting the private variables.


**Reference Implementations**

1. https://github.com/mcoavoux/pnet
2. https://github.com/yanaiela/demog-text-removal






