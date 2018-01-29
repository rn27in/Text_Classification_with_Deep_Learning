######This uses the CBOW version of Word2Vec#########################
###########We use the gensim package to load Word vectors###############
###############Initially, we will use pre-trained vectors#####################
import numpy as np
import keras
from keras.datasets import reuters
from keras.models import Sequential
from keras.layers import Dense, Dropout, Activation
from keras.preprocessing.text import Tokenizer
import pandas as pd
from keras.callbacks import  EarlyStopping
from nltk.corpus import stopwords
import re,os,time
from keras.layers import Embedding,Flatten
from keras.preprocessing.sequence import pad_sequences
from keras.utils import to_categorical
stop = (stopwords.words('english'))
from keras.layers import LSTM
import gensim
import nltk

stop.append('.')
stop = set(stop)

def cleaning_records(df, stop):
    df['description'] = df['description'].astype(str)
    df['description'] = [df['description'][record].lower() for record in range(df.shape[0])]##Lower case###
    df['description'] = [re.sub(r'\n', '',record) for record in df['description']]## Removing \n##
    df_desc = [doc for doc in df.description]
    final = []
    for doc in df_desc:
        temp = doc.split()
        temp = [word for word in temp if word not in stop]
        final.append(' '.join(temp))
    df['description_lower'] = final

    return df

######Loading the data######################################3
path ="../train.csv"

train = pd.read_csv(path)
train['description'] = train['description'].astype(str)

train = cleaning_records(df = train, stop = stop )

categories = train['category'].unique()
    ##Creating dictionaries for category####
dict_categories = {}
for i in range(len(categories)):
    dict_categories[categories[i]] = i
dict_inverse_categories = {i: j for j, i in dict_categories.iteritems()}
train['Labels'] = [dict_categories[category] for category in train['category']]

########################################################################################
##########Creating an instance of Tokenizer###################
tokenizer = Tokenizer()
tokenizer.fit_on_texts(train['description_lower'])
sequences = tokenizer.texts_to_sequences(train['description_lower'])

tokenizer_norm = tokenizer.word_index
tokenizer_inverse_norm = {elem:index for index,elem in tokenizer_norm.iteritems() }
sequences = tokenizer.texts_to_sequences(train['description_lower'])

####Loading the word2vec model####################
model = gensim.models.KeyedVectors.load_word2vec_format('../GoogleNews-vectors-negative300.bin', binary=True)

########Creating the Embedding matrix using the word2vec information#############
EMBEDDING_DIM = 300
embedding_matrix = np.zeros((len(tokenizer.word_index) + 1, EMBEDDING_DIM))
for word, elem in tokenizer.word_index.items():
    try:
        embedding_vector = model[word]
    except KeyError:
        continue
    if embedding_vector is not None:
        # words not found in embedding index will be all-zeros.
        embedding_matrix[elem] = embedding_vector

################This will create an average vector for each record#####################
def return_feature_vector(sequence_to_be_cal,embedding_matrix, seq):
    feature_vector = np.zeros((embedding_matrix.shape[1],))
    for elem in range(len(sequence_to_be_cal)):
        feature_vector = np.add(feature_vector, embedding_matrix[sequence_to_be_cal[elem]])

    if len(sequence_to_be_cal) == 0:
        print seq

    feature_vector = np.divide(feature_vector,len(sequence_to_be_cal))

    return feature_vector

def word2vec_embedding_vectors(sequences, embedding_matrix):
    feature_vector_final = np.zeros((len(sequences),embedding_matrix.shape[1]))
    for seq in  range(len(sequences)):
        feature_vector = return_feature_vector(sequences[seq],embedding_matrix, seq)
        feature_vector_final[seq] = feature_vector

    return feature_vector_final

feature_vector_final = word2vec_embedding_vectors(sequences, embedding_matrix)
#########################################################################################
##########Building the model #####################################
from sklearn.linear_model import LogisticRegression
clf = LogisticRegression(penalty= 'l2', multi_class= 'ovr')
start = time.time()
clf.fit(feature_vector_final[:300000], np.array(train.Labels)[:300000])
end = time.time()
pred = clf.predict(feature_vector_final[:300000])
pred_test = clf.predict(feature_vector_final[300000:])

###########Accuracy###################
np.sum(pred == np.array(train.Labels)[:300000])/(1.0 * len(pred)) ###68.43% for 300 vectors
np.sum(pred_test == np.array(train.Labels)[300000:])/(1.0 * len(pred_test)) ###68% for 300 vectors #

##########End########################################################
