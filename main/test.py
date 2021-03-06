import cPickle
import copy
import random
import sys
import argparse
import lasagne
import numpy as np
import utils
from mixed_models import mixed_models
from models import models

random.seed(1)
np.random.seed(1)

def str2learner(v):
    if v is None:
        return None
    if v.lower() == "adagrad":
        return lasagne.updates.adagrad
    if v.lower() == "adam":
        return lasagne.updates.adam
    raise ValueError('A type that was supposed to be a learner is not.')

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-dim", help="Dimension of model", type=int, default=300)
    parser.add_argument("-wordfile", help="Word embedding file", default='../data/paragram_sl999_czeng.txt')
    parser.add_argument("-save", help="Whether to pickle model", type=int, default=0)
    parser.add_argument("-margin", help="Margin in objective function", type=float, default=0.4)
    parser.add_argument("-samplingtype", help="Type of Sampling used: MAX, MIX, or RAND", default="MAX")
    parser.add_argument("-evaluate", help="Whether to evaluate the model during training", type=int, default=1)
    parser.add_argument("-epochs", help="Number of epochs in training", type=int, default=10)
    parser.add_argument("-eta", help="Learning rate", type=float, default=0.001)
    parser.add_argument("-learner", help="Either AdaGrad or Adam", default="adam")
    parser.add_argument("-model", help="Which model to use between wordaverage, maxpool, (bi)lstmavg, (bi)lstmmax")
    parser.add_argument("-scramble", type=float, help="Rate of scrambling", default=0.3)
    parser.add_argument("-max", type=int, help="Maximum number of examples to use (<= 0 means use all data)", default=0)
    parser.add_argument("-loadmodel", help="Name of pickle file containing model", default=None)
    parser.add_argument("-data", help="Name of data file containing paraphrases", default=None)
    parser.add_argument("-wordtype", help="Either words or 3grams", default="words")
    parser.add_argument("-random_embs", help="Whether to use random embeddings "
                                             "and not pretrained embeddings", type = int, default=0)
    parser.add_argument("-mb_batchsize", help="Size of megabatch", type=int, default=40)
    parser.add_argument("-axis", help="Axis on which to concatenate hidden "
                                      "states (1 for sequence, 2 for embeddings)", type=int, default=1)
    parser.add_argument("-combination_method", help="Type of combining models (either add or concat)")
    parser.add_argument("-combination_type", help="choices are ngram-word, ngram-lstm, "
                                            "ngram-word-lstm, word-lstm")
    parser.add_argument("input_pair_file", help="Filename containing the input sentence pairs")
    parser.add_argument("output_score_File", help="Filename for the output score file")

    args = parser.parse_args()
    args.learner = str2learner(args.learner)

    params = args

    if params.combination_type:
        if params.loadmodel:
            saved_params = cPickle.load(open(params.loadmodel, 'rb'))
            if params.combination_type == "ngram-word":
                words = saved_params.pop(-1)
                words_3grams = words[0]
                words_words = words[1]
            elif params.combination_type == "ngram-word-lstm":
                words = saved_params.pop(-1)
                words_3grams = words[0]
                words_words = words[1]

            if params.combination_type == "ngram-word":
                model = mixed_models(saved_params[0], saved_params[1], params)
            elif params.combination_type == "ngram-word-lstm":
                model = mixed_models(saved_params[0], saved_params[1], params, We_initial_lstm = saved_params[2])

            lasagne.layers.set_all_param_values(model.final_layer, saved_params)

        print( "Num n-grams:", len(words_3grams))
        print("Num words:", len(words_words))

    else:
        if params.loadmodel:
            saved_params = cPickle.load(open(params.loadmodel, 'rb'))
            words = saved_params.pop(-1)
            model = models(saved_params[0], params)
            lasagne.layers.set_all_param_values(model.final_layer, saved_params)



    with open(params.input_pair_file, "r") as fdata:
        with open(params.output_score_File, "w") as fout:
            line = fdata.readline()
            while line:
                fld = line.strip("\n").split("\t")
                if len(fld) == 2:
                    p1 = unicode(fld[0], "utf-8")
                    p2 = unicode(fld[1], "utf-8")
                    score = model.predict_pairs(p1,p2, words_3grams, words_words, params)
                    print( score)
                    fout.write("%.4f\n" % score[0])
                line = fdata.readline()

    # p1 = "full stack engineer"
    # p2 = "software engineer"
    # score = model.predict_pairs(p1, p2, words_3grams, words_words, params)
    # print "score between (%s) and (%s) is %.3f " % ( p1, p2, score[0])

    # p1 = "A man with a hard hat is dancing"
    # p2 = "A man wearing a hard hat is dancing"
    # score = model.predict_pairs(p1, p2, words_3grams, words_words, params)
    # print "score between (%s) and (%s) is %.3f " % ( p1, p2, score[0])

    # p1 = "skillful in java and python"
    # p2 = "good java skill"
    # score = model.predict_pairs(p1, p2, words_3grams, words_words, params)
    # print "score between (%s) and (%s) is %.3f " % ( p1, p2, score[0])
    # p1 = "Experience leading engineering teams including establishing best practices creating core architecture for a site and mentoring junior engineers"
    # p2 = "Leading a team of engineers or mentoring junior engineers"
    # #  in loading of huge Open Access design databases by facilitating incremental loading of design partitions Provided enhancements to the Open Access framework to support advanced nodes and improved performance and capacity of Virtuoso Developed and shipped C/C++ libraries for third party EDA vendors to enable interoperability with Virtuoso"
    # print "score between (%s) and (%s) is %.3f " % ( p1, p2, score[0])
