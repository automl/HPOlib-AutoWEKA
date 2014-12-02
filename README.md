HPOlib-AutoWEKA
===============
````
  wget http://www.cs.ubc.ca/labs/beta/Projects/autoweka/autoweka-0.5.tar.gz
  tar -xf autoweka-0.5.tar.gz
  tar -xf Data.tar.gz
````
Modify config.cfg, you might want to change:
  
  --trainarff ../Data/abalone/train.arff
  --testarff ../Data/abalone/train.arff
  --pathToAw ../autoweka-0.5/autoweka.jar

  ``function = python ../wrappingAutoweka.py --trainarff ../Data/abalone/train.arff --testarff ../Data/abalone/train.arff --trainingtime 9000 --javamemory 1000 --pathToAw ../autoweka-0.5/autoweka.jar``

then run:
````
  HPOlib-run -o path/to/smac 
````
