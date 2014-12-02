##
# wrapping: A program making it easy to use hyperparameter
# optimization software.
# Copyright (C) 2013 Katharina Eggensperger and Matthias Feurer
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

__authors__ = ["Katharina Eggensperger", "Matthias Feurer"]
__contact__ = "automl.org"

import ast
import os
import subprocess
import sys
import time

import HPOlib.benchmark_util as benchmark_util
import HPOlib.wrapping_util as wrapping_util

def reduce_params(params):
    # Problem: Spearmint evaluates all parameters and passes all parameters
    # to the autoweka wrapper which itself passes all parameters to auto-
    # weka. This leads to illegal AutoWEKA calls. Now, the spearmint
    # search space is a translation of the tpe search space since the tpe
    # search space and the smac search space use different parameter names
    # for the same parameter. Then the tpe search space is loaded and all
    # evaluated parameters from spearmint are put into the tpe search space
    # replacing the random values by Literals. A call to tpes evaluate
    # method rec_eval evaluates this search space and kicks out all
    # conditional hyperparameters, which are inactive

    # Bad hack to import the hyperopt search space...
    # TODO: Remove this bad hack :-)
    import HPOlib.cv as cv
    import hyperopt
    sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), "hyperopt_august2013_mod"))
    import space

    hps = {}
    hpspace = hyperopt.pyll.base.as_apply(space.space)
    hpspace = hyperopt.pyll.stochastic.recursive_set_rng_kwarg(hpspace)
    hyperopt.pyll_utils.expr_to_config(hpspace, (), hps)
    # print hps

    memo = {}
    for param in params:
        # print param
        node = hps[param]['node']
        # We have to convert the parameter back to a string so literal eval can
        # actually work with it
        try:
            value = ast.literal_eval(str(params[param]))
        except ValueError as e:
            print "Malformed String:", params[param]
            raise e
        memo[node] = hyperopt.pyll.Literal(value)

    hpspace = hyperopt.pyll.base.rec_eval(hpspace, memo=memo)
    new_params = cv.flatten_parameter_dict(hpspace)
    del params
    return new_params


def wrapAutoweka(params, **kwargs):
    """ This functions wraps the autoweka software to use it in the BBoM workflow
    """

    # Look for spearmint calling wrappingAutoweka
    if len(params.keys()) > 700:
        params = reduce_params(params)
    print "Params:", params

    # The values Xmx (java memory) and the number 9000 (150 minutes) are from
    # the AutoWEKA paper. The 15 minutes for feature search are specified in the
    # parameter file
    # algo = "/usr/lib/jvm/java-7-openjdk-amd64/jre/bin/java" -Xmx1000m -cp
    # pathToAW autoweka.smac.SMACWrapper -prop datasetString=testArff=
    # testarff__COLONESCAPE__:type=trainTestArff__COLONESCAPE__:
    # trainArff=trainarff:
    # instanceGenerator=autoweka.instancegenerators.CrossValidation:
    # resultMetric=errorRate
    # -prop executionMode=SMAC:initialIncumbent=RANDOM:initialN=1 -wrapper

    # We do not necessarily need testarff, javamemory, trainingtime, pathToAW
    if "testarff" not in kwargs:
        kwargs["testarff"] = "__DUMMY__"
    else:
        kwargs["testarff"] = os.path.abspath(kwargs["testarff"])
        if not os.path.exists(kwargs["testarff"]):
            raise ValueError("%s does not exist, please correct --testarff" % 
                             kwargs["testarff"])
    if "javamemory" not in kwargs:
        kwargs["javamemory"] = "3000"
    if "trainingtime" not in kwargs:
        kwargs["trainingtime"] = "9000"
    if "pathToAw" not in kwargs:
        path_to_aw = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                "/autoweka-0.5/autoweka.jar")
    else:
        path_to_aw = os.path.abspath(kwargs["pathToAw"])
    if not os.path.exists(path_to_aw):
        raise ValueError("%s does not exist, please corect --pathToAw")

    # But we do need trainarff, folds, fold
    if "trainarff" not in kwargs:
        raise ValueError("Please set --trainarff")
    else:
        kwargs["trainarff"] = os.path.abspath(kwargs["trainarff"])
        if not os.path.exists(kwargs["trainarff"]):
            raise ValueError("%s does not exist, please correct --trainarff" %
                             kwargs["trainarff"])
    if not "folds" in kwargs:
        raise ValueError("--folds not specified")
    if not "fold" in kwargs:
        raise ValueError("--fold not specified")

    # Build the command
    cmd = "".join(['java -Xmx%sm -cp "%s" ' % (kwargs["javamemory"], path_to_aw),
                   "autoweka.smac.SMACWrapper -prop ",
                   "datasetString=testArff=%s__COLONESCAPE__:" % kwargs['testarff'],
                   "type=trainTestArff__COLONESCAPE__:",
                   "trainArff=%s:" % kwargs['trainarff'],
                   "instanceGenerator=autoweka.instancegenerators.CrossValidation:"
                   "resultMetric=errorRate ",
                   "-prop executionMode=SMAC:",
                   "initialIncumbent=RANDOM:",
                   "initialN=1 ",
                   "-wrapper seed=0:",
                   "numFolds=%s:fold=%s " % (kwargs['folds'], kwargs['fold']),
                   "0 %s 2147483647 -1 " % kwargs["trainingtime"]])
    cmd += ("%s" % (" ".join("-%s %s" % (i, params[i]) for i in params.keys())))

    time_string = wrapping_util.get_time_string()
    output_file = os.path.join(os.getcwd(), time_string + "_autoweka.out")
    print "\nRunning this command:\n%s" % cmd
    print "Saving to %s" % output_file
    fh = open(output_file, "a")
    process = subprocess.Popen(cmd, stdout=fh, stderr=fh, shell=True,
                               executable="/bin/bash")
    ret = process.wait()                                 
    fh.close()
    
    # Read the run_instance output file
    fh = open(output_file, "r")
    content = fh.readlines()
    fh.close()
    result = 100
    sat = ''
    for line in content:
        pos = line.find("Result for ParamILS:")
        if pos != -1:
            line = line.split(",")
            result = float(line[3].strip())
            sat = line[0].split(":")[1].strip()
            break
    if sat == "SAT":
        os.remove(output_file)
        print result
        return result
    else:
        raise Exception(("Autoweka crashed, have a look at %s" % (output_file,)))


def main(params, **kwargs):
    y = wrapAutoweka(params, **kwargs)
    print 'Result: ', y
    return y


if __name__ == "__main__":
    starttime = time.time()
    args, params = benchmark_util.parse_cli()
    result = main(params, **args)
    duration = time.time() - starttime
    print "Result for ParamILS: %s, %d, 1, %f, %d, %s" % \
        ("SAT", abs(duration), result, -1, str(__file__))