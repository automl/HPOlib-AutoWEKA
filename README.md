HPOlib-AutoWEKA
===============
To run this benchmark you additionaly need AutoWEKA and the datasets, you can both them from http://www.cs.ubc.ca/labs/beta/Projects/autoweka/
````
  wget http://www.cs.ubc.ca/labs/beta/Projects/autoweka/autoweka-0.5.tar.gz
  wget http://www.cs.ubc.ca/labs/beta/Projects/autoweka/datasets/abalone.zip
  tar -xf autoweka-0.5.tar.gz
  unzip abalone.zip
````
Modify config.cfg, you might want to change:
  
  --trainarff ../abalone/train.arff
  --testarff ../abalone/train.arff
  --pathToAw ../autoweka-0.5/autoweka.jar

  ``function = python ../wrappingAutoweka.py --trainarff ../abalone/train.arff --testarff ../abalone/train.arff --trainingtime 9000 --javamemory 1000 --pathToAw ../autoweka-0.5/autoweka.jar``

then run:
````
  HPOlib-run -o path/to/smac 
````
